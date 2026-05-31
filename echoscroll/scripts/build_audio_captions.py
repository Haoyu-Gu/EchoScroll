"""§3.2.2 — Build structured natural-language captions for Chinese instrument
audio (Guzheng_Tech99 / erhu_playing_tech / 13-Dim Music Emotions).

These caption templates expose mood / instrumentation / technique to MusicGen
during fine-tune. Output: data/captions/instrument_captions.jsonl
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path("/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/开题/EchoScroll_data_plan/data")
OUT = DATA / "captions" / "instrument_captions.jsonl"

GUZHENG_TECH_TEMPLATES = {
    "Vibrato":             "Solo guzheng with continuous left-hand vibrato, gentle expressive bends.",
    "Plucks":              "Guzheng with crisp right-hand plucks, clean attacks and short decay.",
    "Upward_Portamento":   "Guzheng line rising in pitch with smooth portamento.",
    "Downward_Portamento": "Guzheng line descending in pitch with smooth portamento.",
    "Glissando":           "Guzheng with sweeping glissando across the strings.",
    "Tremolo":             "Guzheng with continuous tremolo, sustained shimmering texture.",
    "Point_Note":          "Guzheng playing isolated short notes with clear separation.",
}

ERHU_TECH_TEMPLATES = {
    "vibrato":  "Solo erhu with slow vibrato, plaintive sustained tone.",
    "tremolo":  "Solo erhu with bow tremolo, agitated texture.",
    "trill":    "Solo erhu with rapid trill, ornamented pitch oscillation.",
    "staccato": "Solo erhu with short detached bow strokes.",
    "legato":   "Solo erhu with smooth legato bowing, lyrical line.",
    "slide":    "Solo erhu with expressive pitch slides between notes.",
    "default":  "Solo erhu, traditional Chinese folk style.",
}


def caption_from_13dim_row(row: dict) -> str:
    """Pick top-2 dominant emotion ratings and embed in caption."""
    nums = {k: v for k, v in row.items() if isinstance(v, (int, float)) and k != "audio"}
    if not nums:
        return "Instrumental music excerpt."
    ranked = sorted(nums.items(), key=lambda kv: -kv[1])
    top = [k for k, _ in ranked[:2]]
    mood = " and ".join(t.replace("/", " or ") for t in top)
    return f"Instrumental piece evoking a {mood} mood."


def build_guzheng() -> list[dict]:
    out = []
    try:
        import datasets as ds
        path = DATA / "audio/ccmusic_guzheng99/default"
        if not path.exists():
            print("  [skip] Guzheng_Tech99 default split not present")
            return out
        d = ds.load_from_disk(str(path))
        for split_name, split in d.items():
            # Skip audio decoding — we only need the label column
            keep_cols = [c for c in split.column_names if c != "audio"]
            split = split.remove_columns([c for c in split.column_names if c not in keep_cols])
            for i, ex in enumerate(split):
                # label is per-clip; pull techniques from frame-level label dict
                label = ex.get("label") or {}
                ipt = label.get("IPT") if isinstance(label, dict) else None
                techniques = set()
                if isinstance(ipt, list):
                    for x in ipt:
                        if isinstance(x, str):
                            techniques.add(x)
                desc_parts = []
                if techniques:
                    desc_parts.append(", ".join(sorted(techniques)) + " techniques")
                tech_phrase = "; ".join(
                    GUZHENG_TECH_TEMPLATES[t] for t in sorted(techniques)
                    if t in GUZHENG_TECH_TEMPLATES
                )
                caption = tech_phrase or "Solo guzheng, traditional Chinese plucked zither."
                out.append({
                    "source":      f"guzheng_tech99:{split_name}:{i}",
                    "instrument":  "guzheng",
                    "techniques":  sorted(techniques),
                    "caption":     caption,
                    "split":       split_name,
                })
    except Exception as e:
        print(f"  [warn] guzheng caption build failed: {e}")
    return out


def build_erhu() -> list[dict]:
    out = []
    try:
        import datasets as ds
        path = DATA / "audio/ccmusic_erhu/default"
        if not path.exists():
            print("  [skip] erhu default split not present")
            return out
        d = ds.load_from_disk(str(path))
        for split_name, split in d.items():
            class_names = split.features["label"].names if "label" in split.features else []
            keep_cols = [c for c in split.column_names if c != "audio"]
            split = split.remove_columns([c for c in split.column_names if c not in keep_cols])
            for i, ex in enumerate(split):
                lbl = ex.get("label")
                tech = class_names[lbl] if isinstance(lbl, int) and 0 <= lbl < len(class_names) else "default"
                cap = ERHU_TECH_TEMPLATES.get(tech.lower(), ERHU_TECH_TEMPLATES["default"])
                out.append({
                    "source":     f"erhu:{split_name}:{i}",
                    "instrument": "erhu",
                    "technique":  tech,
                    "caption":    cap,
                    "split":      split_name,
                })
    except Exception as e:
        print(f"  [warn] erhu caption build failed: {e}")
    return out


def build_13dim() -> list[dict]:
    out = []
    try:
        import pandas as pd
        pqs = list((DATA / "audio/13dim").rglob("*.parquet"))
        if not pqs:
            print("  [skip] 13-dim parquet not found")
            return out
        df = pd.read_parquet(pqs[0])
        # drop the 'audio' column if present (bytes)
        rating_cols = [c for c in df.columns if c != "audio"]
        for i, row in df[rating_cols].iterrows():
            cap = caption_from_13dim_row(row.to_dict())
            out.append({
                "source":      f"13dim:{i}",
                "instrument":  "mixed",
                "caption":     cap,
                "top_emotion": row.idxmax() if len(rating_cols) else None,
            })
    except Exception as e:
        print(f"  [warn] 13-dim caption build failed: {e}")
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    print("  building guzheng captions…")
    rows.extend(build_guzheng())
    print("  building erhu captions…")
    rows.extend(build_erhu())
    print("  building 13-dim captions…")
    rows.extend(build_13dim())

    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n  wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(rows)} rows)")

    from collections import Counter
    inst = Counter(r.get("instrument") for r in rows)
    print("\n  by instrument:")
    for k, v in inst.most_common():
        print(f"    {k:>10}  {v}")


if __name__ == "__main__":
    main()
