"""Walk every dataset under data/ and emit a single INVENTORY.md.

For each dataset we record: kind, file count, total size, schema/sample row,
key stats (rows, dynasty distribution, etc.).
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

DATA_ROOT = Path(
    "/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/开题/EchoScroll_data_plan/data"
)
OUT = DATA_ROOT / "INVENTORY.md"


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def dir_size(p: Path) -> int:
    total = 0
    for root, _, files in os.walk(p):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def count_files(p: Path, pattern: str = "*") -> int:
    return sum(1 for _ in p.rglob(pattern) if _.is_file())


# --- per-dataset inspectors ---

def inspect_image_dir_with_manifest(p: Path, source: str) -> dict:
    """Met / Cleveland style: many .jpg + manifest.jsonl."""
    jpgs = list(p.glob("*.jpg"))
    manifest = p / "manifest.jsonl"
    rows = []
    if manifest.exists():
        with manifest.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    dyn = Counter()
    for r in rows:
        d = r.get("dynasty") or "?"
        # short-form normalize
        for k in ["Song", "Tang", "Ming", "Qing", "Yuan", "Han", "Sui"]:
            if k in d:
                d = k + ("·" + d.split(k, 1)[1].strip("(),' ")[:6] if k in d else "")
                break
        dyn[d if d else "?"] += 1
    sample = rows[0] if rows else None
    return {
        "kind": "image dir + manifest.jsonl",
        "files": len(jpgs),
        "manifest_rows": len(rows),
        "size": dir_size(p),
        "sample_keys": list(sample.keys()) if sample else [],
        "dynasty_top5": dyn.most_common(5),
        "license": (sample or {}).get("license"),
    }


def inspect_hf_parquet(p: Path) -> dict:
    parquets = list(p.rglob("*.parquet"))
    info = {"kind": "HF parquet", "files": len(parquets), "size": dir_size(p)}
    if not parquets:
        return info
    try:
        import pandas as pd
        # only read first parquet
        df = pd.read_parquet(parquets[0])
        info["columns"] = list(df.columns)
        info["rows_first_shard"] = len(df)
        info["total_shards"] = len(parquets)
        # try a sample row
        row = df.iloc[0].to_dict()
        # drop big binary cols
        row = {k: (str(v)[:80] if not isinstance(v, (int, float, str)) else v) for k, v in row.items()}
        info["sample"] = row
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_hf_arrow(p: Path) -> dict:
    arrows = list(p.rglob("*.arrow"))
    info = {"kind": "HF arrow (datasets.load_from_disk)", "files": len(arrows), "size": dir_size(p)}
    try:
        import datasets as ds
        # try each config subdir
        for sub in p.iterdir():
            if (sub / "dataset_dict.json").exists():
                d = ds.load_from_disk(sub)
                splits = {k: len(v) for k, v in d.items()}
                info.setdefault("configs", {})[sub.name] = {
                    "splits": splits,
                    "columns": list(next(iter(d.values())).column_names),
                }
                break  # don't load eval config too
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_emoart(p: Path) -> dict:
    info = {"kind": "EmoArt partial: annotation.json + style tar.gz", "size": dir_size(p)}
    ann = p / "Annotation.json"
    if ann.exists():
        with ann.open() as f:
            data = json.load(f)
        info["annotation_size"] = ann.stat().st_size
        # data could be list or dict
        if isinstance(data, list):
            info["total_annotated_paintings"] = len(data)
            sample = data[0]
        elif isinstance(data, dict):
            info["total_annotated_paintings"] = len(data)
            sample = next(iter(data.values()))
        else:
            sample = None
        if sample:
            info["sample_keys"] = list(sample.keys()) if isinstance(sample, dict) else type(sample).__name__
    info["style_archives"] = [t.name for t in p.glob("*.tar.gz")]
    return info


def inspect_deam(p: Path) -> dict:
    info = {"kind": "DEAM annotations only", "size": dir_size(p)}
    ann_dir = p / "annotations"
    if ann_dir.exists():
        # song-level CSVs + per-rater CSVs
        per_song = (ann_dir / "annotations averaged per song").rglob("*.csv")
        per_rater = (ann_dir / "annotations per each rater").rglob("*.csv")
        info["per_song_files"] = sum(1 for _ in per_song)
        info["per_rater_files"] = sum(1 for _ in per_rater)
    return info


def inspect_wikiart_emotions(p: Path) -> dict:
    inner = p / "WikiArt-Emotions"
    if not inner.exists():
        return {"kind": "WikiArt-Emotions (extracted)", "size": dir_size(p), "error": "extracted dir not found"}
    info = {"kind": "WikiArt-Emotions TSVs", "size": dir_size(p)}
    try:
        import pandas as pd
        all_tsv = inner / "WikiArt-Emotions-All.tsv"
        if all_tsv.exists():
            df = pd.read_csv(all_tsv, sep="\t", nrows=1)
            info["columns_first_10"] = list(df.columns)[:10]
            df = pd.read_csv(all_tsv, sep="\t")
            info["rows"] = len(df)
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_musiccaps_csv(p: Path) -> dict:
    csv = p / "musiccaps-public.csv"
    info = {"kind": "MusicCaps caption CSV", "size": dir_size(p)}
    if csv.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv)
            info["rows"] = len(df)
            info["columns"] = list(df.columns)
            info["balanced_subset_rows"] = int(df.get("is_balanced_subset", []).sum()) if "is_balanced_subset" in df.columns else None
            info["audioset_eval_rows"] = int(df.get("is_audioset_eval", []).sum()) if "is_audioset_eval" in df.columns else None
        except Exception as e:
            info["error"] = str(e)
    return info


def inspect_musicbench_json(p: Path) -> dict:
    info = {"kind": "MusicBench JSONL captions+features", "size": dir_size(p)}
    files = sorted(p.glob("MusicBench_*.json"))
    info["files"] = [f.name for f in files]
    counts = {}
    for f in files:
        try:
            with f.open() as g:
                n = sum(1 for _ in g)
            counts[f.name] = n
        except Exception:
            pass
    info["lines_per_file"] = counts
    return info


def inspect_generic_dir(p: Path) -> dict:
    return {
        "kind": "generic dir",
        "files": count_files(p),
        "size": dir_size(p),
    }


def inspect_rag_chunks(p: Path) -> dict:
    f = p / "chunks.jsonl"
    info = {"kind": "JSONL · RAG chunks (built from Met+Cleveland)", "size": dir_size(p)}
    if f.exists():
        rows = [json.loads(l) for l in f.open(encoding="utf-8") if l.strip()]
        info["rows"] = len(rows)
        if rows:
            info["sample_keys"] = list(rows[0].keys())
            dyn = Counter(r.get("dynasty") or "?" for r in rows)
            info["dynasty_top5"] = dyn.most_common(5)
    return info


def inspect_va_labels(p: Path) -> dict:
    f = p / "emoart_va_labels.csv"
    info = {"kind": "CSV · V-A training labels from EmoArt", "size": dir_size(p)}
    if f.exists():
        try:
            import pandas as pd
            df = pd.read_csv(f, low_memory=False)
            info["rows"] = len(df)
            info["columns"] = list(df.columns)
            info["rows_with_local_image"] = int(df["has_local_image"].sum()) if "has_local_image" in df.columns else None
            info["top_emotions"] = df["dominant_emotion"].value_counts().head(8).to_dict() if "dominant_emotion" in df.columns else None
        except Exception as e:
            info["error"] = str(e)
    return info


def inspect_instrument_captions(p: Path) -> dict:
    f = p / "instrument_captions.jsonl"
    info = {"kind": "JSONL · structured audio captions", "size": dir_size(p)}
    if f.exists():
        rows = [json.loads(l) for l in f.open(encoding="utf-8") if l.strip()]
        info["rows"] = len(rows)
        info["by_instrument"] = Counter(r.get("instrument") for r in rows).most_common()
    return info


def inspect_unified_paintings(p: Path) -> dict:
    f = p / "paintings_unified.parquet"
    info = {"kind": "Parquet · unified painting manifest (Met+Cleveland+zqman)", "size": dir_size(p)}
    if f.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(f)
            info["rows"] = len(df)
            info["columns"] = list(df.columns)
            info["by_source"] = df["source"].value_counts().to_dict()
            info["dynasty_top5"] = df["dynasty"].value_counts().head(5).to_dict()
        except Exception as e:
            info["error"] = str(e)
    return info


# --- dispatcher ---

DATASET_PLAN = [
    # (path relative to DATA_ROOT, display name, inspector)
    ("images/met_asian_art",       "Met Asian Art",            lambda p: inspect_image_dir_with_manifest(p, "met")),
    ("images/cleveland_chinese",   "Cleveland Chinese Art",    lambda p: inspect_image_dir_with_manifest(p, "cleveland")),
    ("images/zqman",               "zqman Text2image-ChinesePainting", inspect_hf_parquet),
    ("images/mingyy",              "mingyy Chinese Landscape (PARTIAL 12/89)", inspect_hf_parquet),
    ("images/amazarashi",          "AmazarashiEndure Landscape", inspect_generic_dir),
    ("images/artbench",            "ArtBench-10",              inspect_hf_parquet),
    ("images/wikiart_emotions",    "WikiArt-Emotions",         inspect_wikiart_emotions),
    ("images/emoart",              "EmoArt-130k (PARTIAL: labels 100%, 9 styles)", inspect_emoart),
    ("audio/13dim",                "13-Dim Music Emotions",    inspect_hf_parquet),
    ("audio/deam",                 "DEAM annotations",         inspect_deam),
    ("audio/ccmusic_guzheng99",    "CCMusic Guzheng_Tech99",   inspect_hf_arrow),
    ("audio/ccmusic_erhu",         "CCMusic erhu_playing_tech", inspect_hf_arrow),
    ("captions/musiccaps",         "MusicCaps captions",       inspect_musiccaps_csv),
    ("captions/musicbench",        "MusicBench captions+features", inspect_musicbench_json),
    # --- §3.2.2/3.2.4 processed outputs from echoscroll/scripts/ ---
    ("rag",                        "RAG chunks (Met+Cleveland descriptions)",     inspect_rag_chunks),
    ("annotations",                "EmoArt V-A labels (continuous, 132K rows)",   inspect_va_labels),
    ("captions",                   "Instrument captions (Guzheng+erhu+13-dim)",   inspect_instrument_captions),
    ("processed",                  "Unified painting manifest (parquet+csv)",     inspect_unified_paintings),
]


def render_markdown(records: list[tuple]) -> str:
    L = []
    L.append("# EchoScroll · Data Inventory")
    L.append("")
    L.append("> Auto-generated by `inspect_data.py`. Walks every dataset directory under `data/`")
    L.append("> and reports kind, file count, total bytes on disk, schema and a sample row.")
    L.append("")

    # quick summary table
    total_bytes = sum(r[2].get("size", 0) for r in records)
    L.append(f"**Total: {len(records)} datasets · {human_size(total_bytes)} on disk**")
    L.append("")
    L.append("| # | Dataset | Kind | Size | Key counts |")
    L.append("|---|---|---|---:|---|")
    for i, (path, name, info) in enumerate(records, 1):
        size = human_size(info.get("size", 0))
        bits = []
        if "rows" in info: bits.append(f"rows={info['rows']}")
        if "manifest_rows" in info: bits.append(f"manifest={info['manifest_rows']}")
        if "files" in info: bits.append(f"files={info['files']}")
        if "rows_first_shard" in info and "total_shards" in info:
            bits.append(f"shards={info['total_shards']}×{info['rows_first_shard']}+ rows")
        if "total_annotated_paintings" in info:
            bits.append(f"annot={info['total_annotated_paintings']}")
        if "configs" in info:
            for cfg, body in info["configs"].items():
                splits = body["splits"]
                bits.append(f"{cfg}: " + "/".join(f"{k}={v}" for k, v in splits.items()))
        L.append(f"| {i} | **{name}** | {info['kind']} | {size} | {', '.join(bits) or '—'} |")
    L.append("")

    # per-dataset details
    L.append("---")
    L.append("")
    L.append("## Details")
    L.append("")
    for path, name, info in records:
        L.append(f"### {name}")
        L.append(f"- **Path**: `data/{path}`")
        L.append(f"- **Kind**: {info['kind']}")
        L.append(f"- **Size**: {human_size(info.get('size', 0))}")
        for k, v in info.items():
            if k in ("kind", "size"):
                continue
            if isinstance(v, dict):
                L.append(f"- **{k}**:")
                for kk, vv in v.items():
                    L.append(f"    - `{kk}` → `{vv}`")
            elif isinstance(v, list):
                if v and isinstance(v[0], tuple):
                    L.append(f"- **{k}**: " + ", ".join(f"{a} ({b})" for a, b in v))
                else:
                    L.append(f"- **{k}**: `{v[:8]}`" + (f" … ({len(v)} total)" if len(v) > 8 else ""))
            else:
                L.append(f"- **{k}**: `{v}`")
        L.append("")

    return "\n".join(L)


def main():
    records = []
    for rel, name, inspector in DATASET_PLAN:
        p = DATA_ROOT / rel
        if not p.exists():
            print(f"[skip] {rel} not found")
            continue
        print(f"[inspect] {name}…")
        try:
            info = inspector(p)
        except Exception as e:
            info = {"kind": "FAILED", "error": str(e), "size": dir_size(p)}
        records.append((rel, name, info))

    md = render_markdown(records)
    OUT.write_text(md, encoding="utf-8")
    print(f"\nwrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
