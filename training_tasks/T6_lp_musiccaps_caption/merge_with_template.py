"""Merge template captions (main repo) with LP-MusicCaps captions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="instrument_captions.jsonl")
    ap.add_argument("--lpmc", required=True, help="caps_extended.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--combine", choices=["template", "lpmc", "template + lpmc"],
                    default="template + lpmc")
    args = ap.parse_args()

    by_audio = {}
    for line in open(args.template):
        r = json.loads(line)
        by_audio[r["audio_path"]] = {"audio_path": r["audio_path"],
                                      "caption_template": r["caption"],
                                      "instrument": r.get("instrument")}
    for line in open(args.lpmc):
        r = json.loads(line)
        key = r["audio"]
        if key not in by_audio:
            by_audio[key] = {"audio_path": key,
                              "caption_template": "",
                              "instrument": r.get("instrument")}
        by_audio[key]["caption_lpmc"] = r.get("caption_lpmc", "")

    rows = []
    for key, v in by_audio.items():
        tpl = v.get("caption_template", "")
        lp = v.get("caption_lpmc", "")
        if args.combine == "template":     cap = tpl
        elif args.combine == "lpmc":       cap = lp
        else:                              cap = (tpl + "\n" + lp).strip()
        rows.append({"audio_path": key, "caption": cap,
                      "instrument": v.get("instrument")})

    with open(args.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"merged {len(rows)} rows ({args.combine}) → {args.out}")


if __name__ == "__main__":
    main()
