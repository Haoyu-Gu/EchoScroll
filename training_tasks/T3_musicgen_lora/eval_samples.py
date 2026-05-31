"""Quick sanity check for a LoRA adapter: generate 4 clips with vs. without it."""

from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
import torch


PROBES = [
    ("guzheng_calm",      "Solo guzheng, slow, calm, traditional Chinese style"),
    ("guzheng_excited",   "Solo guzheng, fast tempo, virtuosic glissandi"),
    ("erhu_melancholic",  "Solo erhu, mournful, slow vibrato, traditional Chinese"),
    ("ensemble_pentatonic","Pentatonic Chinese ensemble, guqin and xiao, contemplative"),
]


def gen(model, out_dir: Path, suffix: str, duration: int):
    model.set_generation_params(duration=duration)
    prompts = [p[1] for p in PROBES]
    with torch.no_grad():
        wavs = model.generate(prompts, progress=False)
    for (name, _), w in zip(PROBES, wavs):
        sf.write(out_dir / f"{name}_{suffix}.wav",
                 w[0].cpu().numpy(), model.sample_rate, subtype="PCM_16")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True, help="path to LoRA adapter dir")
    ap.add_argument("--model", default="facebook/musicgen-small")
    ap.add_argument("--out", default="checkpoints/eval_samples")
    ap.add_argument("--duration", type=int, default=10)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    from audiocraft.models import MusicGen
    from peft import PeftModel

    print("[1/2] vanilla MusicGen → baseline samples")
    base = MusicGen.get_pretrained(args.model)
    gen(base, out, "vanilla", args.duration)

    print("[2/2] +LoRA adapter → tuned samples")
    text_encoder = base.lm.condition_provider.conditioners["description"].t5  # type: ignore[attr-defined]
    text_encoder = PeftModel.from_pretrained(text_encoder, args.adapter)
    base.lm.condition_provider.conditioners["description"].t5 = text_encoder  # type: ignore[attr-defined]
    gen(base, out, "lora", args.duration)

    print(f"done. listen to {out}/*.wav")


if __name__ == "__main__":
    main()
