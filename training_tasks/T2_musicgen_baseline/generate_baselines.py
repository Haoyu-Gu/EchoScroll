"""Generate 24 MusicGen baseline audios (8 paintings × 3 systems A/B/C).

System A: text-only generic prompt
System B: A + V-A descriptors
System C: B + top-3 RAG context (= full EchoScroll prompt)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf
import torch
from tqdm import tqdm


SYSTEMS = ("A", "B", "C")


def build_prompt(item: dict, system: str) -> str:
    base = item["prompt_text"]
    if system == "A":
        return base
    if system == "B":
        return (f"{base}. valence={item['va'][0]:.2f} arousal={item['va'][1]:.2f}, "
                f"mood: {item['word']}. {item['va_descriptors']}")
    # C
    return (f"{base}. valence={item['va'][0]:.2f} arousal={item['va'][1]:.2f}, "
            f"mood: {item['word']}. {item['va_descriptors']}. "
            f"Cultural context: {item['rag_context']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="facebook/musicgen-small")
    ap.add_argument("--paintings-json", default="paintings.json")
    ap.add_argument("--out", default="audio")
    ap.add_argument("--duration", type=int, default=12, help="seconds")
    ap.add_argument("--paintings", default="", help="comma-separated ids; default all")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    items = json.loads(Path(args.paintings_json).read_text())
    if args.paintings:
        wanted = set(s.strip() for s in args.paintings.split(","))
        items = [it for it in items if it["id"] in wanted]

    print(f"[1/3] loading MusicGen {args.model}")
    from audiocraft.models import MusicGen
    model = MusicGen.get_pretrained(args.model)
    model.set_generation_params(duration=args.duration)
    sr = model.sample_rate

    manifest = []
    print(f"[2/3] generating {len(items)} × 3 = {len(items)*3} clips, {args.duration}s each")
    for it in tqdm(items):
        prompts = [build_prompt(it, s) for s in SYSTEMS]
        with torch.no_grad():
            wav = model.generate(prompts, progress=False)  # [3, 1, T]
        for s, w in zip(SYSTEMS, wav):
            fname = f"{it['id']}_{s}.wav"
            sf.write(out / fname, w[0].cpu().numpy(), sr, subtype="PCM_16")
            manifest.append({"painting_id": it["id"], "system": s,
                              "file": fname, "duration_s": args.duration,
                              "sr": sr, "prompt": build_prompt(it, s)})

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[3/3] wrote {len(manifest)} clips → {out}")


if __name__ == "__main__":
    main()
