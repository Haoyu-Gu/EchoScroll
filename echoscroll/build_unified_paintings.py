"""Merge Met + Cleveland + zqman painting metadata into a single schema.

Schema:
  id, source, title, artist, dynasty, period, school, subject,
  medium, license, image_url, image_local_path, caption, description

Output:
  data/processed/paintings_unified.parquet
  data/processed/paintings_unified.csv   (for human inspection)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

DATA = Path("/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/开题/EchoScroll_data_plan/data")
OUT_DIR = DATA / "processed"
OUT_DIR.mkdir(exist_ok=True)


def normalize_dynasty(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    # Pull canonical dynasty token if a long descriptor is given.
    for key in ("Northern Song", "Southern Song", "Song", "Tang", "Yuan", "Ming", "Qing", "Han", "Sui", "Five Dynasties"):
        if key.lower() in s.lower():
            return key
    return s


def load_met() -> pd.DataFrame:
    p = DATA / "images/met_asian_art/manifest.jsonl"
    rows = []
    if p.exists():
        for line in p.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows.append({
                "id":               f"met_{r.get('id')}",
                "source":           "met",
                "title":            r.get("title"),
                "artist":           r.get("artist"),
                "dynasty":          normalize_dynasty(r.get("dynasty") or r.get("period")),
                "period":           r.get("period"),
                "school":           None,
                "subject":          r.get("classification"),
                "medium":           r.get("medium"),
                "license":          r.get("license", "CC0"),
                "image_url":        r.get("image_url"),
                "image_local_path": r.get("local_path"),
                "caption":          None,
                "description":      r.get("title"),
            })
    return pd.DataFrame(rows)


def load_cleveland() -> pd.DataFrame:
    p = DATA / "images/cleveland_chinese/manifest.jsonl"
    rows = []
    if p.exists():
        for line in p.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            culture = r.get("culture")
            if isinstance(culture, list) and culture:
                culture = culture[0]
            rows.append({
                "id":               f"cle_{r.get('id')}",
                "source":           "cleveland",
                "title":            r.get("title"),
                "artist":           r.get("artist"),
                "dynasty":          normalize_dynasty(culture or r.get("dynasty")),
                "period":           culture,
                "school":           None,
                "subject":          r.get("classification"),
                "medium":           r.get("medium"),
                "license":          r.get("license", "CC0"),
                "image_url":        r.get("image_url"),
                "image_local_path": r.get("local_path"),
                "caption":          r.get("description"),
                "description":      r.get("wall_description") or r.get("description"),
            })
    return pd.DataFrame(rows)


def load_zqman() -> pd.DataFrame:
    """zqman is HF parquet with 2192 (image, text) rows; we only keep the text + index."""
    pqs = list((DATA / "images/zqman").rglob("*.parquet"))
    if not pqs:
        return pd.DataFrame()
    df = pd.read_parquet(pqs[0])
    # Image column is bytes — drop it; just record presence
    rows = []
    for i, row in df.iterrows():
        rows.append({
            "id":               f"zqman_{i}",
            "source":           "zqman",
            "title":            None,
            "artist":           None,
            "dynasty":          None,
            "period":           None,
            "school":           None,
            "subject":          "landscape painting",
            "medium":           "ink and color",
            "license":          "research",
            "image_url":        None,
            "image_local_path": f"images/zqman/data/train-00000-of-00001.parquet#{i}",
            "caption":          row.get("text"),
            "description":      None,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parts = {
        "met":       load_met(),
        "cleveland": load_cleveland(),
        "zqman":     load_zqman(),
    }
    for k, df in parts.items():
        print(f"  {k}: {len(df)} rows")
    unified = pd.concat(parts.values(), ignore_index=True)
    # Coerce any list-valued cells to strings so parquet writer is happy.
    for col in unified.columns:
        if unified[col].apply(lambda v: isinstance(v, list)).any():
            unified[col] = unified[col].apply(
                lambda v: " | ".join(str(x) for x in v) if isinstance(v, list) else v
            )
    print(f"\n  unified: {len(unified)} rows · {unified['source'].value_counts().to_dict()}")

    out_pq = OUT_DIR / "paintings_unified.parquet"
    out_csv = OUT_DIR / "paintings_unified.csv"
    unified.to_parquet(out_pq, index=False)
    unified.to_csv(out_csv, index=False)
    print(f"\n  wrote {out_pq} ({out_pq.stat().st_size:,} bytes)")
    print(f"  wrote {out_csv} ({out_csv.stat().st_size:,} bytes)")

    # Print dynasty distribution
    print("\n  dynasty distribution:")
    for k, v in unified["dynasty"].value_counts(dropna=False).head(15).items():
        print(f"    {k!r:>30}  {v}")


if __name__ == "__main__":
    main()
