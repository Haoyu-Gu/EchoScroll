"""
EchoScroll M4 visualizations.

Generates three PNG figures into ``figures/`` that illustrate how the mock
music generator translates V--A coordinates into audio. All figures use the
:class:`MockMusicGenerator` (no MusicGen download required).

Run::

    python viz.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import librosa
import matplotlib.pyplot as plt
import numpy as np

from generator import MockMusicGenerator


FIGDIR = Path(__file__).parent / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

# Three sample V--A points used across all three figures.
SAMPLES = [
    {
        "va": (-0.7, -0.6),
        "label": "melancholic",
        "text_prompt": "melancholic literati landscape",
    },
    {
        "va": (0.0, 0.0),
        "label": "neutral",
        "text_prompt": "neutral",
    },
    {
        "va": (0.7, 0.7),
        "label": "joyful",
        "text_prompt": "joyful festival",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _va_to_pitch_hz(valence: float) -> float:
    """Replicate the mock generator's V -> base-frequency mapping.

    Matches the formula in :class:`MockMusicGenerator.generate`:
    ``196 * 2 ** ((v + 1) / 2 * log2(523/196))``.
    """
    v = float(np.clip(valence, -1.0, 1.0))
    return 196.0 * (2.0 ** ((v + 1.0) * 0.5 * math.log2(523.0 / 196.0)))


def _make_condition(sample: dict, duration_s: int = 8) -> dict:
    return {
        "text_prompt": sample["text_prompt"],
        "va": sample["va"],
        "retrieved_context": None,
        "duration_s": duration_s,
        "control_descriptors": None,
    }


def _generate(sample: dict, duration_s: int = 8) -> tuple[np.ndarray, int]:
    gen = MockMusicGenerator().load()
    out = gen.generate(_make_condition(sample, duration_s=duration_s))
    return np.asarray(out["wav"], dtype=np.float32), int(out["sample_rate"])


# ---------------------------------------------------------------------------
# Figure 1: time-domain waveforms (first 5 s)
# ---------------------------------------------------------------------------

def fig_waveforms_va(path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.6), sharey=True)

    for ax, sample in zip(axes, SAMPLES):
        wav, sr = _generate(sample, duration_s=8)
        n = min(len(wav), int(5 * sr))
        wav = wav[:n]
        t = np.arange(n, dtype=np.float32) / float(sr)
        ax.plot(t, wav, linewidth=0.5, color="#1f4e79")
        v, a = sample["va"]
        ax.set_title(f"V={v:+.1f}, A={a:+.1f}  ({sample['label']})")
        ax.set_xlabel("Time (s)")
        ax.set_xlim(0, 5)
        ax.set_ylim(-1.05, 1.05)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Amplitude")
    fig.suptitle("Mock music generator: time-domain waveforms (first 5 s)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 2: log-mel spectrograms
# ---------------------------------------------------------------------------

def fig_mel_spectrograms(path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.0))
    last_im = None

    for ax, sample in zip(axes, SAMPLES):
        wav, sr = _generate(sample, duration_s=8)
        mel = librosa.feature.melspectrogram(
            y=wav.astype(np.float32),
            sr=sr,
            n_mels=80,
            n_fft=2048,
            hop_length=512,
            power=2.0,
        )
        mel_db = librosa.power_to_db(mel, ref=np.max)

        last_im = librosa.display.specshow(
            mel_db,
            sr=sr,
            hop_length=512,
            x_axis="time",
            y_axis="mel",
            cmap="magma",
            ax=ax,
        )
        v, a = sample["va"]
        ax.set_title(f"V={v:+.1f}, A={a:+.1f}  ({sample['label']})")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Mel frequency (Hz)")

    cbar = fig.colorbar(last_im, ax=axes, format="%+2.0f dB", shrink=0.85)
    cbar.set_label("Power (dB)")
    fig.suptitle("Mock music generator: log-mel spectrograms (n_mels=80)")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 3: V--A -> pitch heatmap
# ---------------------------------------------------------------------------

def fig_va_to_pitch_map(path: Path) -> Path:
    grid_n = 20
    v_edges = np.linspace(-1.0, 1.0, grid_n + 1)
    a_edges = np.linspace(-1.0, 1.0, grid_n + 1)
    v_centers = 0.5 * (v_edges[:-1] + v_edges[1:])
    a_centers = 0.5 * (a_edges[:-1] + a_edges[1:])

    # pitch[i, j] indexed by (arousal_i, valence_j) so imshow with
    # origin='lower' puts +A at top, +V on the right.
    pitch = np.zeros((grid_n, grid_n), dtype=np.float32)
    for i, _a in enumerate(a_centers):
        for j, v in enumerate(v_centers):
            pitch[i, j] = _va_to_pitch_hz(v)

    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(
        pitch,
        origin="lower",
        extent=(-1.0, 1.0, -1.0, 1.0),
        aspect="equal",
        cmap="viridis",
    )

    # Contour lines for readability.
    V, A = np.meshgrid(v_centers, a_centers)
    cs = ax.contour(
        V, A, pitch,
        levels=8,
        colors="white",
        linewidths=0.6,
        alpha=0.7,
    )
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.0f Hz")

    # Overlay the three sample points.
    for sample in SAMPLES:
        v, a = sample["va"]
        ax.scatter([v], [a], s=110, c="red", edgecolors="white", linewidths=1.5, zorder=5)
        ax.annotate(
            f"{sample['label']}\n({v:+.1f}, {a:+.1f})",
            xy=(v, a),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=8,
            color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc="black", alpha=0.6, ec="none"),
        )

    ax.axhline(0.0, color="white", linewidth=0.5, alpha=0.4)
    ax.axvline(0.0, color="white", linewidth=0.5, alpha=0.4)
    ax.set_xlabel("Valence")
    ax.set_ylabel("Arousal")
    ax.set_title("Mock generator: V--A -> base pitch (Hz)")

    cbar = fig.colorbar(im, ax=ax, shrink=0.9)
    cbar.set_label("Base frequency (Hz)")

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    p1 = fig_waveforms_va(FIGDIR / "fig_waveforms_va.png")
    p2 = fig_mel_spectrograms(FIGDIR / "fig_mel_spectrograms.png")
    p3 = fig_va_to_pitch_map(FIGDIR / "fig_va_to_pitch_map.png")
    for p in (p1, p2, p3):
        print(f"[viz] wrote {p.resolve()}")


if __name__ == "__main__":
    main()
