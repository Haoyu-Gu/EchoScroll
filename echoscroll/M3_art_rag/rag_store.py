"""
M3 Art-history RAG: ArtRAGStore.

A small wrapper around sentence-transformers (BAAI/bge-m3) + FAISS IndexFlatIP
that stores short art-history snippets together with light metadata
(dynasty / painter / school / motif / source) and supports:

  - build(chunks, index_dir)        -- embed + persist
  - load(index_dir)                  -- restore
  - query(text, top_k=, filters=)    -- pure-text retrieval
  - query_multimodal(text, fused_vec, top_k=, alpha=, filters=)
                                     -- rerank by text-sim + visual-fused sim

Chunks are plain dicts:

    {
      "text":    str,
      "dynasty": str | None,
      "painter": str | None,
      "school":  str | None,
      "motif":   str | None,
      "source":  str,
    }

Index layout on disk (`<index_dir>/`):
    faiss.index       binary FAISS IndexFlatIP
    chunks.json       parallel metadata list (same order as vectors)
    config.json       {"model_name": ..., "dim": ...}

This module is intentionally self-contained -- it does NOT import any other
EchoScroll module.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

import numpy as np

# Lazy heavy imports so demos can import the module without paying the cost
# until .build() / .load() is actually called.
_MODEL_CACHE: dict = {}


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

@dataclass
class ArtChunk:
    """One retrieval unit in the art-history KB."""
    text: str
    source: str
    dynasty: str | None = None
    painter: str | None = None
    school: str | None = None
    motif: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ArtChunk":
        return cls(
            text=d["text"],
            source=d.get("source", "unknown"),
            dynasty=d.get("dynasty"),
            painter=d.get("painter"),
            school=d.get("school"),
            motif=d.get("motif"),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_encoder(model_name: str):
    """Load sentence-transformers model once and cache it."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name, device="cpu")
    _MODEL_CACHE[model_name] = model
    return model


def _l2_normalise(x: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalisation so that IndexFlatIP behaves as cosine sim."""
    if x.ndim == 1:
        n = np.linalg.norm(x) + 1e-12
        return x / n
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms


def _chunk_to_embedding_text(c: ArtChunk) -> str:
    """Concatenate metadata + text so embedding is metadata-aware."""
    bits = []
    if c.dynasty:
        bits.append(f"[{c.dynasty}]")
    if c.painter:
        bits.append(f"Painter: {c.painter}.")
    if c.school:
        bits.append(f"School: {c.school}.")
    if c.motif:
        bits.append(f"Motif: {c.motif}.")
    bits.append(c.text)
    return " ".join(bits)


# ---------------------------------------------------------------------------
# Main store
# ---------------------------------------------------------------------------

class ArtRAGStore:
    """FAISS-backed retriever for an art-history knowledge base."""

    DEFAULT_MODEL = "BAAI/bge-m3"

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._index = None         # faiss.IndexFlatIP
        self._chunks: list[ArtChunk] = []
        self._dim: int | None = None

    # ----- build / load / save --------------------------------------------

    def build(self, chunks: Iterable[dict | ArtChunk], index_dir: str | os.PathLike) -> "ArtRAGStore":
        """Embed `chunks` with bge-m3, build an IndexFlatIP, persist to disk."""
        import faiss

        chunks = [c if isinstance(c, ArtChunk) else ArtChunk.from_dict(c) for c in chunks]
        if not chunks:
            raise ValueError("ArtRAGStore.build: chunk list is empty.")

        encoder = _get_encoder(self.model_name)
        texts = [_chunk_to_embedding_text(c) for c in chunks]
        embs = encoder.encode(
            texts,
            batch_size=8,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        ).astype("float32")
        embs = _l2_normalise(embs)

        dim = embs.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embs)

        self._index = index
        self._chunks = chunks
        self._dim = dim

        self._persist(index_dir)
        return self

    def _persist(self, index_dir: str | os.PathLike) -> None:
        import faiss
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_dir / "faiss.index"))
        with open(index_dir / "chunks.json", "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self._chunks], f, ensure_ascii=False, indent=2)
        with open(index_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump({"model_name": self.model_name, "dim": self._dim}, f, indent=2)

    def load(self, index_dir: str | os.PathLike) -> "ArtRAGStore":
        import faiss
        index_dir = Path(index_dir)
        with open(index_dir / "config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        with open(index_dir / "chunks.json", "r", encoding="utf-8") as f:
            chunks_raw = json.load(f)

        self.model_name = cfg["model_name"]
        self._dim = cfg["dim"]
        self._chunks = [ArtChunk.from_dict(c) for c in chunks_raw]
        self._index = faiss.read_index(str(index_dir / "faiss.index"))
        return self

    # ----- querying --------------------------------------------------------

    def _encode_query(self, text: str) -> np.ndarray:
        encoder = _get_encoder(self.model_name)
        v = encoder.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
        ).astype("float32")
        return _l2_normalise(v)

    def _match_filters(self, chunk: ArtChunk, filters: dict | None) -> bool:
        if not filters:
            return True
        for key, want in filters.items():
            got = getattr(chunk, key, None)
            if got is None:
                return False
            # case-insensitive substring match -- "Song" matches "Northern Song"
            if str(want).lower() not in str(got).lower():
                return False
        return True

    def query(
        self,
        text: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        """Retrieve top-k chunks for a textual query, with optional post-filter."""
        if self._index is None:
            raise RuntimeError("ArtRAGStore: index not built/loaded.")
        q = self._encode_query(text)

        # Over-fetch when filtering so the post-filter still yields top_k.
        fetch = top_k * 4 if filters else top_k
        fetch = min(fetch, self._index.ntotal)
        scores, idxs = self._index.search(q, fetch)

        results = []
        for score, i in zip(scores[0], idxs[0]):
            if i < 0:
                continue
            chunk = self._chunks[i]
            if not self._match_filters(chunk, filters):
                continue
            results.append({
                "text": chunk.text,
                "score": float(score),
                "metadata": {
                    "dynasty": chunk.dynasty,
                    "painter": chunk.painter,
                    "school": chunk.school,
                    "motif": chunk.motif,
                    "source": chunk.source,
                },
            })
            if len(results) >= top_k:
                break
        return results

    def query_multimodal(
        self,
        text: str,
        fused_vec: np.ndarray,
        top_k: int = 5,
        alpha: float = 0.5,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Rerank by a convex combination of:
          - text-vs-chunk similarity (uses bge-m3 embedding)
          - fused-multimodal-vector-vs-chunk similarity (assumes the caller
            has projected their multimodal vector into the same embedding
            space, e.g. via a learned linear adapter -- we just normalise it
            and dot-product against the stored chunk embeddings).

        Score = alpha * cos(text, chunk) + (1 - alpha) * cos(fused, chunk).
        alpha=1.0 -> pure text retrieval (same as .query).
        alpha=0.0 -> pure visual-fused retrieval.
        """
        if self._index is None:
            raise RuntimeError("ArtRAGStore: index not built/loaded.")

        fused = np.asarray(fused_vec, dtype="float32").reshape(-1)
        if fused.shape[0] != self._dim:
            raise ValueError(
                f"fused_vec dim {fused.shape[0]} != index dim {self._dim}. "
                "Project your multimodal vector into the bge-m3 space first."
            )
        fused = _l2_normalise(fused.reshape(1, -1))

        q_text = self._encode_query(text)

        # IndexFlatIP gives us cosine since everything is L2-normalised.
        # Reconstruct the full matrix once -- cheap for a small KB and lets us
        # combine two scores cleanly.
        n = self._index.ntotal
        all_vecs = np.vstack([self._index.reconstruct(i) for i in range(n)])  # (n, d)

        text_sim = (all_vecs @ q_text.T).reshape(-1)
        vis_sim = (all_vecs @ fused.T).reshape(-1)
        combined = alpha * text_sim + (1.0 - alpha) * vis_sim

        order = np.argsort(-combined)
        results = []
        for i in order:
            chunk = self._chunks[int(i)]
            if not self._match_filters(chunk, filters):
                continue
            results.append({
                "text": chunk.text,
                "score": float(combined[i]),
                "metadata": {
                    "dynasty": chunk.dynasty,
                    "painter": chunk.painter,
                    "school": chunk.school,
                    "motif": chunk.motif,
                    "source": chunk.source,
                    "text_sim": float(text_sim[i]),
                    "visual_sim": float(vis_sim[i]),
                },
            })
            if len(results) >= top_k:
                break
        return results

    # ----- convenience -----------------------------------------------------

    def __len__(self) -> int:
        return len(self._chunks)

    @property
    def dim(self) -> int | None:
        return self._dim
