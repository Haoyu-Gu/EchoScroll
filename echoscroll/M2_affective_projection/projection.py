"""M2 Affective Projection.

Maps a fused multimodal feature z (B, d) into a 2D valence-arousal vector
on the Russell circumplex. Used by EchoScroll between the multimodal
encoder (M1) and the music generator (M4).

Public API:
    AffectiveProjection(nn.Module)   -- g_phi: R^d -> R^2 (tanh)
    va_loss(...)                     -- MSE + lambda * InfoNCE
    va_to_word(v, a)                 -- Russell-circumplex quadrant label
"""

from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class AffectiveProjection(nn.Module):
    """Two-layer MLP that projects fused multimodal z into V-A space.

    Args:
        in_dim: dimensionality of the fused feature z (default 768).
        hidden_dim: width of the hidden layer (default 256).

    Forward:
        z: torch.Tensor of shape (B, in_dim).
        returns: (v_hat, a_hat) each of shape (B,), in [-1, 1].
    """

    def __init__(self, in_dim: int = 768, hidden_dim: int = 256):
        super().__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 2),
        )

    def forward(self, z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if z.dim() != 2:
            raise ValueError(f"expected z of shape (B, d), got {tuple(z.shape)}")
        if z.shape[1] != self.in_dim:
            raise ValueError(
                f"expected in_dim={self.in_dim}, got {z.shape[1]}"
            )
        va = torch.tanh(self.net(z))  # (B, 2) in [-1, 1]
        v_hat, a_hat = va[:, 0], va[:, 1]
        return v_hat, a_hat


# ---------------------------------------------------------------------------
# Loss
# ---------------------------------------------------------------------------

def _info_nce_by_class(
    z: torch.Tensor,
    labels: torch.Tensor,
    tau: float = 0.1,
) -> torch.Tensor:
    """Supervised NT-Xent on z, grouped by categorical labels.

    Positives = same class (excluding self); negatives = all others.
    Returns a scalar tensor. If no class has >= 2 members, returns 0.
    """
    if z.shape[0] != labels.shape[0]:
        raise ValueError("z and labels must have same batch dimension")

    B = z.shape[0]
    if B < 2:
        return z.new_zeros(())

    z_norm = F.normalize(z, dim=1)
    sim = z_norm @ z_norm.t() / tau  # (B, B)

    # mask out self-similarity
    eye = torch.eye(B, dtype=torch.bool, device=z.device)
    sim = sim.masked_fill(eye, float("-inf"))

    # positive mask: same class, not self
    same = labels.unsqueeze(0) == labels.unsqueeze(1)
    pos_mask = same & ~eye  # (B, B)

    # only anchors that actually have at least one positive contribute
    has_pos = pos_mask.any(dim=1)
    if not has_pos.any():
        return z.new_zeros(())

    # log-softmax over each row (denominator = all non-self entries).
    # The diagonal is -inf so it contributes 0 to the softmax denominator;
    # log_softmax will be -inf at the diagonal, which we then zero out
    # before summing (otherwise -inf * 0 = NaN).
    log_prob = F.log_softmax(sim, dim=1)  # (B, B)
    log_prob = log_prob.masked_fill(eye, 0.0)  # safe: diagonal is never a positive

    # mean of log-prob over positives, per anchor
    pos_counts = pos_mask.sum(dim=1).clamp(min=1).float()
    pos_log_prob = (log_prob * pos_mask.float()).sum(dim=1) / pos_counts

    loss = -pos_log_prob[has_pos].mean()
    return loss


def va_loss(
    pred_va: torch.Tensor,
    target_va: torch.Tensor,
    z: torch.Tensor,
    labels_categorical: Optional[torch.Tensor] = None,
    tau: float = 0.1,
    lam: float = 0.5,
) -> dict:
    """Compute L_VA = MSE(pred, target) + lam * InfoNCE_contrastive(z | labels).

    Args:
        pred_va: (B, 2) predicted (v, a) from AffectiveProjection.
        target_va: (B, 2) ground-truth (v, a) in [-1, 1].
        z: (B, d) fused features used for the contrastive term.
        labels_categorical: (B,) long tensor of coarse emotion classes.
            If None, the contrastive term is 0.
        tau: NT-Xent temperature.
        lam: weight of the contrastive term.

    Returns:
        dict with keys: 'loss', 'mse', 'contrastive'.
    """
    if pred_va.shape != target_va.shape:
        raise ValueError(
            f"pred {tuple(pred_va.shape)} vs target {tuple(target_va.shape)}"
        )
    if pred_va.shape[-1] != 2:
        raise ValueError("pred_va/target_va must have last dim = 2")

    mse = F.mse_loss(pred_va, target_va)

    if labels_categorical is None:
        contrastive = z.new_zeros(())
    else:
        contrastive = _info_nce_by_class(z, labels_categorical, tau=tau)

    total = mse + lam * contrastive
    return {"loss": total, "mse": mse, "contrastive": contrastive}


# ---------------------------------------------------------------------------
# Russell circumplex utility
# ---------------------------------------------------------------------------

# Eight equal sectors on the V-A circumplex, ordered by angle theta = atan2(a, v).
# Sector 0 is centred at theta = 0 (high valence, neutral arousal).
# Sector k covers [(k-0.5)*pi/4, (k+0.5)*pi/4).
_SECTOR_WORDS = (
    "excited/joyful",   # 0    -- high V, mid A
    "powerful",         # pi/4 -- high V, high A
    "tense/anxious",    # pi/2 -- low V,  high A   (note: arousal axis is +y)
    "tense/anxious",    # 3pi/4 -- low V, high A boundary
    "sad/depressed",    # pi    -- low V,  mid A
    "melancholic",      # -3pi/4 -- low V, low A
    "bored",            # -pi/2  -- mid V,low A  (but here V near 0)
    "calm/serene",      # -pi/4  -- high V, low A
)


def va_to_word(v: float, a: float) -> str:
    """Map a V-A point to a Russell-style affect word.

    Uses the 8-sector partition of the circumplex (Russell, 1980):

        arousal +
                |
       tense  --|-- powerful
                |
       sad   <--+-->  excited/joyful
                |
      melancholic-|-- calm/serene
                |    arousal -
                v

    The eight returned words are::

        "excited/joyful", "powerful", "tense/anxious", "sad/depressed",
        "melancholic", "bored", "calm/serene", "tender"

    "tender" is used for the near-origin / mildly positive low-arousal region,
    matching the soft / gentle quadrant used in ArtEmis-style annotations.
    """
    # Near-origin / soft positive-valence low-arousal band: "tender".
    # This matches the "soft/gentle" sector used in ArtEmis-style art-emotion
    # annotations and the proposal's "tender" descriptor.
    r = math.sqrt(v * v + a * a)
    if r < 0.15:
        return "tender"
    if v > 0.0 and -0.35 < a <= 0.0 and v < 0.55:
        return "tender"

    theta = math.atan2(a, v)  # in (-pi, pi]
    # 8 sectors, each of width pi/4, centred at k*pi/4 for k = -3..4
    # shift theta by pi/8 so sector index = floor((theta + pi/8) / (pi/4)) mod 8
    idx = int(math.floor((theta + math.pi / 8) / (math.pi / 4))) % 8

    table = {
        0: "excited/joyful",    # theta ~ 0      -> +V, mid A
        1: "powerful",          # theta ~ pi/4   -> +V, +A
        2: "tense/anxious",     # theta ~ pi/2   ->  V~0, +A
        3: "tense/anxious",     # theta ~ 3pi/4  -> -V, +A
        4: "sad/depressed",     # theta ~ pi     -> -V, mid A
        5: "melancholic",       # theta ~ -3pi/4 -> -V, -A
        6: "bored",             # theta ~ -pi/2  ->  V~0, -A
        7: "calm/serene",       # theta ~ -pi/4  -> +V, -A
    }
    # Distinguish the upper-left vs. upper-right "tense" sectors:
    #   if valence is clearly positive and arousal high, prefer "powerful"
    #   if valence is clearly negative and arousal high, prefer "tense/anxious"
    # The table above already covers this; we additionally map the soft
    # low-arousal positive-valence band to "tender" when |a| is very small.
    word = table[idx]
    if word == "calm/serene" and a > -0.25 and v > 0.0:
        # mild positive valence, gently low arousal -> "tender"
        return "tender"
    return word
