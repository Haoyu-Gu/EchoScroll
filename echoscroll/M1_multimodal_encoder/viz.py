"""
Visualizations for EchoScroll M1 Multimodal Encoder.

NOTE: This script does NOT download CLIP or bge-m3 weights. Instead, it uses
deterministic random embeddings at the documented per-modality dimensions and
runs them through the actual `FusionHead` (with `torch.randn` initialized
weights, fixed seed). The figures are intended for layout / schematic purposes
only — they illustrate the encoder architecture and the qualitative behaviour
of the fusion head, not real CLIP / bge-m3 semantic geometry.

Outputs (saved to ./figures/):
    1. fig_modality_norms.png      — L2 norms of e_img / e_txt / e_meta / z
                                     for 4 synthetic painting inputs.
    2. fig_similarity_heatmap.png  — 4x4 cosine similarity of fused z vectors.
    3. fig_fusion_diagram.png      — Boxes-and-arrows schematic of the encoder.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from encoder import (
    CLIP_IMAGE_DIM,
    FUSED_DIM,
    META_RAW_DIM,
    SBERT_TEXT_DIM,
    FusionHead,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

SEED = 20260513
PAINTINGS = [
    "Northern Song landscape",
    "Bird-and-flower",
    "Calligraphy scroll",
    "Bamboo ink",
]

# Clean qualitative palette (color-blind friendly Okabe–Ito-ish).
PALETTE = {
    "e_img":  "#0072B2",   # blue
    "e_txt":  "#D55E00",   # vermillion
    "e_meta": "#009E73",   # green
    "z":      "#CC79A7",   # purple-pink
}

CAPTION = (
    "Random-projection placeholder embeddings used for figure generation "
    "(no model weights downloaded)."
)


# ---------------------------------------------------------------------------
# Synthetic embedding generation
# ---------------------------------------------------------------------------

def make_random_embeddings(seed: int = SEED) -> dict[str, np.ndarray]:
    """Produce deterministic synthetic (e_img, e_txt, e_meta) for each painting.

    Each per-modality vector is L2-normalised to mimic the real encoder's
    output convention (CLIP image features and bge-m3 CLS are L2-normalised;
    metadata hash vectors are bounded). Returns a dict keyed by painting name
    with subkeys 'e_img', 'e_txt', 'e_meta'.
    """
    rng = np.random.default_rng(seed)
    out: dict[str, dict[str, np.ndarray]] = {}
    for name in PAINTINGS:
        e_img = rng.standard_normal(CLIP_IMAGE_DIM).astype(np.float32)
        e_img /= np.linalg.norm(e_img) + 1e-8
        e_txt = rng.standard_normal(SBERT_TEXT_DIM).astype(np.float32)
        e_txt /= np.linalg.norm(e_txt) + 1e-8
        e_meta = rng.standard_normal(META_RAW_DIM).astype(np.float32)
        e_meta /= np.linalg.norm(e_meta) + 1e-8
        out[name] = {"e_img": e_img, "e_txt": e_txt, "e_meta": e_meta}
    return out


def run_fusion(per_modality: dict[str, dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    """Run each painting's modality vectors through a freshly-seeded FusionHead.

    Returns dict keyed by painting name with z vectors (np.float32).
    """
    torch.manual_seed(SEED)
    fusion = FusionHead(
        img_dim=CLIP_IMAGE_DIM,
        txt_dim=SBERT_TEXT_DIM,
        meta_dim=META_RAW_DIM,
        out_dim=FUSED_DIM,
    )
    fusion.eval()

    z_out: dict[str, np.ndarray] = {}
    with torch.no_grad():
        for name, vecs in per_modality.items():
            t_img = torch.from_numpy(vecs["e_img"]).unsqueeze(0)
            t_txt = torch.from_numpy(vecs["e_txt"]).unsqueeze(0)
            t_meta = torch.from_numpy(vecs["e_meta"]).unsqueeze(0)
            z = fusion(t_img, t_txt, t_meta)[0].cpu().float().numpy()
            z_out[name] = z
    return z_out


# ---------------------------------------------------------------------------
# Figure 1: bar chart of modality L2 norms
# ---------------------------------------------------------------------------

def fig_modality_norms(
    per_modality: dict[str, dict[str, np.ndarray]],
    z_by_name: dict[str, np.ndarray],
    save_path: Path,
) -> None:
    modalities = ["e_img", "e_txt", "e_meta", "z"]
    names = list(per_modality.keys())
    n_paint = len(names)
    n_mod = len(modalities)

    # Compute norms: shape [n_mod, n_paint].
    norms = np.zeros((n_mod, n_paint), dtype=np.float32)
    for j, name in enumerate(names):
        norms[0, j] = float(np.linalg.norm(per_modality[name]["e_img"]))
        norms[1, j] = float(np.linalg.norm(per_modality[name]["e_txt"]))
        norms[2, j] = float(np.linalg.norm(per_modality[name]["e_meta"]))
        norms[3, j] = float(np.linalg.norm(z_by_name[name]))

    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    x = np.arange(n_paint)
    bar_w = 0.20
    offsets = np.linspace(-1.5, 1.5, n_mod) * bar_w

    for i, mod in enumerate(modalities):
        ax.bar(
            x + offsets[i],
            norms[i],
            width=bar_w,
            label=mod,
            color=PALETTE[mod],
            edgecolor="white",
            linewidth=0.8,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=10, ha="right")
    ax.set_ylabel(r"$\ell_2$ norm")
    ax.set_title("Per-modality and fused embedding norms across 4 synthetic inputs")
    ax.legend(title="vector", loc="upper right", frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.text(0.5, -0.02, CAPTION, ha="center", va="top",
             fontsize=8, style="italic", color="#555555")

    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: cosine similarity heatmap of z
# ---------------------------------------------------------------------------

def fig_similarity_heatmap(
    z_by_name: dict[str, np.ndarray],
    save_path: Path,
) -> None:
    names = list(z_by_name.keys())
    Z = np.stack([z_by_name[n] for n in names], axis=0)  # [4, FUSED_DIM]
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-8)
    sim = Zn @ Zn.T  # [4, 4]

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(
        sim,
        annot=True,
        fmt=".3f",
        cmap="RdBu_r",
        center=0.0,
        vmin=-1.0,
        vmax=1.0,
        square=True,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "cosine similarity", "shrink": 0.8},
        xticklabels=names,
        yticklabels=names,
        ax=ax,
    )
    ax.set_title("Cosine similarity of fused vectors $z$ across 4 inputs")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    fig.text(0.5, -0.02, CAPTION, ha="center", va="top",
             fontsize=8, style="italic", color="#555555")

    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: schematic boxes-and-arrows diagram
# ---------------------------------------------------------------------------

def _add_box(ax, xy, w, h, text, *, face, edge, text_color="black", fontsize=10):
    x, y = xy
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4,
        facecolor=face,
        edgecolor=edge,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center",
            fontsize=fontsize, color=text_color)


def _add_arrow(ax, src, dst, *, color="#444444"):
    arrow = FancyArrowPatch(
        src, dst,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.4,
        color=color,
        shrinkA=2, shrinkB=2,
    )
    ax.add_patch(arrow)


def fig_fusion_diagram(save_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Column x-positions (left edges) and shared box sizing.
    col_x = [0.4, 3.4, 6.4, 9.0, 10.7]
    box_w = 2.4
    box_h = 0.95

    # Row y-centers (top, middle, bottom).
    rows_y = [4.6, 3.0, 1.4]
    row_top, row_mid, row_bot = rows_y

    # ---- Column 1: input boxes -------------------------------------------
    inputs = [
        ("Image", "PIL.Image (RGB, 224x224)", PALETTE["e_img"]),
        ("Text",  "str (bilingual prompt)",   PALETTE["e_txt"]),
        ("Metadata", "dict[str, str]",        PALETTE["e_meta"]),
    ]
    for (title, sub, color), y in zip(inputs, rows_y):
        _add_box(
            ax, (col_x[0], y - box_h / 2), box_w, box_h,
            f"{title}\n" + r"$\mathit{" + sub.replace(" ", r"\,") + r"}$",
            face="white", edge=color, text_color="black", fontsize=9,
        )

    # ---- Column 2: encoder boxes -----------------------------------------
    encoders = [
        ("CLIP-ViT-L/14",       r"$e_\mathrm{img} \in \mathbb{R}^{768}$",  PALETTE["e_img"]),
        ("BAAI/bge-m3 (CLS)",   r"$e_\mathrm{txt} \in \mathbb{R}^{1024}$", PALETTE["e_txt"]),
        ("Hash-bucket embed.",  r"$e_\mathrm{meta} \in \mathbb{R}^{256}$", PALETTE["e_meta"]),
    ]
    for (title, dim_str, color), y in zip(encoders, rows_y):
        _add_box(
            ax, (col_x[1], y - box_h / 2), box_w, box_h,
            f"{title}\n{dim_str}",
            face=color, edge=color, text_color="white", fontsize=9.5,
        )

    # ---- Column 3: linear projection labels -----------------------------
    projections = [
        (r"$W_v \in \mathbb{R}^{768\times 768}$",  PALETTE["e_img"]),
        (r"$W_t \in \mathbb{R}^{768\times 1024}$", PALETTE["e_txt"]),
        (r"$W_m \in \mathbb{R}^{768\times 256} + b$", PALETTE["e_meta"]),
    ]
    proj_w = 2.2
    for (label, color), y in zip(projections, rows_y):
        _add_box(
            ax, (col_x[2], y - box_h / 2), proj_w, box_h,
            label,
            face="white", edge=color, text_color="black", fontsize=9.5,
        )

    # ---- Column 4: fusion box (spans rows) -------------------------------
    fusion_x = col_x[3]
    fusion_y = row_bot - 0.2
    fusion_w = 1.5
    fusion_h = (row_top + box_h / 2) - (row_bot - box_h / 2 + 0.2)
    fbox = FancyBboxPatch(
        (fusion_x, row_bot - box_h / 2),
        fusion_w, fusion_h,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=1.6,
        facecolor="#F2E9D8",
        edgecolor="#8C6E2F",
    )
    ax.add_patch(fbox)
    ax.text(
        fusion_x + fusion_w / 2,
        row_mid,
        "Fusion\n" + r"$\sum + \mathrm{GELU}$",
        ha="center", va="center",
        fontsize=11, color="#3a2c0a",
    )

    # ---- Column 5: output box -------------------------------------------
    out_w = 1.3
    out_h = 1.1
    out_x = col_x[4]
    out_y = row_mid - out_h / 2
    _add_box(
        ax, (out_x, out_y), out_w, out_h,
        r"$z \in \mathbb{R}^{768}$",
        face=PALETTE["z"], edge=PALETTE["z"], text_color="white", fontsize=11,
    )

    # ---- Arrows: column-to-column ---------------------------------------
    # input -> encoder
    for y in rows_y:
        _add_arrow(ax,
                   (col_x[0] + box_w, y),
                   (col_x[1], y))
    # encoder -> projection
    for y in rows_y:
        _add_arrow(ax,
                   (col_x[1] + box_w, y),
                   (col_x[2], y))
    # projection -> fusion (converge)
    for y in rows_y:
        _add_arrow(ax,
                   (col_x[2] + proj_w, y),
                   (fusion_x, row_mid))
    # fusion -> output
    _add_arrow(ax,
               (fusion_x + fusion_w, row_mid),
               (out_x, row_mid))

    ax.set_title("EchoScroll M1: Multimodal Encoder fusion architecture",
                 fontsize=13, pad=10)

    fig.text(0.5, 0.02, CAPTION, ha="center", va="bottom",
             fontsize=8, style="italic", color="#555555")

    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    sns.set_theme(style="white", context="talk", font_scale=0.7)

    print(f"[viz] Generating placeholder embeddings (seed={SEED}) ...")
    per_mod = make_random_embeddings(SEED)
    z_by_name = run_fusion(per_mod)

    f1 = FIG_DIR / "fig_modality_norms.png"
    f2 = FIG_DIR / "fig_similarity_heatmap.png"
    f3 = FIG_DIR / "fig_fusion_diagram.png"

    print(f"[viz] Writing {f1.name} ...")
    fig_modality_norms(per_mod, z_by_name, f1)

    print(f"[viz] Writing {f2.name} ...")
    fig_similarity_heatmap(z_by_name, f2)

    print(f"[viz] Writing {f3.name} ...")
    fig_fusion_diagram(f3)

    for p in (f1, f2, f3):
        assert p.exists(), f"Missing output: {p}"
        print(f"  -> {p}  ({p.stat().st_size / 1024:.1f} KB)")

    print("[viz] Done.")


if __name__ == "__main__":
    main()
