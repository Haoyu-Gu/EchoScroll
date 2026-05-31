"""
M3 Art-history RAG: visualizations.

Generates three figures into ./figures/:
  - fig_retrieval_scores.png : top-5 retrieval scores for 3 demo queries
  - fig_corpus_pca.png       : 2D PCA scatter of corpus embeddings by dynasty
  - fig_query_pipeline.png   : boxes-and-arrows schematic of the RAG pipeline

To avoid downloading the ~2GB BGE-M3 checkpoint, we monkey-patch the
sentence-transformers encoder used by `rag_store.ArtRAGStore` with a
deterministic `MockEmbedder`: each text is hashed and used to seed a numpy
RNG that emits a stable 384-dim vector. Semantically meaningless distances,
but enough to exercise the retrieval / FAISS code-path and draw figures.

Captions / titles flag that mock embeddings are in use.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import seaborn as sns
from sklearn.decomposition import PCA


def _configure_cjk_font() -> None:
    """Pick a CJK-capable font so 元代文人山水 etc. render correctly."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    chosen = None
    for path in candidates:
        if os.path.exists(path):
            try:
                font_manager.fontManager.addfont(path)
            except Exception:
                pass
            try:
                chosen = font_manager.FontProperties(fname=path).get_name()
                break
            except Exception:
                continue
    if chosen:
        plt.rcParams["font.family"] = [chosen, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_configure_cjk_font()

# Make sure we can import the M3 module regardless of where viz.py is launched.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import rag_store
from rag_store import ArtRAGStore, _chunk_to_embedding_text, ArtChunk
from seed_corpus import SEED_CHUNKS

SEED = 42
EMB_DIM = 384
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

MOCK_TAG = "Mock embeddings (no BGE-M3 download required for figures)"


# ---------------------------------------------------------------------------
# Deterministic mock embedder
# ---------------------------------------------------------------------------

class MockEmbedder:
    """Hash-seeded deterministic embedder, drop-in for SentenceTransformer."""

    def __init__(self, dim: int = EMB_DIM):
        self.dim = dim

    @staticmethod
    def _seed_from_text(text: str) -> int:
        # Stable across runs (Python's built-in hash() is salted per-process,
        # so use a hand-rolled FNV-1a 32-bit hash instead).
        h = 0x811C9DC5
        for ch in text.encode("utf-8"):
            h ^= ch
            h = (h * 0x01000193) & 0xFFFFFFFF
        return h

    def _embed_one(self, text: str) -> np.ndarray:
        seed = self._seed_from_text(text) % (2 ** 32)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self.dim).astype("float32")
        return v

    def encode(
        self,
        texts,
        batch_size: int = 8,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = False,
    ) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        out = np.stack([self._embed_one(t) for t in texts], axis=0)
        if normalize_embeddings:
            n = np.linalg.norm(out, axis=1, keepdims=True) + 1e-12
            out = out / n
        return out


def install_mock_encoder() -> None:
    """Monkey-patch rag_store._get_encoder so .build()/.query() use MockEmbedder."""
    mock = MockEmbedder(EMB_DIM)

    def _patched_get_encoder(model_name: str):
        # ignore model_name; always return the same mock
        return mock

    rag_store._get_encoder = _patched_get_encoder
    # Also clear any pre-cached real encoder.
    rag_store._MODEL_CACHE.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DYNASTY_ORDER = [
    "Tang", "Northern Song", "Southern Song", "Yuan", "Ming", "Qing", "other",
]


def _dynasty_key(d: str | None) -> str:
    if d is None or d == "":
        return "other"
    return d if d in DYNASTY_ORDER else "other"


def _truncate(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _short_label(chunk: dict) -> str:
    """Short annotation for a corpus chunk: painter or motif fallback."""
    painter = chunk.get("painter")
    if painter:
        # Keep only first painter listed
        return painter.split(";")[0].strip()
    motif = chunk.get("motif") or ""
    return motif.split(";")[0].strip() if motif else (chunk.get("school") or "?")


# ---------------------------------------------------------------------------
# Build a temporary store (mock-encoded) we can reuse across figures
# ---------------------------------------------------------------------------

def build_mock_store(tmp_dir: Path) -> ArtRAGStore:
    install_mock_encoder()
    store = ArtRAGStore(model_name="mock-bge-m3")
    store.build(SEED_CHUNKS, index_dir=str(tmp_dir))
    return store


# ---------------------------------------------------------------------------
# Figure 1: retrieval scores
# ---------------------------------------------------------------------------

QUERIES = [
    "Northern Song landscape",
    "Bada Shanren eccentric birds",
    "元代文人山水",  # 元代文人山水
]


def fig_retrieval_scores(store: ArtRAGStore, out_path: Path) -> None:
    top_k = 5
    fig, axes = plt.subplots(1, 3, figsize=(18, 8), sharey=False)
    palette = sns.color_palette("crest", n_colors=top_k)

    for ax, q in zip(axes, QUERIES):
        results = store.query(q, top_k=top_k)
        scores = [r["score"] for r in results]
        labels = [_truncate(r["text"], 32) for r in results]
        positions = np.arange(len(results))

        bars = ax.bar(positions, scores, color=palette, edgecolor="black", linewidth=0.6)
        ax.set_title(f'Query: "{q}"', fontsize=11, pad=6)
        ax.set_xticks(positions)
        ax.set_xticklabels([f"#{i+1}" for i in range(len(results))], fontsize=10)
        ax.set_ylabel("cosine score (mock)")

        # Symmetric y range so negative bars don't get cramped, and leave
        # enough head/foot-room for rotated text annotations.
        y_max_raw = max(scores + [0.0])
        y_min_raw = min(scores + [0.0])
        span = max(y_max_raw - y_min_raw, 0.05)
        pad = span * 0.06
        ax.set_ylim(y_min_raw - 0.3 * span, y_max_raw + 1.6 * span)

        for bar, label, score in zip(bars, labels, scores):
            # Place the truncated text above the top of the bar's positive
            # half OR above zero if the bar is negative -- always rotated
            # upwards so columns don't collide horizontally.
            anchor_y = max(bar.get_height(), 0.0) + pad
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                anchor_y,
                label,
                rotation=35,
                ha="left",
                va="bottom",
                fontsize=8,
                color="#222",
            )
            # Numeric score INSIDE the bar (slightly inset from the tip).
            tip = bar.get_height()
            inside = tip - pad if tip >= 0 else tip + pad
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                inside,
                f"{score:.2f}",
                ha="center",
                va="top" if tip >= 0 else "bottom",
                fontsize=8,
                color="white",
                fontweight="bold",
            )

        ax.axhline(0.0, color="#888", linewidth=0.8)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.set_axisbelow(True)

    fig.suptitle(
        f"M3 Art-RAG top-5 retrieval scores per query  --  {MOCK_TAG}",
        fontsize=13,
        y=0.995,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: corpus PCA scatter
# ---------------------------------------------------------------------------

def fig_corpus_pca(store: ArtRAGStore, out_path: Path) -> None:
    n = len(store)
    vecs = np.vstack([store._index.reconstruct(i) for i in range(n)])  # (n, d)

    pca = PCA(n_components=2, random_state=SEED)
    coords = pca.fit_transform(vecs)
    var = pca.explained_variance_ratio_

    dynasties = [_dynasty_key(c.dynasty) for c in store._chunks]
    palette = sns.color_palette("tab10", n_colors=len(DYNASTY_ORDER))
    dyn_to_color = {d: palette[i] for i, d in enumerate(DYNASTY_ORDER)}

    fig, ax = plt.subplots(figsize=(11, 8))
    for d in DYNASTY_ORDER:
        mask = np.array([dy == d for dy in dynasties])
        if not mask.any():
            continue
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=[dyn_to_color[d]],
            s=120,
            edgecolor="black",
            linewidth=0.7,
            label=d,
            alpha=0.9,
        )

    for i, c in enumerate(store._chunks):
        label = _short_label(c.to_dict())
        ax.annotate(
            label,
            (coords[i, 0], coords[i, 1]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=7.5,
            color="#222",
        )

    ax.set_xlabel(f"PC1 ({var[0]*100:.1f}% var)")
    ax.set_ylabel(f"PC2 ({var[1]*100:.1f}% var)")
    ax.set_title(
        f"M3 Art-RAG corpus PCA (20 chunks)  --  {MOCK_TAG}",
        fontsize=12,
    )
    ax.grid(linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    ax.legend(
        title="Dynasty",
        loc="best",
        frameon=True,
        fontsize=9,
        title_fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: pipeline schematic
# ---------------------------------------------------------------------------

def fig_query_pipeline(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 4.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis("off")

    boxes = [
        {
            "xy": (0.2, 1.3),
            "w": 2.2,
            "h": 1.4,
            "label": "Input\n(painting + text)",
            "fc": "#FDE7C9",
            "ec": "#C68B4C",
        },
        {
            "xy": (3.0, 1.3),
            "w": 2.4,
            "h": 1.4,
            "label": "bge-m3\nencoder",
            "fc": "#D6E8FA",
            "ec": "#3A6FB4",
        },
        {
            "xy": (6.0, 1.3),
            "w": 2.4,
            "h": 1.4,
            "label": "FAISS\nIndexFlatIP",
            "fc": "#E5DAF5",
            "ec": "#6A45A8",
        },
        {
            "xy": (9.0, 1.3),
            "w": 2.4,
            "h": 1.4,
            "label": "top-k\nretrieval",
            "fc": "#D5F0DA",
            "ec": "#3E8B4E",
        },
        {
            "xy": (12.0, 1.3),
            "w": 1.8,
            "h": 1.4,
            "label": "Output\nsnippets",
            "fc": "#FFDADA",
            "ec": "#B83A3A",
        },
    ]

    centres = []
    for b in boxes:
        patch = FancyBboxPatch(
            b["xy"],
            b["w"],
            b["h"],
            boxstyle="round,pad=0.02,rounding_size=0.18",
            linewidth=1.6,
            facecolor=b["fc"],
            edgecolor=b["ec"],
        )
        ax.add_patch(patch)
        cx = b["xy"][0] + b["w"] / 2
        cy = b["xy"][1] + b["h"] / 2
        centres.append((cx, cy, b["xy"][0], b["xy"][0] + b["w"]))
        ax.text(
            cx,
            cy,
            b["label"],
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#222",
        )

    # Arrows between consecutive boxes.
    for i in range(len(centres) - 1):
        _, cy_a, _, right_a = centres[i]
        _, cy_b, left_b, _ = centres[i + 1]
        arrow = FancyArrowPatch(
            (right_a + 0.05, cy_a),
            (left_b - 0.05, cy_b),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=1.6,
            color="#444",
        )
        ax.add_patch(arrow)

    # Auxiliary annotations under the arrows.
    ann = [
        (centres[0][3] + (centres[1][2] - centres[0][3]) / 2, 1.1, "text+meta\nconcat"),
        (centres[1][3] + (centres[2][2] - centres[1][3]) / 2, 1.1, "1024-d vec\n(L2 norm)"),
        (centres[2][3] + (centres[3][2] - centres[2][3]) / 2, 1.1, "cosine\nsearch"),
        (centres[3][3] + (centres[4][2] - centres[3][3]) / 2, 1.1, "rank +\nfilter"),
    ]
    for x, y, txt in ann:
        ax.text(x, y, txt, ha="center", va="top", fontsize=8.5, color="#555", style="italic")

    ax.set_title(
        f"M3 Art-RAG query pipeline  --  {MOCK_TAG}",
        fontsize=13,
        pad=10,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    np.random.seed(SEED)
    sns.set_theme(context="paper", style="white")
    # seaborn resets font.family -- re-apply CJK font now.
    _configure_cjk_font()

    # Build a mock-encoded store inside the figures dir (kept for reproducibility).
    tmp_index_dir = FIG_DIR / "_mock_index"
    store = build_mock_store(tmp_index_dir)

    out1 = FIG_DIR / "fig_retrieval_scores.png"
    out2 = FIG_DIR / "fig_corpus_pca.png"
    out3 = FIG_DIR / "fig_query_pipeline.png"

    fig_retrieval_scores(store, out1)
    fig_corpus_pca(store, out2)
    fig_query_pipeline(out3)

    print("Wrote:")
    for p in (out1, out2, out3):
        size_kb = os.path.getsize(p) / 1024
        print(f"  {p}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
