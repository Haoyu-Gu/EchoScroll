"""§3.2.2 & §3.2.4 — Build the art-history RAG corpus from Met/Cleveland manifests.

Each painting's description / wall_description / title becomes one (or several)
chunk(s) tagged with dynasty / artist / source. Writes:
  data/rag/chunks.jsonl   each line {text, dynasty, painter, school, motif, source, painting_id}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DATA = Path("/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/开题/EchoScroll_data_plan/data")
OUT = DATA / "rag" / "chunks.jsonl"
CHUNK_MAX = 500  # ~500 chars; we don't have a tokenizer here so use chars as a coarse proxy

DYNASTY_TOKENS = ("Tang", "Five Dynasties", "Northern Song", "Southern Song", "Song",
                  "Yuan", "Ming", "Qing", "Han", "Sui", "Jin")


def detect_dynasty(text: str | None) -> str | None:
    if not text:
        return None
    for tok in DYNASTY_TOKENS:
        if tok.lower() in text.lower():
            return tok
    return None


def chunk(text: str, max_chars: int = CHUNK_MAX) -> list[str]:
    """Split on sentence boundaries, glue until max_chars."""
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return [text]
    sents = re.split(r"(?<=[.!?。！？])\s+", text)
    out, buf = [], ""
    for s in sents:
        if len(buf) + len(s) + 1 > max_chars:
            if buf:
                out.append(buf.strip())
                buf = s
            else:
                # single sentence too long — hard split
                out.append(s[:max_chars])
                buf = s[max_chars:]
        else:
            buf = (buf + " " + s).strip()
    if buf:
        out.append(buf.strip())
    return out


def from_met() -> list[dict]:
    p = DATA / "images/met_asian_art/manifest.jsonl"
    chunks = []
    if not p.exists():
        return chunks
    for line in p.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        text_parts = [
            r.get("title"), r.get("artist"),
            r.get("medium"), r.get("classification"),
            r.get("period"), r.get("dynasty"), r.get("culture"),
        ]
        text = ". ".join(t for t in text_parts if t)
        for c in chunk(text):
            chunks.append({
                "text":        c,
                "dynasty":     detect_dynasty(r.get("dynasty") or r.get("period") or r.get("culture")),
                "painter":     r.get("artist"),
                "school":      None,
                "motif":       r.get("classification"),
                "source":      f"met:{r.get('id')}",
                "painting_id": f"met_{r.get('id')}",
            })
    return chunks


def from_cleveland() -> list[dict]:
    p = DATA / "images/cleveland_chinese/manifest.jsonl"
    chunks = []
    if not p.exists():
        return chunks
    for line in p.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Cleveland: description + wall_description are the rich body
        desc = r.get("description") or ""
        wall = r.get("wall_description") or ""
        for body in (desc, wall):
            for c in chunk(body):
                culture = r.get("culture")
                if isinstance(culture, list):
                    culture = culture[0] if culture else None
                chunks.append({
                    "text":        c,
                    "dynasty":     detect_dynasty(culture or r.get("dynasty")),
                    "painter":     r.get("artist"),
                    "school":      None,
                    "motif":       r.get("classification"),
                    "source":      f"cleveland:{r.get('id')}",
                    "painting_id": f"cle_{r.get('id')}",
                })
        # Also include the metadata-only stub as a structural chunk
        head_parts = [r.get("title"), r.get("artist"), r.get("technique"), r.get("creation_date")]
        head = ". ".join(t for t in head_parts if t)
        if head and not desc and not wall:
            culture = r.get("culture")
            if isinstance(culture, list):
                culture = culture[0] if culture else None
            chunks.append({
                "text":        head,
                "dynasty":     detect_dynasty(culture or r.get("dynasty")),
                "painter":     r.get("artist"),
                "school":      None,
                "motif":       r.get("classification"),
                "source":      f"cleveland:{r.get('id')}",
                "painting_id": f"cle_{r.get('id')}",
            })
    return chunks


def main() -> None:
    met_chunks = from_met()
    cle_chunks = from_cleveland()
    all_chunks = met_chunks + cle_chunks
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"  met chunks:        {len(met_chunks):>5}")
    print(f"  cleveland chunks:  {len(cle_chunks):>5}")
    print(f"  total:             {len(all_chunks):>5}")
    print(f"  wrote {OUT}  ({OUT.stat().st_size:,} bytes)")

    from collections import Counter
    dyn = Counter(c["dynasty"] for c in all_chunks)
    print("\n  dynasty distribution:")
    for k, v in dyn.most_common():
        print(f"    {str(k):>20}  {v}")


if __name__ == "__main__":
    main()
