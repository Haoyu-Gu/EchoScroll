"""Quick smoke query against an existing FAISS index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="index/faiss_bge_m3.index")
    ap.add_argument("--id-map", default="index/id_map.json")
    ap.add_argument("--meta", default="index/chunks_meta.parquet")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--q", required=True)
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    from FlagEmbedding import BGEM3FlagModel
    import faiss
    import pandas as pd

    model = BGEM3FlagModel(args.model, use_fp16=True)
    res = model.encode([args.q], return_dense=True)
    q = np.asarray(res["dense_vecs"], dtype=np.float32)
    q /= (np.linalg.norm(q, axis=1, keepdims=True) + 1e-8)

    index = faiss.read_index(args.index)
    id_map = json.loads(Path(args.id_map).read_text())
    meta = pd.read_parquet(args.meta).set_index("id")

    scores, idxs = index.search(q, args.top)
    for s, i in zip(scores[0], idxs[0]):
        cid = id_map[str(i)]
        row = meta.loc[cid].to_dict() if cid in meta.index else {}
        print(f"  {s:+.3f}  {cid:24s}  {row}")


if __name__ == "__main__":
    main()
