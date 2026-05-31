"""M2 demo: random z -> V-A predictions -> word labels -> loss components.

CPU-only. Run with:
    python demo.py
"""

from __future__ import annotations

import torch

from projection import AffectiveProjection, va_loss, va_to_word


def main() -> None:
    torch.manual_seed(0)
    device = "cpu"

    B, d = 4, 768
    z = torch.randn(B, d, device=device)

    model = AffectiveProjection(in_dim=d, hidden_dim=256).to(device).eval()

    with torch.no_grad():
        v_hat, a_hat = model(z)

    print("=== M2 Affective Projection demo ===")
    print(f"input z: shape={tuple(z.shape)}, dtype={z.dtype}, device={z.device}")
    print(f"output v_hat: {v_hat.tolist()}")
    print(f"output a_hat: {a_hat.tolist()}")
    print()
    print("Per-sample V-A and Russell-circumplex word:")
    for i in range(B):
        v = float(v_hat[i].item())
        a = float(a_hat[i].item())
        word = va_to_word(v, a)
        print(f"  [{i}] v={v:+.3f}  a={a:+.3f}  ->  {word}")

    # ---- fake supervision for the loss demo ----
    # 2 emotion classes, each with 2 samples (so InfoNCE has positives).
    target_va = torch.tensor(
        [[0.6, -0.2], [0.5, -0.3], [-0.4, 0.7], [-0.5, 0.6]],
        device=device,
    )
    labels = torch.tensor([0, 0, 1, 1], device=device)

    pred_va = torch.stack([v_hat, a_hat], dim=1)  # (B, 2)
    losses = va_loss(
        pred_va=pred_va,
        target_va=target_va,
        z=z,
        labels_categorical=labels,
        tau=0.1,
        lam=0.5,
    )
    print()
    print("Loss components (with categorical labels):")
    print(f"  mse         = {losses['mse'].item():.4f}")
    print(f"  contrastive = {losses['contrastive'].item():.4f}")
    print(f"  total       = {losses['loss'].item():.4f}")

    # also show the no-label case
    losses_nolabel = va_loss(
        pred_va=pred_va,
        target_va=target_va,
        z=z,
        labels_categorical=None,
    )
    print()
    print("Loss components (no labels, contrastive disabled):")
    print(f"  mse         = {losses_nolabel['mse'].item():.4f}")
    print(f"  contrastive = {losses_nolabel['contrastive'].item():.4f}")
    print(f"  total       = {losses_nolabel['loss'].item():.4f}")


if __name__ == "__main__":
    main()
