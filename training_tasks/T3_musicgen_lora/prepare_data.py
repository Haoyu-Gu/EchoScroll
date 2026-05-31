"""Build (audio_path, caption) training pairs for MusicGen LoRA.

Reads:
    $ECHOSCROLL_DATA/captions/instrument_captions.jsonl
Audio:
    $ECHOSCROLL_DATA/audio/ccmusic_guzheng99/...
    $ECHOSCROLL_DATA/audio/ccmusic_erhu/...

Re-samples every clip to 32 kHz mono, clips to ≤ max_dur seconds,
writes (audio_path, caption, duration) pairs to JSONL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import librosa
import soundfile as sf
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.paths import data_root, require_file  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--captions", default="captions/instrument_captions.jsonl")
    ap.add_argument("--audio-prep", default="data/audio_32k",
                    help="dir to write re-encoded 32 kHz mono clips")
    ap.add_argument("--out", default="data/train_pairs.jsonl")
    ap.add_argument("--sr", type=int, default=32000)
    ap.add_argument("--max-dur", type=float, default=30.0)
    ap.add_argument("--min-dur", type=float, default=4.0)
    args = ap.parse_args()

    root = Path(args.data_root) if args.data_root else data_root()
    caps_path = require_file(root / args.captions)
    audio_out = Path(args.audio_prep); audio_out.mkdir(parents=True, exist_ok=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    pairs = []
    skipped = 0
    with open(caps_path) as f:
        rows = [json.loads(line) for line in f if line.strip()]

    for r in tqdm(rows, desc="prep"):
        src = root / r["audio_path"] if not Path(r["audio_path"]).is_absolute() \
              else Path(r["audio_path"])
        if not src.exists():
            skipped += 1
            continue
        try:
            y, sr0 = librosa.load(src, sr=args.sr, mono=True)
        except Exception:
            skipped += 1
            continue
        dur = len(y) / args.sr
        if dur < args.min_dur:
            skipped += 1
            continue
        # clip to max_dur
        if dur > args.max_dur:
            y = y[: int(args.max_dur * args.sr)]
            dur = args.max_dur
        out_path = audio_out / f"{src.stem}.wav"
        sf.write(out_path, y, args.sr, subtype="PCM_16")
        pairs.append({"audio": str(out_path), "caption": r["caption"],
                       "duration": float(dur), "instrument": r.get("instrument")})

    with open(args.out, "w") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"wrote {len(pairs)} pairs (skipped {skipped}) → {args.out}")


if __name__ == "__main__":
    main()
