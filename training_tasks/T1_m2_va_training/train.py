"""Train M2 affective projection head on EmoArt-130k V-A labels.

Pipeline:
    image (PIL) ─► CLIP ViT-L/14 (frozen) ─► z ∈ R^768
    z ─► MLP(768 → 256 → 2) ─► (v, a) ∈ [-1, 1]^2

Loss = MSE(pred, label) + λ · InfoNCE_contrastive(z | quadrant)

Output:
    checkpoints/va_head.pt              <-- weights only (~3 MB)
    checkpoints/train_curves.png
    checkpoints/eval_metrics.json
    checkpoints/predictions_val.csv
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.paths import data_root, require_file  # noqa: E402


# ---------- model ----------------------------------------------------------

class VAHead(nn.Module):
    """2-layer MLP that maps CLIP image embeddings to V-A."""

    def __init__(self, in_dim: int = 768, hidden: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, 2),
            nn.Tanh(),  # output in [-1, 1]
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)


# ---------- data -----------------------------------------------------------

class EmoArtVADataset(Dataset):
    """Reads emoart_va_labels.csv + local images and yields (image, v, a, quad)."""

    def __init__(self, csv_path: Path, image_root: Path, processor):
        df = pd.read_csv(csv_path)
        # only rows that have a local image on disk
        df = df[df["rows_with_local_image_flag"].astype(bool) if
                "rows_with_local_image_flag" in df.columns
                else df["local_image_path"].notna()]
        df["local_image_path"] = df["local_image_path"].astype(str)
        self.df = df.reset_index(drop=True)
        self.image_root = image_root
        self.processor = processor

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        path = self.image_root / row["local_image_path"]
        img = Image.open(path).convert("RGB")
        pixel = self.processor(images=img, return_tensors="pt").pixel_values[0]
        v = float(row["valence"])
        a = float(row["arousal"])
        # quadrant id ∈ {0,1,2,3} for InfoNCE positives
        quad = int(2 * (v >= 0) + (a >= 0))
        return pixel, torch.tensor([v, a], dtype=torch.float32), quad


# ---------- losses --------------------------------------------------------

def info_nce_by_quadrant(z: torch.Tensor, quad: torch.Tensor, tau: float = 0.1) -> torch.Tensor:
    """Same-quadrant images are positives; different quadrant negatives."""
    z = F.normalize(z, dim=-1)
    sim = (z @ z.t()) / tau                            # [B, B]
    sim.fill_diagonal_(-1e4)
    pos_mask = (quad.unsqueeze(0) == quad.unsqueeze(1)).float()
    pos_mask.fill_diagonal_(0)
    if pos_mask.sum() == 0:
        return torch.tensor(0.0, device=z.device)
    log_prob = sim - torch.logsumexp(sim, dim=-1, keepdim=True)
    return -(pos_mask * log_prob).sum() / pos_mask.sum()


# ---------- evaluation ----------------------------------------------------

def pearson(pred: np.ndarray, gt: np.ndarray) -> float:
    pred = pred - pred.mean()
    gt = gt - gt.mean()
    denom = (np.linalg.norm(pred) * np.linalg.norm(gt)) + 1e-8
    return float((pred * gt).sum() / denom)


# ---------- main ----------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None,
                    help="defaults to $ECHOSCROLL_DATA")
    ap.add_argument("--csv", default="annotations/emoart_va_labels.csv")
    ap.add_argument("--image-root", default="images/emoart")
    ap.add_argument("--clip-model", default="openai/clip-vit-large-patch14")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--lambda-contrast", type=float, default=0.1)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--out", default="checkpoints/va_head.pt")
    args = ap.parse_args()

    root = Path(args.data_root) if args.data_root else data_root()
    csv_path = require_file(root / args.csv,
                            "run echoscroll/scripts/build_va_labels.py first")

    out_dir = Path(args.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("[warn] CUDA not available — will be slow but should run")

    # ---- load frozen CLIP ----
    from transformers import CLIPProcessor, CLIPVisionModel
    print(f"[1/4] loading {args.clip_model}")
    processor = CLIPProcessor.from_pretrained(args.clip_model)
    clip = CLIPVisionModel.from_pretrained(args.clip_model).to(device).eval()
    for p in clip.parameters():
        p.requires_grad_(False)

    # ---- data split ----
    print(f"[2/4] building dataset from {csv_path}")
    ds_full = EmoArtVADataset(csv_path, root / args.image_root, processor)
    n_val = int(len(ds_full) * args.val_frac)
    n_train = len(ds_full) - n_val
    gen = torch.Generator().manual_seed(42)
    ds_train, ds_val = torch.utils.data.random_split(ds_full, [n_train, n_val], generator=gen)
    dl_train = DataLoader(ds_train, batch_size=args.batch_size, shuffle=True,
                          num_workers=4, pin_memory=True, drop_last=True)
    dl_val = DataLoader(ds_val, batch_size=args.batch_size, shuffle=False, num_workers=4)
    print(f"      train {n_train} | val {n_val}")

    # ---- model + opt ----
    head = VAHead(in_dim=clip.config.hidden_size).to(device)
    opt = torch.optim.AdamW(head.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    history = {"train_mse": [], "val_mse": [], "val_r_v": [], "val_r_a": []}

    # ---- train loop ----
    print(f"[3/4] train for {args.epochs} epochs on {device}")
    for ep in range(args.epochs):
        head.train()
        ep_loss = 0.0
        for pixel, label, quad in tqdm(dl_train, desc=f"ep{ep+1}"):
            pixel, label, quad = pixel.to(device), label.to(device), quad.to(device)
            with torch.no_grad():
                z = clip(pixel_values=pixel).pooler_output
            pred = head(z)
            loss = F.mse_loss(pred, label)
            if args.lambda_contrast > 0:
                loss = loss + args.lambda_contrast * info_nce_by_quadrant(pred, quad)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += loss.item() * label.size(0)
        sched.step()
        ep_loss /= n_train

        # ---- val ----
        head.eval()
        preds_v, preds_a, gts_v, gts_a = [], [], [], []
        val_mse = 0.0
        with torch.no_grad():
            for pixel, label, _ in dl_val:
                pixel, label = pixel.to(device), label.to(device)
                z = clip(pixel_values=pixel).pooler_output
                p = head(z)
                val_mse += F.mse_loss(p, label, reduction="sum").item()
                preds_v.append(p[:, 0].cpu().numpy()); gts_v.append(label[:, 0].cpu().numpy())
                preds_a.append(p[:, 1].cpu().numpy()); gts_a.append(label[:, 1].cpu().numpy())
        val_mse /= (2 * n_val)
        r_v = pearson(np.concatenate(preds_v), np.concatenate(gts_v))
        r_a = pearson(np.concatenate(preds_a), np.concatenate(gts_a))

        history["train_mse"].append(ep_loss)
        history["val_mse"].append(val_mse)
        history["val_r_v"].append(r_v)
        history["val_r_a"].append(r_a)
        print(f"  ep{ep+1}: train_mse={ep_loss:.4f} val_mse={val_mse:.4f} "
              f"r_v={r_v:.3f} r_a={r_a:.3f}")

    # ---- save ----
    print(f"[4/4] saving to {args.out}")
    torch.save({"state_dict": head.state_dict(), "in_dim": clip.config.hidden_size,
                "history": history}, args.out)
    with open(out_dir / "eval_metrics.json", "w") as f:
        json.dump({"val_mse": history["val_mse"][-1],
                   "pearson_v": history["val_r_v"][-1],
                   "pearson_a": history["val_r_a"][-1]}, f, indent=2)

    # ---- plot ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(history["train_mse"], label="train"); ax[0].plot(history["val_mse"], label="val")
        ax[0].set_xlabel("epoch"); ax[0].set_ylabel("MSE"); ax[0].legend(); ax[0].set_title("loss")
        ax[1].plot(history["val_r_v"], label="r_valence"); ax[1].plot(history["val_r_a"], label="r_arousal")
        ax[1].set_xlabel("epoch"); ax[1].set_ylabel("Pearson r"); ax[1].legend(); ax[1].set_title("val r")
        plt.tight_layout(); plt.savefig(out_dir / "train_curves.png", dpi=120)
    except Exception as e:
        print(f"[warn] plot skipped: {e}")

    print("done.")


if __name__ == "__main__":
    main()
