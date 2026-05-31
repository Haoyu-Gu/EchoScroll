"""Assemble a 3x3 gallery image (one headline figure per module)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (module dir, headline figure, label shown on the gallery)
HEADLINES = [
    ("M1_multimodal_encoder",   "fig_fusion_diagram.png",       "M1 · Multimodal Encoder"),
    ("M2_affective_projection", "fig_circumplex.png",           "M2 · Affective Projection"),
    ("M3_art_rag",              "fig_retrieval_scores.png",     "M3 · Art-history RAG"),
    ("M4_music_generator",      "fig_mel_spectrograms.png",     "M4 · Music Generator"),
    ("M5_editing_layer",        "fig_bpm_stretch.png",          "M5 · Editing Layer"),
    ("M6_prompt_translator",    "fig_slot_heatmap.png",         "M6 · Prompt Translator"),
    ("M7_humming_interaction",  "fig_pitch_contour.png",        "M7 · Humming Interaction"),
    ("M8_frontend_backend",     "fig_system_arch.png",          "M8 · Frontend + Backend"),
    ("M9_evaluation",           "fig_metric_summary.png",       "M9 · Evaluation"),
]


def main() -> None:
    fig, axes = plt.subplots(3, 3, figsize=(20, 16))
    fig.suptitle(
        "EchoScroll · Module Showcase",
        fontsize=24, fontweight="bold", y=0.995,
    )
    for ax, (mod, png, label) in zip(axes.flat, HEADLINES):
        path = ROOT / mod / "figures" / png
        if path.exists():
            ax.imshow(mpimg.imread(path))
            ax.set_title(label, fontsize=13, fontweight="bold", pad=6)
        else:
            ax.text(0.5, 0.5, f"missing:\n{mod}/{png}", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(label, fontsize=13)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    out = ROOT / "GALLERY.png"
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out, dpi=130, bbox_inches="tight", facecolor="#fafafa")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
