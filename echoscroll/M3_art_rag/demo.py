"""
M3 Art-history RAG demo.

Builds a FAISS index from the seed corpus, then runs three sample queries
(two English, one Chinese) and prints top-3 retrievals for each. Also
demonstrates a dynasty filter and a multimodal-rerank call with a random
"fused" vector.

Run:  python demo.py
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from rag_store import ArtRAGStore
from seed_corpus import SEED_CHUNKS


def _print_hits(hits: list[dict]) -> None:
    if not hits:
        print("    (no results)")
        return
    for rank, h in enumerate(hits, start=1):
        md = h["metadata"]
        head = f"  {rank}. score={h['score']:+.3f}"
        if md.get("painter"):
            head += f"  painter={md['painter']}"
        if md.get("dynasty"):
            head += f"  dynasty={md['dynasty']}"
        if md.get("school"):
            head += f"  school={md['school']}"
        print(head)
        txt = h["text"].replace("\n", " ")
        if len(txt) > 220:
            txt = txt[:217] + "..."
        print(f"     {txt}")


def main() -> None:
    index_dir = Path(tempfile.mkdtemp(prefix="echoscroll_m3_"))
    print(f"[demo] index dir: {index_dir}")
    print(f"[demo] corpus size: {len(SEED_CHUNKS)} chunks")
    print("[demo] loading BAAI/bge-m3 and embedding the seed corpus...")
    print("[demo] (first run will download ~2GB of weights; subsequent runs are instant)")

    store = ArtRAGStore().build(SEED_CHUNKS, index_dir)
    print(f"[demo] built index with dim={store.dim}, |chunks|={len(store)}")

    # ------------------------------------------------------------------
    # Query 1 (EN): canonical Northern Song landscape
    # ------------------------------------------------------------------
    q1 = "Northern Song landscape with mountains and mist, tiny travellers, monumental peak"
    print("\n[Q1 EN]", q1)
    _print_hits(store.query(q1, top_k=3))

    # ------------------------------------------------------------------
    # Query 2 (EN): eccentric early-Qing bird painting
    # ------------------------------------------------------------------
    q2 = "Eccentric monk painter, glaring-eyed birds, splashed ink, Ming loyalist"
    print("\n[Q2 EN]", q2)
    _print_hits(store.query(q2, top_k=3))

    # ------------------------------------------------------------------
    # Query 3 (ZH): quiet literati landscape
    # ------------------------------------------------------------------
    q3 = "元代文人山水，干笔，疏树空亭，没有人物的孤寂意境"
    print("\n[Q3 ZH]", q3)
    _print_hits(store.query(q3, top_k=3))

    # ------------------------------------------------------------------
    # Demonstrate the dynasty filter
    # ------------------------------------------------------------------
    print("\n[Q4 EN + filter dynasty=Southern Song]",
          "mist, water, lone figure, lyrical mood")
    _print_hits(store.query(
        "mist, water, lone figure, lyrical mood",
        top_k=3,
        filters={"dynasty": "Southern Song"},
    ))

    # ------------------------------------------------------------------
    # Reload from disk and run the multimodal-rerank API with a
    # placeholder "fused" vector (random unit vector in bge-m3 space).
    # In the real pipeline this would come from M2 / M1.
    # ------------------------------------------------------------------
    print("\n[demo] reloading store from disk...")
    store2 = ArtRAGStore().load(index_dir)
    assert len(store2) == len(store)

    rng = np.random.default_rng(0)
    fused = rng.normal(size=(store2.dim,)).astype("float32")
    print("[Q5 EN multimodal-rerank, alpha=0.7]",
          "bamboo and plum, calligraphic brush, market literati")
    hits = store2.query_multimodal(
        text="bamboo and plum, calligraphic brush, market literati",
        fused_vec=fused,
        top_k=3,
        alpha=0.7,
    )
    _print_hits(hits)

    # Cleanup: keep the tmp dir around for inspection if EHOSCROLL_KEEP set,
    # else remove it.
    if not os.environ.get("ECHOSCROLL_KEEP"):
        shutil.rmtree(index_dir, ignore_errors=True)
        print(f"\n[demo] removed temp index dir ({index_dir})")
    else:
        print(f"\n[demo] kept index dir at {index_dir}")


if __name__ == "__main__":
    main()
