# M3 · Art-history RAG

Cultural-context retriever for EchoScroll (§3.2.4 of the proposal). Given a
painting query (text, or text + fused multimodal vector), it returns the
top-k most relevant snippets from a Chinese art-history knowledge base.

**I/O contract**
- Build input: list of dicts `{"text", "dynasty", "painter", "school", "motif", "source"}`.
- Query input: a query string (and optionally a fused multimodal vector projected into the bge-m3 embedding space).
- Query output: `[{"text", "score", "metadata"}, ...]`, top-k by cosine similarity, with optional `filters={"dynasty": "Song"}` post-filtering.

**Models / index**
- Embedding: `BAAI/bge-m3` via `sentence-transformers` (CPU). **First run downloads ~2 GB of weights**; subsequent runs use the HF cache.
- Index: FAISS `IndexFlatIP` over L2-normalised embeddings (cosine similarity). Switch to `IndexHNSWFlat` or `IndexIVFFlat` when the corpus grows beyond ~10⁴ chunks.

**Run**
```bash
pip install -r requirements.txt
python demo.py
```
Demo builds an index from `seed_corpus.py` (~20 snippets covering Tang/Song/Yuan/Ming/Qing literati landscape, bird-and-flower, Mi family cloud-mountain, Bada Shanren, etc.), runs 3 EN/ZH queries, demonstrates the dynasty filter, then reloads from disk and exercises the multimodal-rerank path.

**Swap to a bigger corpus**: prepare a JSON list with the same chunk schema (e.g. extracted from museum descriptions or art-history textbooks), then `ArtRAGStore().build(my_chunks, "my_index/")`. No code changes needed; query API stays the same.

**Files**: `rag_store.py` (class), `seed_corpus.py` (sample data), `demo.py` (entry point), `requirements.txt`, `README.md` (this file).
