"""Bake all 48 demo audios offline (8 paintings × 6 variants).

Variants:
    default   : (v, a) at the painting's preset
    va_low    : a -= 0.4
    va_high   : a += 0.4
    va_pos    : v += 0.4
    slow      : phase-vocoder x0.7 of default
    fast      : phase-vocoder x1.3 of default
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
import torch


VARIANTS = ["default", "va_low", "va_high", "va_pos", "slow", "fast"]
VARIANT_DV = {"default": (0, 0), "va_low": (0, -0.4),
              "va_high": (0, 0.4), "va_pos": (0.4, 0)}


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def va_word(v: float, a: float) -> str:
    # quadrant + radial intensity word
    if v >= 0 and a >= 0:   return "excited" if a > 0.3 else "tender"
    if v >= 0 and a < 0:    return "calm"     if a < -0.3 else "tender"
    if v < 0 and a >= 0:    return "tense"    if a > 0.3 else "tense"
    return "melancholic" if a < -0.3 else "sad"


def build_prompt(item: dict, dv: float, da: float) -> str:
    v = clamp(item["va"][0] + dv); a = clamp(item["va"][1] + da)
    word = va_word(v, a)
    return (f"{item['prompt_text']}. valence={v:.2f} arousal={a:.2f}, "
            f"mood: {word}. {item['va_descriptors']}. "
            f"Cultural context: {item['rag_context']}")


def time_stretch(wav: np.ndarray, sr: int, factor: float) -> np.ndarray:
    """Pitch-preserving stretch via librosa phase-vocoder."""
    import librosa
    return librosa.effects.time_stretch(wav.astype(np.float32), rate=factor)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paintings-json", default="paintings.json")
    ap.add_argument("--model", default="facebook/musicgen-small")
    ap.add_argument("--adapter", default="", help="path to T3 LoRA adapter (optional)")
    ap.add_argument("--use-lora", choices=["true", "false"], default="true")
    ap.add_argument("--duration", type=int, default=16)
    ap.add_argument("--out", default="audio")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    items = json.loads(Path(args.paintings_json).read_text())

    print(f"[1/3] loading MusicGen {args.model}")
    from audiocraft.models import MusicGen
    model = MusicGen.get_pretrained(args.model)

    if args.use_lora == "true" and args.adapter:
        print(f"      attaching LoRA adapter from {args.adapter}")
        from peft import PeftModel
        text_encoder = model.lm.condition_provider.conditioners["description"].t5  # type: ignore[attr-defined]
        text_encoder = PeftModel.from_pretrained(text_encoder, args.adapter)
        model.lm.condition_provider.conditioners["description"].t5 = text_encoder  # type: ignore[attr-defined]

    model.set_generation_params(duration=args.duration)
    sr = model.sample_rate

    manifest = []
    print(f"[2/3] generating {len(items)} paintings × {len(VARIANTS)} variants")
    for it in items:
        # generate the 4 "fresh" variants (default + 3 V-A shifts) in one batch
        prompts = []
        names = []
        for vname in ["default", "va_low", "va_high", "va_pos"]:
            dv, da = VARIANT_DV[vname]
            prompts.append(build_prompt(it, dv, da))
            names.append(vname)
        with torch.no_grad():
            wavs = model.generate(prompts, progress=False)   # [4, 1, T]
        clips = {}
        for nm, w in zip(names, wavs):
            fname = f"{it['id']}_{nm}.wav"
            arr = w[0].cpu().numpy()
            sf.write(out / fname, arr, sr, subtype="PCM_16")
            clips[nm] = arr
            manifest.append({"painting_id": it["id"], "variant": nm,
                             "file": fname, "duration_s": args.duration,
                             "sr": sr, "prompt": prompts[names.index(nm)]})

        # derived edited variants from default via M5-style phase-vocoder
        for nm, factor in (("slow", 0.7), ("fast", 1.3)):
            stretched = time_stretch(clips["default"], sr, factor)
            fname = f"{it['id']}_{nm}.wav"
            sf.write(out / fname, stretched, sr, subtype="PCM_16")
            manifest.append({"painting_id": it["id"], "variant": nm,
                             "file": fname, "duration_s": args.duration / factor,
                             "sr": sr, "edit": f"time_stretch({factor})",
                             "derived_from": f"{it['id']}_default.wav"})
        print(f"  ✓ {it['id']}")

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[3/3] wrote {len(manifest)} clips → {out}")


if __name__ == "__main__":
    main()
