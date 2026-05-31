"""LoRA fine-tune the MusicGen text encoder on Chinese instrument captions.

Strategy (PEFT-style):
    - Freeze MusicGen LM + EnCodec entirely
    - Attach LoRA adapters (r=16) to the T5 text-encoder's q/v projections
    - Train cross-entropy on EnCodec discrete codes, conditioned on caption

This script is intentionally a minimal-correct reference. For a production-grade
run consider Audiocraft's `musicgen-dreamboothing` repo (mirrors this setup).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


class MusicCapDataset(Dataset):
    def __init__(self, jsonl_path: Path, sr: int, max_seconds: float):
        with open(jsonl_path) as f:
            self.rows = [json.loads(l) for l in f if l.strip()]
        self.sr = sr
        self.max_samples = int(max_seconds * sr)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int):
        import torchaudio
        r = self.rows[idx]
        wav, sr0 = torchaudio.load(r["audio"])
        if sr0 != self.sr:
            wav = torchaudio.functional.resample(wav, sr0, self.sr)
        wav = wav.mean(0, keepdim=True)  # mono
        wav = wav[:, : self.max_samples]
        # pad to fixed length so we can batch
        if wav.size(1) < self.max_samples:
            wav = F.pad(wav, (0, self.max_samples - wav.size(1)))
        return wav, r["caption"]


def collate(batch):
    wavs = torch.stack([b[0] for b in batch])  # [B, 1, T]
    caps = [b[1] for b in batch]
    return wavs, caps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="data/train_pairs.jsonl")
    ap.add_argument("--model", default="facebook/musicgen-small")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--lora-rank", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lora-dropout", type=float, default=0.1)
    ap.add_argument("--max-seconds", type=float, default=10.0,
                    help="audio length used per training sample")
    ap.add_argument("--out", default="checkpoints/lora_chinese_instr/")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    assert device == "cuda", "training without GPU is not supported here"

    print(f"[1/4] loading MusicGen {args.model}")
    from audiocraft.models import MusicGen
    musicgen = MusicGen.get_pretrained(args.model)
    lm = musicgen.lm                  # the transformer LM
    compression = musicgen.compression_model  # EnCodec

    # freeze everything by default
    for p in musicgen.lm.parameters(): p.requires_grad_(False)
    for p in musicgen.compression_model.parameters(): p.requires_grad_(False)

    # attach LoRA to the text encoder
    print(f"[2/4] attaching LoRA r={args.lora_rank} to text encoder")
    from peft import LoraConfig, get_peft_model
    # MusicGen wraps a T5 in lm.condition_provider.conditioners.description.t5_tokenizer/.t5
    # The exact attribute path may vary by audiocraft version; adjust here if KeyError.
    text_encoder = lm.condition_provider.conditioners["description"].t5  # type: ignore[attr-defined]
    lora_cfg = LoraConfig(
        r=args.lora_rank, lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q", "v"],   # T5 attention proj
        bias="none",
        task_type="FEATURE_EXTRACTION",
    )
    text_encoder = get_peft_model(text_encoder, lora_cfg)
    lm.condition_provider.conditioners["description"].t5 = text_encoder  # type: ignore[attr-defined]
    text_encoder.print_trainable_parameters()

    # ---- data ----
    print(f"[3/4] loading pairs from {args.pairs}")
    ds = MusicCapDataset(Path(args.pairs), musicgen.sample_rate, args.max_seconds)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True,
                    num_workers=4, collate_fn=collate, pin_memory=True)
    print(f"      {len(ds)} pairs / batch {args.batch_size} / grad_accum {args.grad_accum}")

    opt = torch.optim.AdamW([p for p in text_encoder.parameters() if p.requires_grad],
                            lr=args.lr, weight_decay=1e-4)

    losses = []
    print(f"[4/4] train {args.epochs} epochs")
    step = 0
    for ep in range(args.epochs):
        ep_loss = 0.0
        pbar = tqdm(dl, desc=f"ep{ep+1}")
        opt.zero_grad()
        for it, (wavs, caps) in enumerate(pbar):
            wavs = wavs.to(device)
            # encode audio to EnCodec discrete codes
            with torch.no_grad():
                codes, _ = compression.encode(wavs)              # [B, K, T_c]
            # forward LM with caption condition; predict the same codes
            attributes = [{"description": c} for c in caps]
            # NOTE: actual call shape depends on audiocraft version; the closest
            # public API is musicgen.lm.compute_predictions
            out_lm = lm.compute_predictions(codes, conditions=attributes)  # type: ignore[attr-defined]
            logits = out_lm.logits                               # [B, K, T_c, V]
            mask = out_lm.mask
            target = codes
            loss = F.cross_entropy(
                logits.permute(0, 1, 3, 2).reshape(-1, logits.size(-1)),
                target.reshape(-1),
                ignore_index=-1,
            )
            loss = loss / args.grad_accum
            loss.backward()
            ep_loss += loss.item() * args.grad_accum
            step += 1
            if step % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(
                    [p for p in text_encoder.parameters() if p.requires_grad], 1.0)
                opt.step(); opt.zero_grad()
            pbar.set_postfix(loss=f"{loss.item()*args.grad_accum:.3f}")
        ep_loss /= len(dl)
        losses.append(ep_loss)
        print(f"  ep{ep+1}: train_loss={ep_loss:.4f}")
        # save mid-train
        text_encoder.save_pretrained(out)

    # final save
    text_encoder.save_pretrained(out)
    (out / "training_log.json").write_text(json.dumps({"losses": losses}, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(7, 4)); plt.plot(losses)
        plt.xlabel("epoch"); plt.ylabel("train CE loss"); plt.title("LoRA fine-tune")
        plt.tight_layout(); plt.savefig(out / "train_loss.png", dpi=120)
    except Exception as e:
        print(f"[warn] plot skipped: {e}")

    print(f"done. adapter saved to {out}")


if __name__ == "__main__":
    main()
