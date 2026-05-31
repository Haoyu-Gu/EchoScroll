"""Visualisations for M7 Humming Interaction.

Produces three PNGs into ``figures/``:

1. fig_pitch_contour.png       — waveform + F0 contour of the synthesised hum
2. fig_pitch_class_histogram.png — PC histogram vs rotated KS profiles
3. fig_dtw_alignment.png       — DTW cost matrix + chroma alignment view

Run as ``python viz.py`` from inside ``M7_humming_interaction/``.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import librosa
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from demo import SR, synth_hum_a_major, synth_target_c_major
from humming import (
    KS_MAJOR_PROFILE,
    KS_MINOR_PROFILE,
    PENTATONIC_GONG_PROFILE,
    PITCH_CLASS_NAMES,
    HummingProcessor,
    _pitch_class_histogram,
    estimate_key,
)


FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_fig_dir() -> None:
    os.makedirs(FIG_DIR, exist_ok=True)


def _save(fig: plt.Figure, name: str) -> str:
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Fig 1: waveform + F0 contour
# ---------------------------------------------------------------------------


def make_pitch_contour_figure(
    hum: np.ndarray, sr: int, processor: HummingProcessor
) -> str:
    f0, _midi = processor.extract_pitch(hum, sr=sr)

    # Time axes
    t_wave = np.arange(hum.shape[0]) / float(sr)
    hop = processor.hop_length
    t_f0 = np.arange(f0.shape[0]) * hop / float(sr)

    fig, (ax_w, ax_p) = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True,
        gridspec_kw={"height_ratios": [1.0, 1.4]},
    )

    # Top: waveform
    ax_w.plot(t_wave, hum, color="#1f77b4", linewidth=0.6)
    ax_w.set_ylabel("amplitude")
    ax_w.set_title("Synthesised A-major hum  —  waveform (top) & F0 contour (bottom)")
    ax_w.grid(alpha=0.3)
    ax_w.set_xlim(t_wave[0], t_wave[-1])

    # Bottom: F0 contour
    voiced = np.isfinite(f0) & (f0 > 0)
    ax_p.plot(
        t_f0[voiced], f0[voiced],
        color="#f6c700", linewidth=2.2, label="extracted F0 (pYIN)",
    )

    # Reference pitch grid: A2 .. A5
    grid_notes = ["A2", "A3", "A4", "A5"]
    for n in grid_notes:
        hz = float(librosa.note_to_hz(n))
        ax_p.axhline(hz, color="gray", linestyle="--", alpha=0.5, linewidth=1.0)
        ax_p.text(
            t_f0[-1] * 1.005, hz, n,
            va="center", ha="left", fontsize=9, color="gray",
        )

    # Annotate the three peaks: A4 / C#5 / E5 — find frames near each freq
    targets = [("A4", 440.0), ("C#5", 554.37), ("E5", 659.26)]
    if voiced.any():
        for name, hz in targets:
            # find the voiced frame closest to this hz (in log-space)
            voiced_f = f0[voiced]
            voiced_t = t_f0[voiced]
            log_diff = np.abs(np.log2(voiced_f / hz))
            j = int(np.argmin(log_diff))
            # only annotate if reasonably close (< 1 semitone)
            if log_diff[j] < (1.0 / 12.0):
                ax_p.annotate(
                    name,
                    xy=(voiced_t[j], voiced_f[j]),
                    xytext=(voiced_t[j], voiced_f[j] * 1.18),
                    ha="center", fontsize=9, color="#b8860b",
                    arrowprops=dict(arrowstyle="-", color="#b8860b", lw=0.8),
                )

    ax_p.set_yscale("log")
    # y-limits: roughly A2 to A5 with padding
    ax_p.set_ylim(80.0, 1200.0)
    ax_p.set_xlabel("time (s)")
    ax_p.set_ylabel("F0 (Hz, log scale)")
    ax_p.grid(alpha=0.3, which="both")
    ax_p.legend(loc="upper right")

    return _save(fig, "fig_pitch_contour.png")


# ---------------------------------------------------------------------------
# Fig 2: pitch-class histogram + rotated KS profiles
# ---------------------------------------------------------------------------


def make_pitch_class_histogram_figure(
    hum: np.ndarray, sr: int, processor: HummingProcessor
) -> str:
    _f0, midi = processor.extract_pitch(hum, sr=sr)
    hist = _pitch_class_histogram(midi)
    tonal_center, mode, conf, _ = estimate_key(midi)
    root = PITCH_CLASS_NAMES.index(tonal_center)

    profiles = {
        "major": KS_MAJOR_PROFILE,
        "minor": KS_MINOR_PROFILE,
        "pentatonic_gong": PENTATONIC_GONG_PROFILE,
    }

    fig, ax = plt.subplots(figsize=(10, 5.5))

    x = np.arange(12)
    ax.bar(
        x, hist,
        color="#4c72b0", alpha=0.75, edgecolor="black", linewidth=0.6,
        label="hum PC histogram",
    )

    # Overlay rotated profiles, normalised to sum=1 for comparability with hist.
    colors = {
        "major": "#d62728",
        "minor": "#2ca02c",
        "pentatonic_gong": "#9467bd",
    }
    styles = {
        "major": "-",
        "minor": "--",
        "pentatonic_gong": ":",
    }
    for name, prof in profiles.items():
        rotated = np.roll(prof, root).astype(np.float32)
        rotated = rotated / rotated.sum()
        marker = "o" if name == mode else "."
        lw = 2.2 if name == mode else 1.3
        ax.plot(
            x, rotated,
            color=colors[name], linestyle=styles[name], linewidth=lw,
            marker=marker, markersize=6,
            label=f"KS {name} (root={tonal_center})"
                  + ("  [detected]" if name == mode else ""),
        )

    ax.set_xticks(x)
    ax.set_xticklabels(PITCH_CLASS_NAMES)
    ax.set_xlabel("pitch class")
    ax.set_ylabel("normalised weight")
    ax.set_title(
        f"Pitch-class histogram vs rotated KS profiles  —  "
        f"detected: {tonal_center} {mode}  (r = {conf:.3f})"
    )
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)

    # Highlight the root pitch class
    ax.add_patch(
        Rectangle(
            (root - 0.5, 0), 1.0, ax.get_ylim()[1],
            color="yellow", alpha=0.15, zorder=0,
        )
    )

    return _save(fig, "fig_pitch_class_histogram.png")


# ---------------------------------------------------------------------------
# Fig 3: DTW cost matrix + chroma alignment
# ---------------------------------------------------------------------------


def make_dtw_alignment_figure(
    hum: np.ndarray, target: np.ndarray, sr: int, processor: HummingProcessor
) -> str:
    hop = processor.hop_length
    chroma_hum = librosa.feature.chroma_cqt(y=hum, sr=sr, hop_length=hop).astype(
        np.float32
    )
    chroma_tgt = librosa.feature.chroma_cqt(
        y=target, sr=sr, hop_length=hop
    ).astype(np.float32)

    D, wp = librosa.sequence.dtw(X=chroma_hum, Y=chroma_tgt, metric="cosine")
    # wp is end->start, columns (X_idx, Y_idx) i.e. (hum, tgt)
    path = np.asarray(wp[::-1], dtype=np.int64)

    # Also get the transpose_cents using the module's own method, for the title.
    _path2, transpose_cents = processor.align_dtw(hum, target, sr=sr)

    fig = plt.figure(figsize=(13, 6.5))
    gs = fig.add_gridspec(
        2, 2,
        width_ratios=[1.1, 1.4], height_ratios=[1.0, 1.0],
        hspace=0.35, wspace=0.25,
    )

    # ----- Left: DTW cost matrix + path -----
    ax_d = fig.add_subplot(gs[:, 0])
    im = ax_d.imshow(
        D, origin="lower", aspect="auto", cmap="magma",
    )
    ax_d.plot(
        path[:, 1], path[:, 0],
        color="#00ffd0", linewidth=2.0, label="DTW path",
    )
    ax_d.set_xlabel("target frame")
    ax_d.set_ylabel("hum frame")
    ax_d.set_title("DTW accumulated cost matrix")
    ax_d.legend(loc="lower right", fontsize=9)
    fig.colorbar(im, ax=ax_d, fraction=0.046, pad=0.04, label="cost")

    # ----- Right top: chroma of hum -----
    ax_h = fig.add_subplot(gs[0, 1])
    librosa.display.specshow(
        chroma_hum, x_axis="time", y_axis="chroma",
        sr=sr, hop_length=hop, ax=ax_h, cmap="viridis",
    )
    ax_h.set_title("chroma — hum (A-major arpeggio)")

    # ----- Right bottom: chroma of target -----
    ax_t = fig.add_subplot(gs[1, 1])
    librosa.display.specshow(
        chroma_tgt, x_axis="time", y_axis="chroma",
        sr=sr, hop_length=hop, ax=ax_t, cmap="viridis",
    )
    ax_t.set_title("chroma — target (C-major melody)")

    fig.suptitle(
        f"DTW alignment hum <-> target   "
        f"transpose_cents = {transpose_cents:+.1f}  (target -> hum)",
        fontsize=13,
    )

    return _save(fig, "fig_dtw_alignment.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    _ensure_fig_dir()
    proc = HummingProcessor()

    hum = synth_hum_a_major()
    target = synth_target_c_major()

    p1 = make_pitch_contour_figure(hum, SR, proc)
    print(f"[viz] wrote {p1}")

    p2 = make_pitch_class_histogram_figure(hum, SR, proc)
    print(f"[viz] wrote {p2}")

    p3 = make_dtw_alignment_figure(hum, target, SR, proc)
    print(f"[viz] wrote {p3}")

    # Sanity check
    for p in (p1, p2, p3):
        assert os.path.isfile(p), f"missing output: {p}"
    print("[viz] OK — 3 PNGs written")


if __name__ == "__main__":
    main()
