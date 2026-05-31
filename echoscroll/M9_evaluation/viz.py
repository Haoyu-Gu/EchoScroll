"""EchoScroll M9 · Evaluation visualisations.

Generates three publication-style figures from synthetic-but-plausible data
that mirrors the shapes returned by :mod:`metrics` and :mod:`human_rating`.

Outputs (all saved into ``figures/``)::

    fig_human_rating.png         Grouped bar chart of 5 Likert dimensions
                                 across systems A (EchoScroll), B (text-only),
                                 C (non-RAG ablation), with std error bars.
    fig_va_consistency_scatter.png
                                 1x2 scatter of painting vs audio V-A valence
                                 (left) and arousal (right), with diagonal y=x
                                 reference line and per-axis Pearson r.
    fig_metric_summary.png       Radar/polar chart comparing systems A, B, C
                                 across six normalised metrics (objective and
                                 human-rating dimensions).

CPU-only, no model weights, no internet. Run with::

    python viz.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # noqa: E402 — must be set before pyplot import

from pathlib import Path  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


SEED = 42
FIG_DIR = Path(__file__).resolve().parent / "figures"

SYSTEMS = ("A", "B", "C")
SYSTEM_LONG = {
    "A": "EchoScroll (full)",
    "B": "Text-only baseline",
    "C": "Non-RAG ablation",
}
SYSTEM_COLORS = {
    "A": "#d62728",  # crimson
    "B": "#1f77b4",  # steel blue
    "C": "#2ca02c",  # green
}

RATING_DIMENSIONS = (
    "painting_music_relevance",
    "emotional_consistency",
    "cultural_appropriateness",
    "audio_quality",
    "overall_preference",
)


# =====================================================================
# Figure 1 — Human rating grouped bars
# =====================================================================

def _human_rating_means_stds() -> tuple[np.ndarray, np.ndarray]:
    """Return (means, stds) of shape (n_dim, n_system).

    Hand-crafted so that EchoScroll (A) beats both baselines on every Likert
    dimension, with the largest gap on ``cultural_appropriateness`` and the
    smallest gap on ``audio_quality`` (since baselines piggy-back on the same
    audio decoder).
    """
    # Order along axis 0 matches RATING_DIMENSIONS,
    # order along axis 1 matches SYSTEMS = (A, B, C).
    means = np.array(
        [
            [4.30, 3.40, 3.70],  # painting_music_relevance
            [4.20, 3.10, 3.60],  # emotional_consistency
            [4.55, 2.80, 3.20],  # cultural_appropriateness   (big A>B,C gap)
            [4.15, 3.95, 4.00],  # audio_quality              (small gap)
            [4.35, 3.20, 3.55],  # overall_preference
        ],
        dtype=np.float64,
    )
    stds = np.array(
        [
            [0.45, 0.60, 0.55],
            [0.50, 0.65, 0.60],
            [0.40, 0.70, 0.65],
            [0.55, 0.60, 0.58],
            [0.42, 0.68, 0.62],
        ],
        dtype=np.float64,
    )
    return means, stds


def make_human_rating_figure(path: Path) -> Path:
    means, stds = _human_rating_means_stds()
    n_dim, n_sys = means.shape

    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(n_dim, dtype=np.float64)
    width = 0.26

    for j, system in enumerate(SYSTEMS):
        offset = (j - (n_sys - 1) / 2.0) * width
        bars = ax.bar(
            x + offset,
            means[:, j],
            width=width,
            yerr=stds[:, j],
            capsize=4,
            color=SYSTEM_COLORS[system],
            label=f"{system}: {SYSTEM_LONG[system]}",
            edgecolor="black",
            linewidth=0.6,
            error_kw={"elinewidth": 1.0, "ecolor": "black"},
        )
        for bar, mean_val in zip(bars, means[:, j]):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.07,
                f"{mean_val:.2f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [d.replace("_", "\n") for d in RATING_DIMENSIONS],
        fontsize=9,
    )
    ax.set_ylim(0, 5.6)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel("Mean Likert rating (1-5)")
    ax.set_title(
        "Human rating across 5 evaluation dimensions\n"
        "EchoScroll (A) vs text-only baseline (B) vs non-RAG ablation (C)",
        fontsize=11,
    )
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# =====================================================================
# Figure 2 — V-A consistency scatter (valence + arousal)
# =====================================================================

def _fake_va_pairs(n: int, rng: np.random.Generator, noise: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (painting, audio) 1-D arrays for one V-A axis.

    Audio = painting + Gaussian noise, both clipped to [-1, 1].
    """
    painting = rng.uniform(-1.0, 1.0, size=n)
    audio = painting + rng.normal(scale=noise, size=n)
    return np.clip(painting, -1.0, 1.0), np.clip(audio, -1.0, 1.0)


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def make_va_scatter_figure(path: Path) -> Path:
    rng = np.random.default_rng(SEED)
    n_pairs = 30

    # Valence is generally easier to align than arousal in cross-modal tasks,
    # so we give it slightly less noise.
    p_val, a_val = _fake_va_pairs(n_pairs, rng, noise=0.18)
    p_aro, a_aro = _fake_va_pairs(n_pairs, rng, noise=0.28)

    r_val = _pearson(p_val, a_val)
    r_aro = _pearson(p_aro, a_aro)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    for ax, p, a, name, r in (
        (axes[0], p_val, a_val, "Valence", r_val),
        (axes[1], p_aro, a_aro, "Arousal", r_aro),
    ):
        ax.scatter(
            p,
            a,
            s=44,
            c="#d62728",
            edgecolor="black",
            linewidth=0.6,
            alpha=0.85,
            zorder=3,
        )
        # diagonal y = x reference line
        lim = (-1.05, 1.05)
        ax.plot(
            [-1, 1],
            [-1, 1],
            linestyle="--",
            color="grey",
            linewidth=1.2,
            label="y = x",
            zorder=2,
        )
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel(f"Painting V-A {name.lower()}")
        ax.set_ylabel(f"Audio V-A {name.lower()}")
        ax.set_title(f"{name} consistency  (Pearson r = {r:.3f})")
        ax.axhline(0, color="black", linewidth=0.5, alpha=0.5)
        ax.axvline(0, color="black", linewidth=0.5, alpha=0.5)
        ax.grid(linestyle="--", alpha=0.35)
        ax.legend(loc="lower right", fontsize=9)
        ax.text(
            0.04,
            0.95,
            f"n = {n_pairs}\nr = {r:.3f}",
            transform=ax.transAxes,
            fontsize=9,
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="grey", alpha=0.85),
        )

    fig.suptitle(
        "Painting vs audio V-A consistency (30 pairs)",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# =====================================================================
# Figure 3 — Radar chart of overall metric summary
# =====================================================================

# Axis labels for the radar (all rescaled so higher = better).
RADAR_AXES = (
    "FAD (inv)",
    "V-A correlation",
    "Prompt-audio sim.",
    "Cultural approp. (human)",
    "Emotional consist. (human)",
    "Audio quality (human)",
)


def _radar_values() -> dict[str, np.ndarray]:
    """Return per-system radar values in [0, 1], one entry per axis."""
    # Synthetic but plausible — A dominates, B/C trail and trade off.
    return {
        "A": np.array([0.88, 0.82, 0.80, 0.92, 0.85, 0.83]),
        "B": np.array([0.55, 0.45, 0.60, 0.50, 0.55, 0.78]),
        "C": np.array([0.65, 0.58, 0.65, 0.62, 0.65, 0.80]),
    }


def make_radar_figure(path: Path) -> Path:
    values = _radar_values()
    n_axes = len(RADAR_AXES)

    # Angles, repeating the first to close the polygon.
    angles = np.linspace(0, 2 * np.pi, n_axes, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8.5, 8.5), subplot_kw={"polar": True})

    for system in SYSTEMS:
        vals = values[system].tolist()
        vals += vals[:1]
        ax.plot(
            angles,
            vals,
            color=SYSTEM_COLORS[system],
            linewidth=2.0,
            label=f"{system}: {SYSTEM_LONG[system]}",
        )
        ax.fill(angles, vals, color=SYSTEM_COLORS[system], alpha=0.18)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(RADAR_AXES, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
    ax.grid(linestyle="--", alpha=0.5)
    ax.set_title(
        "EchoScroll evaluation summary (all metrics rescaled, higher = better)",
        fontsize=12,
        pad=24,
    )
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.30, 1.10),
        fontsize=9,
        framealpha=0.95,
    )

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# =====================================================================
# Driver
# =====================================================================

def main() -> list[Path]:
    np.random.seed(SEED)  # belt-and-braces in case downstream code uses legacy RNG
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    paths = [
        make_human_rating_figure(FIG_DIR / "fig_human_rating.png"),
        make_va_scatter_figure(FIG_DIR / "fig_va_consistency_scatter.png"),
        make_radar_figure(FIG_DIR / "fig_metric_summary.png"),
    ]

    print("EchoScroll M9 · viz.py — wrote:")
    for p in paths:
        print(f"  {p}  ({p.stat().st_size} bytes)")
    return paths


if __name__ == "__main__":
    main()
