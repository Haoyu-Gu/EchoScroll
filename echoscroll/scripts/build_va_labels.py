"""§3.2.3 — Build a V-A training/eval CSV from EmoArt Annotation.json.

Maps EmoArt's coarse labels into the continuous V-A space:
  arousal:  Low -> -0.5, High -> +0.5
  valence:  Negative -> -0.5, Positive -> +0.5
Adds small per-emotion offsets so different dominant emotions don't collapse.

Writes:
  data/annotations/emoart_va_labels.csv
Columns:
  request_id, image_path, style, valence, arousal,
  arousal_level, valence_polarity, dominant_emotion,
  brushwork, color, composition, light, line, emotional_impact,
  short_caption, healing_effects, has_local_image
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

DATA = Path("/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/开题/EchoScroll_data_plan/data")
SRC = DATA / "images/emoart/Annotation.json"
OUT = DATA / "annotations/emoart_va_labels.csv"

# Per-emotion (v_offset, a_offset). Layered on top of the coarse polarity quadrant
# to produce continuous (v, a) in [-1, 1]^2. Values are small (~0.2) so the
# quadrant signal still dominates.
EMOTION_OFFSETS = {
    "Calm":           (+0.15, -0.30),
    "Joy":            (+0.40, +0.30),
    "Happiness":      (+0.40, +0.30),
    "Hope":           (+0.25, +0.10),
    "Awe":            (+0.10, +0.20),
    "Wonder":         (+0.10, +0.20),
    "Tenderness":     (+0.30, -0.20),
    "Love":           (+0.30, -0.10),
    "Sadness":        (-0.40, -0.30),
    "Melancholy":     (-0.30, -0.30),
    "Loneliness":     (-0.30, -0.30),
    "Fear":           (-0.30, +0.30),
    "Anger":          (-0.30, +0.40),
    "Tension":        (-0.10, +0.30),
    "Disgust":        (-0.30, +0.10),
    "Boredom":        (-0.10, -0.40),
}


def coarse(arousal_level: str, valence_pol: str) -> tuple[float, float]:
    a = +0.5 if (arousal_level or "").lower().startswith("high") else -0.5
    v = +0.5 if (valence_pol or "").lower().startswith("pos") else -0.5
    return v, a


def style_from_path(p: str) -> str:
    # Images\Abstract Art\xxx.jpg  →  Abstract Art
    p = p.replace("\\", "/")
    parts = p.split("/")
    if len(parts) >= 3:
        return parts[1]
    return ""


def normalize_image_rel(p: str) -> str:
    return p.replace("\\", "/")


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def short(s: str | None, n: int = 120) -> str | None:
    if not s:
        return s
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"[err] {SRC} not found — run data plan first")
    print(f"  loading {SRC} ({SRC.stat().st_size / 1e6:.1f} MB)…")
    with SRC.open(encoding="utf-8") as f:
        data = json.load(f)
    print(f"  records: {len(data)}")

    # Build a quick has-local-image lookup based on which style folders survived
    extracted = set()
    for tar in (DATA / "images/emoart").glob("*.tar.gz"):
        extracted.add(tar.stem.replace(".tar", ""))
    # Also accept already-extracted Images/ dir
    img_root = DATA / "images/emoart/Images"
    if img_root.exists():
        for style_dir in img_root.iterdir():
            if style_dir.is_dir():
                extracted.add(style_dir.name)
    print(f"  available styles (tar or extracted): {sorted(extracted)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    n_written = 0
    n_with_local = 0
    style_counts = {}
    emotion_counts = {}
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "request_id", "image_path", "style",
            "valence", "arousal",
            "arousal_level", "valence_polarity", "dominant_emotion",
            "brushwork", "color", "composition", "light", "line",
            "emotional_impact", "short_caption",
            "healing_effects", "has_local_image",
        ])
        for r in data:
            img = r.get("image_path") or ""
            style = style_from_path(img)
            third = (r.get("description") or {}).get("third_section") or {}
            second = (r.get("description") or {}).get("second_section") or {}
            first = (r.get("description") or {}).get("first_section") or {}

            v_coarse, a_coarse = coarse(third.get("emotional_arousal_level"), third.get("emotional_valence"))
            dom = third.get("dominant_emotion") or ""
            dv, da = EMOTION_OFFSETS.get(dom, (0.0, 0.0))
            v = clamp(v_coarse + dv * 0.5)
            a = clamp(a_coarse + da * 0.5)

            attrs = second.get("visual_attributes") or {}
            heal = third.get("healing_effects") or []
            if isinstance(heal, list):
                heal_str = " | ".join(heal)
            else:
                heal_str = str(heal)

            w.writerow([
                r.get("request_id"),
                normalize_image_rel(img),
                style,
                f"{v:.3f}", f"{a:.3f}",
                third.get("emotional_arousal_level"),
                third.get("emotional_valence"),
                dom,
                short(attrs.get("brushstroke")),
                short(attrs.get("color")),
                short(attrs.get("composition")),
                short(attrs.get("light_and_shadow")),
                short(attrs.get("line_quality")),
                short(second.get("emotional_impact")),
                short(first.get("description")),
                heal_str,
                "1" if style in extracted else "0",
            ])
            n_written += 1
            if style in extracted:
                n_with_local += 1
            style_counts[style] = style_counts.get(style, 0) + 1
            emotion_counts[dom] = emotion_counts.get(dom, 0) + 1

    print(f"  wrote {OUT} ({OUT.stat().st_size:,} bytes, {n_written} rows)")
    print(f"  rows with local image: {n_with_local}")
    print(f"\n  top emotions:")
    for k, v in sorted(emotion_counts.items(), key=lambda kv: -kv[1])[:10]:
        print(f"    {k:>15}  {v}")
    print(f"\n  top styles (sample):")
    for k, v in sorted(style_counts.items(), key=lambda kv: -kv[1])[:10]:
        print(f"    {k:>30}  {v}")


if __name__ == "__main__":
    main()
