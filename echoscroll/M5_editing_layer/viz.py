"""Visualizations for M5 (editing layer).

Generates three PNG figures into ./figures/:

    1. fig_beat_detection.png  -- waveform + detected beats + onset envelope
    2. fig_bpm_stretch.png     -- original / x0.5 / x1.5 waveforms side by side
    3. fig_segment_replace.png -- before/after segment replacement

The 10-second synthetic test signal (A4 + E5 sines + 4 noise bursts) is
re-synthesised here via ``synth_test_signal()`` so this script has no I/O
dependency on the demo's output WAVs.

Run:  python viz.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import librosa

from editor import (
    detect_beats,
    change_bpm,
    replace_segment,
    segment as segment_fn,
)


SR = 32000
DURATION_S = 10.0


def synth_test_signal(sr: int = SR, duration_s: float = DURATION_S) -> np.ndarray:
    """A4 + E5 sines with slow AM, plus 4 short noise bursts as fake beats.

    Mirrors ``demo.synth_test_wav`` exactly so the figures match the demo run.
    """
    rng = np.random.default_rng(42)
    n = int(round(sr * duration_s))
    t = np.arange(n, dtype=np.float32) / sr

    a4 = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
    e5 = np.sin(2.0 * np.pi * 659.25 * t).astype(np.float32)

    env = 0.5 * (1.0 + 0.5 * np.sin(2.0 * np.pi * 2.0 * t)).astype(np.float32)
    tone = 0.4 * env * (a4 + 0.7 * e5)

    burst_times = [1.0, 3.5, 6.0, 8.5]
    burst_len = int(0.04 * sr)
    burst_env = np.linspace(1.0, 0.0, burst_len, dtype=np.float32) ** 2
    for bt in burst_times:
        start = int(bt * sr)
        end = min(start + burst_len, n)
        burst = rng.standard_normal(end - start).astype(np.float32) * 0.6
        tone[start:end] += burst * burst_env[: end - start]

    peak = float(np.max(np.abs(tone))) or 1.0
    return (tone / peak * 0.9).astype(np.float32)


# ---------------------------------------------------------------------------
# Figure 1: beat detection
# ---------------------------------------------------------------------------


def fig_beat_detection(wav: np.ndarray, sr: int, out_path: Path) -> None:
    beats = detect_beats(wav, sr)

    # Onset-strength envelope on the same hop grid librosa.beat uses.
    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=wav, sr=sr, hop_length=hop_length)
    onset_t = librosa.frames_to_time(
        np.arange(len(onset_env)), sr=sr, hop_length=hop_length
    )

    t_wav = np.arange(len(wav), dtype=np.float32) / sr

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)

    ax0.plot(t_wav, wav, color="#1f77b4", lw=0.6)
    for bt in beats:
        ax0.axvline(bt, color="red", ls="--", lw=1.0, alpha=0.8)
    ax0.set_ylabel("amplitude")
    ax0.set_title(
        f"Waveform with detected beats (n_beats={len(beats)})"
    )
    ax0.set_ylim(-1.0, 1.0)
    ax0.grid(alpha=0.3)

    ax1.plot(onset_t, onset_env, color="#2ca02c", lw=1.0,
             label="onset strength")
    for bt in beats:
        ax1.axvline(bt, color="red", ls="--", lw=1.0, alpha=0.8)
    ax1.set_xlabel("time (s)")
    ax1.set_ylabel("onset strength")
    ax1.set_title("Onset-strength envelope (librosa.onset.onset_strength)")
    ax1.set_xlim(0.0, len(wav) / sr)
    ax1.grid(alpha=0.3)
    ax1.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: BPM stretch
# ---------------------------------------------------------------------------


def fig_bpm_stretch(wav: np.ndarray, sr: int, out_path: Path) -> None:
    slow = change_bpm(wav, sr, src_bpm=120.0, tgt_bpm=60.0)
    fast = change_bpm(wav, sr, src_bpm=120.0, tgt_bpm=180.0)

    panels = [
        ("Original (x1.0)", wav),
        ("x0.5 BPM (slowed)", slow),
        ("x1.5 BPM (sped up)", fast),
    ]
    y_max = max(float(np.max(np.abs(p[1]))) for p in panels) * 1.05

    fig, axes = plt.subplots(1, 3, figsize=(15, 3.6), sharey=True)
    for ax, (label, w) in zip(axes, panels):
        t = np.arange(len(w), dtype=np.float32) / sr
        ax.plot(t, w, color="#1f77b4", lw=0.5)
        dur = len(w) / sr
        ax.set_title(f"{label}\nduration = {dur:.2f} s")
        ax.set_xlabel("time (s)")
        ax.set_xlim(0.0, dur)
        ax.set_ylim(-y_max, y_max)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("amplitude")

    fig.suptitle("BPM time-stretch via phase vocoder (pitch preserved)",
                 y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: segment replacement
# ---------------------------------------------------------------------------


def fig_segment_replace(wav: np.ndarray, sr: int, out_path: Path) -> None:
    beats = detect_beats(wav, sr)
    segments = segment_fn(wav, sr, beats)
    if len(beats) < 2 or len(segments) < 3:
        raise RuntimeError(
            "Not enough beats/segments to draw a replacement figure."
        )

    mid_idx = len(segments) // 2

    # Boundary times (in seconds) consistent with editor.segment().
    boundaries_samp = np.unique(
        np.clip(np.round(np.asarray(beats) * sr).astype(int), 0, len(wav))
    )
    if boundaries_samp[0] != 0:
        boundaries_samp = np.concatenate([[0], boundaries_samp])
    if boundaries_samp[-1] != len(wav):
        boundaries_samp = np.concatenate([boundaries_samp, [len(wav)]])
    a_samp, b_samp = int(boundaries_samp[mid_idx]), int(boundaries_samp[mid_idx + 1])
    a_t, b_t = a_samp / sr, b_samp / sr

    # White-noise replacement of identical length.
    target_len = len(segments[mid_idx])
    rng = np.random.default_rng(0)
    noise = (rng.standard_normal(target_len) * 0.3).astype(np.float32)

    spliced = replace_segment(
        wav, sr, beats, segment_idx=mid_idx,
        replacement_wav=noise, crossfade_ms=50.0,
    )

    # After splicing with crossfades, the replaced region in the *output*
    # spans roughly the same time window as in the input (segments before
    # mid_idx are kept verbatim except for the trailing xfade).
    new_a_t = a_t
    new_b_t = a_t + target_len / sr

    t_in = np.arange(len(wav), dtype=np.float32) / sr
    t_out = np.arange(len(spliced), dtype=np.float32) / sr

    y_max = max(float(np.max(np.abs(wav))),
                float(np.max(np.abs(spliced)))) * 1.05

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)

    ax0.plot(t_in, wav, color="#1f77b4", lw=0.5)
    ax0.axvspan(a_t, b_t, color="red", alpha=0.3,
                label=f"segment #{mid_idx} (to remove)")
    ax0.set_ylabel("amplitude")
    ax0.set_title("Original waveform — targeted segment shaded")
    ax0.set_ylim(-y_max, y_max)
    ax0.grid(alpha=0.3)
    ax0.legend(loc="upper right")

    ax1.plot(t_out, spliced, color="#1f77b4", lw=0.5)
    ax1.axvspan(new_a_t, new_b_t, color="green", alpha=0.3,
                label="inserted replacement (white noise)")
    ax1.set_xlabel("time (s)")
    ax1.set_ylabel("amplitude")
    ax1.set_title("Spliced waveform — new segment in green (50 ms crossfades)")
    ax1.set_ylim(-y_max, y_max)
    ax1.set_xlim(0.0, max(len(wav), len(spliced)) / sr)
    ax1.grid(alpha=0.3)
    ax1.legend(loc="upper right")

    # Inset arrow showing the swap: from the red box (top axes) to the green
    # box (bottom axes), drawn in figure coordinates.
    seg_center_t = 0.5 * (a_t + b_t)
    ax0.annotate(
        "",
        xy=(seg_center_t, -y_max * 0.9),
        xycoords=ax0.transData,
        xytext=(seg_center_t, y_max * 0.9),
        textcoords=ax1.transData,
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5,
                        connectionstyle="arc3,rad=0.0"),
    )
    ax0.text(
        seg_center_t, y_max * 0.6, "swap",
        ha="center", va="bottom", fontsize=10, color="black",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black",
                  alpha=0.85),
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    here = Path(__file__).resolve().parent
    fig_dir = here / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    wav = synth_test_signal()

    p1 = fig_dir / "fig_beat_detection.png"
    p2 = fig_dir / "fig_bpm_stretch.png"
    p3 = fig_dir / "fig_segment_replace.png"

    fig_beat_detection(wav, SR, p1)
    print(f"[viz] wrote {p1}")

    fig_bpm_stretch(wav, SR, p2)
    print(f"[viz] wrote {p2}")

    fig_segment_replace(wav, SR, p3)
    print(f"[viz] wrote {p3}")


if __name__ == "__main__":
    main()
