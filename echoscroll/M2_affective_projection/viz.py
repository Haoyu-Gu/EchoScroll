"""M2 Affective Projection visualizations.

Produces three PNGs under figures/:
    fig_circumplex.png       -- Russell V-A circumplex with 100 model predictions
    fig_word_distribution.png -- bar chart of word-label frequencies
    fig_loss_components.png  -- MSE + contrastive loss over 50 training steps

Run:
    python viz.py
"""

from __future__ import annotations

import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch

from projection import AffectiveProjection, va_loss, va_to_word


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SEED = 42
DEVICE = "cpu"
IN_DIM = 768
HIDDEN_DIM = 256
N_SAMPLES = 100
N_STEPS = 50
BATCH_SIZE = 32

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

# The eight Russell labels emitted by va_to_word.
WORD_LABELS = (
    "excited/joyful",
    "powerful",
    "tense/anxious",
    "sad/depressed",
    "melancholic",
    "bored",
    "calm/serene",
    "tender",
)

# Aesthetic colour mapping for each label (consistent across both figures).
WORD_COLORS = {
    "excited/joyful": "#F4B400",   # warm yellow
    "powerful":       "#E8743B",   # vivid orange
    "tense/anxious":  "#D7263D",   # red
    "sad/depressed":  "#1F6FB4",   # blue
    "melancholic":    "#6A5ACD",   # slate purple
    "bored":          "#7F8C8D",   # cool grey
    "calm/serene":    "#2CA58D",   # teal-green
    "tender":         "#E59AC8",   # soft pink
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    os.makedirs(FIG_DIR, exist_ok=True)


def _set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)


def _predict_va(model: AffectiveProjection, n: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Run the model on n random z vectors. Returns (v, a, words)."""
    z = torch.randn(n, IN_DIM, device=DEVICE)
    model.eval()
    with torch.no_grad():
        v_hat, a_hat = model(z)
    v = v_hat.cpu().numpy()
    a = a_hat.cpu().numpy()
    words = [va_to_word(float(v[i]), float(a[i])) for i in range(n)]
    return v, a, words


# ---------------------------------------------------------------------------
# Figure 1: Russell V-A circumplex with predictions
# ---------------------------------------------------------------------------

def fig_circumplex(v: np.ndarray, a: np.ndarray, words: list[str]) -> str:
    fig, ax = plt.subplots(figsize=(7.5, 7.5))

    # Quadrant tints (Russell convention).
    # top-right (V>0, A>0): excited/joyful -> warm yellow
    # top-left  (V<0, A>0): tense/anxious -> red
    # bottom-left (V<0, A<0): sad/depressed -> blue
    # bottom-right(V>0, A<0): calm/serene -> green
    ax.add_patch(plt.Rectangle((0.0, 0.0), 1.0, 1.0,
                               facecolor="#FFF3B0", alpha=0.55, zorder=0))   # top-right
    ax.add_patch(plt.Rectangle((-1.0, 0.0), 1.0, 1.0,
                               facecolor="#F7B7B7", alpha=0.55, zorder=0))   # top-left
    ax.add_patch(plt.Rectangle((-1.0, -1.0), 1.0, 1.0,
                               facecolor="#B7CCE6", alpha=0.55, zorder=0))   # bottom-left
    ax.add_patch(plt.Rectangle((0.0, -1.0), 1.0, 1.0,
                               facecolor="#BFE3C9", alpha=0.55, zorder=0))   # bottom-right

    # Unit circle.
    theta = np.linspace(0.0, 2.0 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta),
            color="#444444", lw=1.5, zorder=2)

    # Center cross.
    ax.axhline(0.0, color="#444444", lw=0.8, zorder=2)
    ax.axvline(0.0, color="#444444", lw=0.8, zorder=2)

    # Scatter predictions, coloured by word label.
    plotted_labels = set()
    for vi, ai, wi in zip(v, a, words):
        color = WORD_COLORS.get(wi, "#000000")
        label = wi if wi not in plotted_labels else None
        plotted_labels.add(wi)
        ax.scatter(vi, ai, c=color, s=45, edgecolors="white",
                   linewidths=0.6, zorder=3, label=label)

    # 8 cardinal direction labels around the circle.
    # Place them at radius ~1.15.
    cardinal = [
        ("joyful",    1, 0),
        ("excited",   1, 1),
        ("tense",     0, 1),
        ("angry",    -1, 1),
        ("sad",      -1, 0),
        ("depressed",-1,-1),
        ("calm",      0,-1),
        ("serene",    1,-1),
    ]
    for name, sx, sy in cardinal:
        # Unit vector along the (sx, sy) direction.
        norm = max(np.hypot(sx, sy), 1e-9)
        x = 1.15 * sx / norm
        y = 1.15 * sy / norm
        ax.text(x, y, name,
                ha="center", va="center",
                fontsize=10, fontweight="bold",
                color="#222222", zorder=4)

    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Valence (–/+)", fontsize=11)
    ax.set_ylabel("Arousal (low/high)", fontsize=11)
    ax.set_title("Russell V–A Circumplex: 100 model predictions",
                 fontsize=12, pad=14)

    # Tidy ticks.
    ax.set_xticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    ax.set_yticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    ax.tick_params(axis="both", labelsize=9)

    # Legend (one per label).
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        # Preserve consistent order.
        order = [labels.index(w) for w in WORD_LABELS if w in labels]
        ax.legend(
            [handles[i] for i in order],
            [labels[i] for i in order],
            loc="center left", bbox_to_anchor=(1.02, 0.5),
            fontsize=9, frameon=True, title="va_to_word",
        )

    out = os.path.join(FIG_DIR, "fig_circumplex.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Figure 2: word-label frequency bar chart
# ---------------------------------------------------------------------------

def fig_word_distribution(words: list[str]) -> str:
    counts = Counter(words)
    # Order by frequency (descending), break ties by canonical label order.
    canonical_idx = {w: i for i, w in enumerate(WORD_LABELS)}
    items = sorted(
        counts.items(),
        key=lambda kv: (-kv[1], canonical_idx.get(kv[0], 99)),
    )
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    colors = [WORD_COLORS.get(k, "#888888") for k in labels]

    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    bars = ax.bar(labels, values, color=colors,
                  edgecolor="white", linewidth=1.0, zorder=3)

    # Annotate counts above bars.
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + max(values) * 0.015,
                str(val),
                ha="center", va="bottom",
                fontsize=9, color="#222222")

    ax.set_ylabel("frequency", fontsize=11)
    ax.set_xlabel("va_to_word label", fontsize=11)
    ax.set_title("Word-label distribution over 100 predictions",
                 fontsize=12, pad=10)
    ax.grid(axis="y", linestyle=":", color="#BBBBBB", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelrotation=20, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.set_ylim(0, max(values) * 1.18)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    out = os.path.join(FIG_DIR, "fig_word_distribution.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Figure 3: MSE + contrastive loss vs. step
# ---------------------------------------------------------------------------

def fig_loss_components() -> str:
    """Train the projection on a fake batch for 50 steps, log loss components."""
    model = AffectiveProjection(in_dim=IN_DIM, hidden_dim=HIDDEN_DIM).to(DEVICE)
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    # Fake batch: 32 z vectors, target VA, 4 categorical classes.
    z = torch.randn(BATCH_SIZE, IN_DIM, device=DEVICE)
    target_va = torch.empty(BATCH_SIZE, 2, device=DEVICE).uniform_(-1.0, 1.0)
    labels = torch.randint(low=0, high=4, size=(BATCH_SIZE,), device=DEVICE)

    mse_hist: list[float] = []
    con_hist: list[float] = []

    for _ in range(N_STEPS):
        v_hat, a_hat = model(z)
        pred_va = torch.stack([v_hat, a_hat], dim=1)
        out = va_loss(
            pred_va=pred_va,
            target_va=target_va,
            z=z,
            labels_categorical=labels,
            tau=0.1,
            lam=0.5,
        )
        opt.zero_grad()
        out["loss"].backward()
        opt.step()

        mse_hist.append(float(out["mse"].item()))
        con_hist.append(float(out["contrastive"].item()))

    steps = np.arange(1, N_STEPS + 1)

    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    ax.plot(steps, mse_hist, color="#1F6FB4", lw=2.0,
            linestyle="-", label="MSE")
    ax.plot(steps, con_hist, color="#D7263D", lw=2.0,
            linestyle="--", label="contrastive (InfoNCE)")

    ax.set_xlabel("step", fontsize=11)
    ax.set_ylabel("loss", fontsize=11)
    ax.set_title("L_VA components during a 50-step training run",
                 fontsize=12, pad=10)
    ax.grid(True, linestyle=":", color="#BBBBBB")
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=9)
    ax.legend(loc="upper right", fontsize=10, frameon=True)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    out = os.path.join(FIG_DIR, "fig_loss_components.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _ensure_dirs()
    _set_seed(SEED)

    # Model used for the 100 prediction visuals.
    model = AffectiveProjection(in_dim=IN_DIM, hidden_dim=HIDDEN_DIM).to(DEVICE)
    v, a, words = _predict_va(model, N_SAMPLES)

    p1 = fig_circumplex(v, a, words)
    p2 = fig_word_distribution(words)

    # Re-seed so the loss-curve plot is reproducible independently.
    _set_seed(SEED)
    p3 = fig_loss_components()

    print("Saved:")
    for path in (p1, p2, p3):
        print(f"  {path}  exists={os.path.exists(path)}")


if __name__ == "__main__":
    main()
