"""Evaluate a trained V-A head on the EmoArt validation split.

Usage:
    python eval.py --checkpoint checkpoints/va_head.pt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.paths import data_root, require_file  # noqa: E402

from train import EmoArtVADataset, VAHead, pearson  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--csv", default="annotations/emoart_va_labels.csv")
    ap.add_argument("--image-root", default="images/emoart")
    ap.add_argument("--clip-model", default="openai/clip-vit-large-patch14")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--out", default="checkpoints/predictions_val.csv")
    args = ap.parse_args()

    root = Path(args.data_root) if args.data_root else data_root()
    csv_path = require_file(root / args.csv)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    from transformers import CLIPProcessor, CLIPVisionModel
    processor = CLIPProcessor.from_pretrained(args.clip_model)
    clip = CLIPVisionModel.from_pretrained(args.clip_model).to(device).eval()

    ds_full = EmoArtVADataset(csv_path, root / args.image_root, processor)
    n_val = int(len(ds_full) * args.val_frac)
    n_train = len(ds_full) - n_val
    gen = torch.Generator().manual_seed(42)
    _, ds_val = torch.utils.data.random_split(ds_full, [n_train, n_val], generator=gen)
    dl_val = DataLoader(ds_val, batch_size=args.batch_size, shuffle=False, num_workers=4)

    ckpt = torch.load(args.checkpoint, map_location=device)
    head = VAHead(in_dim=ckpt["in_dim"]).to(device)
    head.load_state_dict(ckpt["state_dict"])
    head.eval()

    rows, total = [], 0
    preds_v, preds_a, gts_v, gts_a = [], [], [], []
    with torch.no_grad():
        for pixel, label, _ in dl_val:
            pixel, label = pixel.to(device), label.to(device)
            z = clip(pixel_values=pixel).pooler_output
            p = head(z)
            total += F.mse_loss(p, label, reduction="sum").item()
            preds_v.append(p[:, 0].cpu().numpy()); gts_v.append(label[:, 0].cpu().numpy())
            preds_a.append(p[:, 1].cpu().numpy()); gts_a.append(label[:, 1].cpu().numpy())
            for i in range(label.size(0)):
                rows.append({"pred_v": float(p[i, 0]), "gt_v": float(label[i, 0]),
                             "pred_a": float(p[i, 1]), "gt_a": float(label[i, 1])})
    mse = total / (2 * len(rows))
    r_v = pearson(np.concatenate(preds_v), np.concatenate(gts_v))
    r_a = pearson(np.concatenate(preds_a), np.concatenate(gts_a))

    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(json.dumps({"val_mse": mse, "pearson_v": r_v, "pearson_a": r_a,
                      "n_val": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
