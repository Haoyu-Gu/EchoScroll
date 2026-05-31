"""Run LP-MusicCaps captioner over a directory of Chinese-instrument audio.

This script assumes the LP-MusicCaps repo has been cloned next to this file
or is importable. If the API is unavailable, falls back to a no-op so the
pipeline still produces an output file with empty `caption_lpmc` slots.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.paths import data_root  # noqa: E402


def load_captioner():
    """Try to import LP-MusicCaps; return a callable(wav, sr) -> str."""
    try:
        from lpmc.music_captioning.captioner import Captioner  # type: ignore
        cap = Captioner.from_pretrained("seungheondoh/lp-music-caps")
        return lambda wav, sr: cap.infer(wav, sr)
    except Exception as e:
        print(f"[warn] LP-MusicCaps not importable ({e}); falling back to no-op")
        return lambda wav, sr: ""


def infer_instrument_from_path(p: Path) -> str:
    parts = [s.lower() for s in p.parts]
    if any("guzheng" in s for s in parts): return "guzheng"
    if any("erhu" in s for s in parts):    return "erhu"
    if any("guqin" in s for s in parts):   return "guqin"
    if any("pipa" in s for s in parts):    return "pipa"
    if any("dizi" in s for s in parts):    return "dizi"
    if any("xiao" in s for s in parts):    return "xiao"
    if any("huqin" in s for s in parts):   return "huqin"
    if any("13dim" in s for s in parts):   return "ensemble"
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-root", default=None)
    ap.add_argument("--datasets", default="ccmusic_guzheng99,ccmusic_erhu,13dim")
    ap.add_argument("--out", default="caps_extended.jsonl")
    ap.add_argument("--max-per-dataset", type=int, default=0,
                    help="0 = no limit")
    ap.add_argument("--target-sr", type=int, default=16000,
                    help="LP-MusicCaps default")
    ap.add_argument("--chunk-s", type=float, default=10.0)
    args = ap.parse_args()

    root = Path(args.audio_root) if args.audio_root else data_root() / "audio"
    cap_fn = load_captioner()

    rows = []
    for ds in args.datasets.split(","):
        ds = ds.strip()
        ds_dir = root / ds
        if not ds_dir.exists():
            print(f"[skip] {ds_dir}")
            continue
        files = sorted(ds_dir.rglob("*.wav")) + sorted(ds_dir.rglob("*.mp3"))
        if args.max_per_dataset > 0:
            files = files[: args.max_per_dataset]
        print(f"[{ds}] {len(files)} files")
        for f in tqdm(files, desc=ds):
            try:
                wav, sr = librosa.load(f, sr=args.target_sr, mono=True)
                # take first chunk_s seconds for caption
                wav = wav[: int(args.chunk_s * args.target_sr)]
                caption = cap_fn(wav, args.target_sr)
            except Exception as e:
                caption = ""
            rows.append({
                "audio": str(f.relative_to(root)),
                "duration_s": float(len(wav) / args.target_sr) if "wav" in dir() else None,
                "caption_lpmc": caption,
                "instrument": infer_instrument_from_path(f),
            })

    with open(args.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows → {args.out}")


if __name__ == "__main__":
    main()
