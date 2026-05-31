"""Embed RAG chunks with BGE-M3 and build a FAISS IndexFlatIP."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.paths import data_root, require_file  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=None,
                    help="defaults to $ECHOSCROLL_DATA/rag/chunks.jsonl")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--out", default="index")
    args = ap.parse_args()

    chunks_path = Path(args.chunks) if args.chunks else require_file(
        data_root() / "rag" / "chunks.jsonl",
        "run echoscroll/scripts/build_rag_corpus.py first")

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] loading chunks from {chunks_path}")
    rows = [json.loads(l) for l in open(chunks_path) if l.strip()]
    texts = [r["text"] for r in rows]
    ids = [r["id"] for r in rows]
    print(f"      {len(rows)} chunks")

    print(f"[2/4] loading {args.model}")
    from FlagEmbedding import BGEM3FlagModel
    model = BGEM3FlagModel(args.model, use_fp16=True)

    print(f"[3/4] embedding batch_size={args.batch_size}")
    t0 = time.time()
    out_emb = []
    for i in tqdm(range(0, len(texts), args.batch_size)):
        batch = texts[i : i + args.batch_size]
        res = model.encode(batch, batch_size=args.batch_size,
                            max_length=args.max_length,
                            return_dense=True, return_sparse=False,
                            return_colbert_vecs=False)
        out_emb.append(np.asarray(res["dense_vecs"], dtype=np.float32))
    emb = np.concatenate(out_emb, axis=0)               # [N, 1024]
    emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8)
    elapsed = time.time() - t0
    print(f"      shape={emb.shape} in {elapsed:.1f}s")

    print(f"[4/4] building FAISS IndexFlatIP")
    import faiss
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    faiss.write_index(index, str(out / "faiss_bge_m3.index"))

    (out / "id_map.json").write_text(json.dumps(
        {i: cid for i, cid in enumerate(ids)}, indent=2, ensure_ascii=False))
    meta_rows = [{"id": r["id"], **r.get("meta", {})} for r in rows]
    pd.DataFrame(meta_rows).to_parquet(out / "chunks_meta.parquet", index=False)
    (out / "build_stats.json").write_text(json.dumps({
        "chunks": len(rows), "dim": int(emb.shape[1]),
        "model": args.model, "elapsed_s": elapsed,
        "max_length": args.max_length}, indent=2))

    print(f"done. wrote index to {out}")


if __name__ == "__main__":
    main()
