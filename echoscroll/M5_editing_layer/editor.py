"""M5 Editing Layer for EchoScroll.

A pure-DSP, CPU-only editing layer that refines a MusicGen-produced soundtrack
through four small operations:

    1. beat detection / segmentation        (librosa.beat.beat_track)
    2. BPM adjustment via phase vocoder     (librosa.effects.time_stretch)
    3. segment replacement with cross-fade  (numpy splice + linear fade)
    4. style-transfer prompt rewrite        (string helper for M4 to re-generate)

No neural networks, no torch, no cross-imports from other M* modules.
All audio is float32 mono at ~32 kHz (MusicGen native rate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import librosa
import numpy as np

# ---------------------------------------------------------------------------
# Module-level functions (the interface other modules / scripts can call)
# ---------------------------------------------------------------------------


def detect_beats(wav: np.ndarray, sr: int) -> np.ndarray:
    """Estimate beat times (seconds) using librosa's beat tracker.

    Args:
        wav: mono float32 waveform, shape (T,).
        sr:  sample rate (Hz), typically 32000 for MusicGen.

    Returns:
        np.ndarray of beat times in seconds, shape (B,). May be empty if the
        tracker fails to find onsets (e.g. pure tone with no transients).
    """
    wav = _as_mono_float32(wav)
    # `units="time"` returns beat positions directly in seconds.
    tempo, beat_times = librosa.beat.beat_track(y=wav, sr=sr, units="time")
    return np.asarray(beat_times, dtype=np.float32)


def segment(
    wav: np.ndarray, sr: int, beat_times: np.ndarray
) -> list[np.ndarray]:
    """Slice the waveform at beat boundaries.

    Beat boundaries are converted to sample indices. The waveform is sliced
    into ``len(beat_times) + 1`` segments: [0, b0), [b0, b1), ..., [b_{n-1}, T).
    Empty segments are skipped.
    """
    wav = _as_mono_float32(wav)
    if beat_times is None or len(beat_times) == 0:
        return [wav.copy()]

    boundaries = np.unique(
        np.clip(np.round(np.asarray(beat_times) * sr).astype(int), 0, len(wav))
    )
    # Always include 0 and T so we cover the whole signal.
    if boundaries[0] != 0:
        boundaries = np.concatenate([[0], boundaries])
    if boundaries[-1] != len(wav):
        boundaries = np.concatenate([boundaries, [len(wav)]])

    segs: list[np.ndarray] = []
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        if b > a:
            segs.append(wav[a:b].copy())
    return segs


def change_bpm(
    wav: np.ndarray, sr: int, src_bpm: float, tgt_bpm: float
) -> np.ndarray:
    """Time-stretch the waveform from ``src_bpm`` to ``tgt_bpm`` without
    changing pitch.

    Implementation note (phase vocoder):
        librosa.effects.time_stretch applies an STFT-domain phase vocoder.
        For each STFT frame m and bin k the unwrapped phase advances as

            phi'[m, k] = phi'[m-1, k] + alpha * (phi[m, k] - phi[m-1, k])

        where alpha is the stretch factor (= src_bpm / tgt_bpm).  Magnitudes
        are interpolated between adjacent input frames; phases are accumulated
        so the instantaneous frequency of each bin is preserved.  Because the
        STFT bin structure is unchanged, pitch is preserved while duration is
        rescaled by 1/alpha.

    Args:
        wav: mono float32 waveform.
        sr:  sample rate (unused by librosa internally for time_stretch but
             accepted here for API symmetry).
        src_bpm: source tempo.
        tgt_bpm: target tempo.

    Returns:
        Stretched waveform (float32).  Length is roughly ``len(wav) * src/tgt``.
    """
    if src_bpm <= 0 or tgt_bpm <= 0:
        raise ValueError(f"BPMs must be positive, got src={src_bpm}, tgt={tgt_bpm}")

    wav = _as_mono_float32(wav)
    rate = float(tgt_bpm) / float(src_bpm)  # speed multiplier
    # librosa convention: rate > 1 => faster (shorter); rate < 1 => slower.
    if abs(rate - 1.0) < 1e-6:
        return wav.copy()

    out = librosa.effects.time_stretch(y=wav, rate=rate)
    return out.astype(np.float32, copy=False)


def replace_segment(
    wav: np.ndarray,
    sr: int,
    beat_times: np.ndarray,
    segment_idx: int,
    replacement_wav: np.ndarray,
    crossfade_ms: float = 50.0,
) -> np.ndarray:
    """Replace one beat-bounded segment with ``replacement_wav``, crossfading
    50 ms (default) at both boundaries.

    Segments are indexed exactly like the output of :func:`segment`:
    segment 0 = [0, beat_times[0]); segment i = [beat_times[i-1], beat_times[i])
    for 1 <= i < len(beat_times); the last segment = [beat_times[-1], T).

    Args:
        wav: original mono float32 waveform.
        sr:  sample rate.
        beat_times: beat times in seconds (from :func:`detect_beats`).
        segment_idx: which segment to drop and replace.
        replacement_wav: replacement clip (mono float32).
        crossfade_ms: crossfade length at each splice point.

    Returns:
        Spliced waveform (float32).  Length ~= len(wav) - seg_len + repl_len.
    """
    wav = _as_mono_float32(wav)
    replacement_wav = _as_mono_float32(replacement_wav)

    if beat_times is None or len(beat_times) == 0:
        raise ValueError("beat_times is empty; cannot identify segments.")

    # Build boundary array consistent with `segment()`.
    boundaries = np.unique(
        np.clip(np.round(np.asarray(beat_times) * sr).astype(int), 0, len(wav))
    )
    if boundaries[0] != 0:
        boundaries = np.concatenate([[0], boundaries])
    if boundaries[-1] != len(wav):
        boundaries = np.concatenate([boundaries, [len(wav)]])

    n_segments = len(boundaries) - 1
    if not 0 <= segment_idx < n_segments:
        raise IndexError(
            f"segment_idx={segment_idx} out of range [0, {n_segments})."
        )

    a, b = int(boundaries[segment_idx]), int(boundaries[segment_idx + 1])
    left = wav[:a]
    right = wav[b:]

    xfade = max(1, int(round(crossfade_ms * 1e-3 * sr)))
    # Don't crossfade longer than the available context on either side.
    xfade = min(xfade, len(left), len(right), len(replacement_wav) // 2 or 1)

    out = _splice_with_crossfade(left, replacement_wav, right, xfade)
    return out.astype(np.float32, copy=False)


def style_transfer_prompt(current_prompt: str, target_style: str) -> str:
    """Rewrite a MusicGen text prompt so its style/adjective slot is swapped.

    Heuristic: if the current prompt already contains a recognised style
    keyword, replace the *first* occurrence with ``target_style``.  Otherwise
    prepend ``"<target_style> style, "``.  The actual re-generation is left
    to M4; this helper only edits the text condition.

    Args:
        current_prompt: previous MusicGen prompt.
        target_style: new style adjective (e.g. ``"guqin"``, ``"orchestral"``,
                      ``"melancholic"``).

    Returns:
        Rewritten prompt string.
    """
    if not isinstance(current_prompt, str):
        current_prompt = "" if current_prompt is None else str(current_prompt)
    target_style = target_style.strip()
    if not target_style:
        return current_prompt

    # A small, intentionally non-exhaustive style/adjective vocabulary.  Order
    # matters: longer / more specific terms come first so we don't partial-match.
    style_vocab = [
        "guqin", "guzheng", "erhu", "xiao", "pipa", "dizi",
        "orchestral", "cinematic", "ambient", "lo-fi", "electronic",
        "jazz", "blues", "rock", "folk", "classical", "minimalist",
        "melancholic", "joyful", "serene", "tense", "solemn", "bright",
        "calm", "energetic", "dreamy", "epic",
    ]

    lower = current_prompt.lower()
    for kw in style_vocab:
        idx = lower.find(kw)
        if idx != -1:
            # Preserve original casing of surroundings; replace just this slice.
            return current_prompt[:idx] + target_style + current_prompt[idx + len(kw):]

    # No known style token found; prepend.
    sep = ", " if current_prompt else ""
    return f"{target_style} style{sep}{current_prompt}"


# ---------------------------------------------------------------------------
# Class wrapper (one method per op)
# ---------------------------------------------------------------------------


@dataclass
class EditLogEntry:
    op: str
    params: dict[str, Any] = field(default_factory=dict)


class EditingLayer:
    """One-stop editing facade.  Each method just forwards to the corresponding
    module-level function and appends to ``self.log`` so the front-end / M8
    can show an editing history."""

    def __init__(self, sr: int = 32000) -> None:
        self.sr = int(sr)
        self.log: list[EditLogEntry] = []

    # --- op 1 ---------------------------------------------------------------
    def detect_beats(self, wav: np.ndarray) -> np.ndarray:
        beats = detect_beats(wav, self.sr)
        self.log.append(EditLogEntry("detect_beats", {"n_beats": int(len(beats))}))
        return beats

    # (kept for convenience; not in the spec but cheap and useful for demos)
    def segment(self, wav: np.ndarray, beat_times: np.ndarray) -> list[np.ndarray]:
        segs = segment(wav, self.sr, beat_times)
        self.log.append(EditLogEntry("segment", {"n_segments": len(segs)}))
        return segs

    # --- op 2 ---------------------------------------------------------------
    def change_bpm(
        self, wav: np.ndarray, src_bpm: float, tgt_bpm: float
    ) -> np.ndarray:
        out = change_bpm(wav, self.sr, src_bpm, tgt_bpm)
        self.log.append(
            EditLogEntry(
                "change_bpm",
                {"src_bpm": float(src_bpm), "tgt_bpm": float(tgt_bpm),
                 "in_len": int(len(wav)), "out_len": int(len(out))},
            )
        )
        return out

    # --- op 3 ---------------------------------------------------------------
    def replace_segment(
        self,
        wav: np.ndarray,
        beat_times: np.ndarray,
        segment_idx: int,
        replacement_wav: np.ndarray,
        crossfade_ms: float = 50.0,
    ) -> np.ndarray:
        out = replace_segment(
            wav, self.sr, beat_times, segment_idx, replacement_wav, crossfade_ms
        )
        self.log.append(
            EditLogEntry(
                "replace_segment",
                {"segment_idx": int(segment_idx),
                 "crossfade_ms": float(crossfade_ms),
                 "replacement_len": int(len(replacement_wav)),
                 "in_len": int(len(wav)),
                 "out_len": int(len(out))},
            )
        )
        return out

    # --- op 4 ---------------------------------------------------------------
    def style_transfer_prompt(self, current_prompt: str, target_style: str) -> str:
        new_prompt = style_transfer_prompt(current_prompt, target_style)
        self.log.append(
            EditLogEntry(
                "style_transfer_prompt",
                {"target_style": target_style,
                 "old_prompt": current_prompt,
                 "new_prompt": new_prompt},
            )
        )
        return new_prompt


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _as_mono_float32(wav: np.ndarray) -> np.ndarray:
    """Coerce to a contiguous mono float32 array."""
    arr = np.asarray(wav)
    if arr.ndim == 2:
        # (channels, samples) or (samples, channels) — collapse either way.
        if arr.shape[0] < arr.shape[1]:
            arr = arr.mean(axis=0)
        else:
            arr = arr.mean(axis=1)
    elif arr.ndim != 1:
        raise ValueError(f"Expected 1-D or 2-D waveform, got shape {arr.shape}.")
    return np.ascontiguousarray(arr, dtype=np.float32)


def _splice_with_crossfade(
    left: np.ndarray,
    middle: np.ndarray,
    right: np.ndarray,
    xfade: int,
) -> np.ndarray:
    """Concatenate ``left + middle + right`` with linear equal-power-ish
    cross-fades of length ``xfade`` samples at both joins.

    The fade uses a sin/cos pair so left^2 + right^2 = 1, which keeps
    perceived loudness roughly constant across the splice.
    """
    if xfade <= 0:
        return np.concatenate([left, middle, right]).astype(np.float32, copy=False)

    t = np.linspace(0.0, 0.5 * np.pi, xfade, dtype=np.float32)
    fade_out = np.cos(t)
    fade_in = np.sin(t)

    # Join 1: end of left, start of middle.
    if len(left) >= xfade and len(middle) >= xfade:
        head = left[:-xfade]
        join1 = left[-xfade:] * fade_out + middle[:xfade] * fade_in
        mid_body = middle[xfade:]
    else:
        head = left[: max(0, len(left) - xfade)]
        join1 = np.array([], dtype=np.float32)
        mid_body = middle

    # Join 2: end of middle (possibly already trimmed), start of right.
    if len(mid_body) >= xfade and len(right) >= xfade:
        mid_keep = mid_body[:-xfade]
        join2 = mid_body[-xfade:] * fade_out + right[:xfade] * fade_in
        tail = right[xfade:]
    else:
        mid_keep = mid_body
        join2 = np.array([], dtype=np.float32)
        tail = right

    return np.concatenate([head, join1, mid_keep, join2, tail]).astype(
        np.float32, copy=False
    )
