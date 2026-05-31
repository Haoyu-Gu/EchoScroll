"""M7 — Humming Interaction.

Self-contained DSP module. Given a short (2-5 s) hum of a melody, extract:
  * frame-level pitch contour (Hz + rounded MIDI),
  * tonal centre + mode via Krumhansl-Schmuckler key-profile correlation,
  * (optionally) DTW alignment against a target soundtrack and the average
    transposition offset (in cents) needed to align target -> hum.

Pure NumPy / SciPy / librosa. CPU only. No torch.
"""

from __future__ import annotations

from typing import Optional

import librosa
import numpy as np
from scipy.stats import pearsonr


# ---------------------------------------------------------------------------
# Key profiles (Krumhansl-Schmuckler + a "pentatonic gong" profile that
# concentrates weight on the 5 notes of the Chinese pentatonic scale built
# on the gong/do degree: scale degrees 0, 2, 4, 7, 9).
# ---------------------------------------------------------------------------

KS_MAJOR_PROFILE: np.ndarray = np.asarray(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    dtype=np.float32,
)

KS_MINOR_PROFILE: np.ndarray = np.asarray(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
    dtype=np.float32,
)

# Pentatonic-gong (Chinese 宫调式 / major-pentatonic) profile.
# Five strong degrees, others near zero.  Weights chosen so the gong (root)
# and zhi (5th) dominate, with shang/jue/yu mid-weight.
PENTATONIC_GONG_PROFILE: np.ndarray = np.asarray(
    [6.0, 0.5, 3.5, 0.5, 3.0, 0.5, 0.5, 5.0, 0.5, 3.0, 0.5, 0.5],
    dtype=np.float32,
)

PITCH_CLASS_NAMES: list[str] = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hz_to_midi_safe(hz: np.ndarray) -> np.ndarray:
    """Convert Hz -> MIDI; unvoiced (NaN / non-positive) becomes -1."""
    out = np.full(hz.shape, -1, dtype=np.int32)
    voiced = np.isfinite(hz) & (hz > 0.0)
    if voiced.any():
        midi = 69.0 + 12.0 * np.log2(hz[voiced] / 440.0)
        out[voiced] = np.rint(midi).astype(np.int32)
    return out


def _pitch_class_histogram(midi_contour: np.ndarray) -> np.ndarray:
    """12-bin pitch-class histogram from voiced MIDI frames."""
    hist = np.zeros(12, dtype=np.float32)
    voiced = midi_contour[midi_contour >= 0]
    if voiced.size == 0:
        return hist
    pcs = np.mod(voiced, 12)
    for pc in pcs:
        hist[int(pc)] += 1.0
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def _correlate_profile(hist: np.ndarray, profile: np.ndarray) -> tuple[int, float]:
    """Return (best_root_pc, best_pearson_r) for a rotated profile."""
    best_r = -np.inf
    best_root = 0
    for root in range(12):
        rotated = np.roll(profile, root)
        if hist.std() < 1e-8 or rotated.std() < 1e-8:
            r = 0.0
        else:
            r, _ = pearsonr(hist, rotated)
        if r > best_r:
            best_r = float(r)
            best_root = root
    return best_root, best_r


def _root_pc_from_chroma_path(
    chroma: np.ndarray, frame_idx: np.ndarray
) -> Optional[int]:
    """Estimate tonal-centre pitch class (0..11) from a chroma matrix
    restricted to the *unique* frames touched by the DTW alignment path.
    Uses the same KS profile correlation as `estimate_key`, but driven by
    chroma energy directly so it works for polyphonic targets without an
    explicit F0 contour.

    Deduplicating frames is essential: DTW can stretch a single source
    frame across many target frames, which would otherwise bias the
    histogram toward whichever note happened to be held longest in the
    alignment.

    Returns None if the chroma is essentially silent / constant.
    """
    if frame_idx.size == 0:
        return None
    unique_idx = np.unique(frame_idx)
    aligned = chroma[:, unique_idx]
    hist = aligned.sum(axis=1).astype(np.float32)
    total = hist.sum()
    if total <= 1e-8:
        return None
    hist = hist / total
    best_r = -np.inf
    best_root: Optional[int] = None
    for profile in (KS_MAJOR_PROFILE, KS_MINOR_PROFILE):
        for root in range(12):
            rotated = np.roll(profile, root)
            if hist.std() < 1e-8 or rotated.std() < 1e-8:
                r = 0.0
            else:
                r, _ = pearsonr(hist, rotated)
            if r > best_r:
                best_r = float(r)
                best_root = root
    return best_root


def estimate_key(
    midi_contour: np.ndarray,
) -> tuple[str, str, float, np.ndarray]:
    """Krumhansl-Schmuckler-style key estimation over major / minor /
    pentatonic-gong profiles.

    Returns
    -------
    tonal_center : str   e.g. "A"
    mode         : str   one of {"major", "minor", "pentatonic", "unclear"}
    confidence   : float  best Pearson r in [-1, 1]
    histogram    : np.ndarray  12-bin pitch-class histogram (for inspection)
    """
    hist = _pitch_class_histogram(midi_contour)
    if hist.sum() <= 0.0:
        return "C", "unclear", 0.0, hist

    candidates: list[tuple[str, str, int, float]] = []
    for mode_name, profile in (
        ("major", KS_MAJOR_PROFILE),
        ("minor", KS_MINOR_PROFILE),
        ("pentatonic", PENTATONIC_GONG_PROFILE),
    ):
        root, r = _correlate_profile(hist, profile)
        candidates.append((mode_name, PITCH_CLASS_NAMES[root], root, r))

    candidates.sort(key=lambda x: x[3], reverse=True)
    best_mode, best_root_name, _, best_r = candidates[0]

    if best_r < 0.3:
        return best_root_name, "unclear", best_r, hist
    return best_root_name, best_mode, best_r, hist


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------


class HummingProcessor:
    """Extract pitch + key from a hum, optionally DTW-align to a target wav."""

    def __init__(
        self,
        fmin_hz: float = librosa.note_to_hz("C2"),
        fmax_hz: float = librosa.note_to_hz("C7"),
        frame_length: int = 2048,
        hop_length: int = 512,
    ) -> None:
        self.fmin_hz = float(fmin_hz)
        self.fmax_hz = float(fmax_hz)
        self.frame_length = int(frame_length)
        self.hop_length = int(hop_length)

    # ------------------------------------------------------------------
    # Pitch
    # ------------------------------------------------------------------
    def extract_pitch(
        self, wav: np.ndarray, sr: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Frame-level F0 via librosa.pyin. Returns (hz, midi)."""
        wav = np.asarray(wav, dtype=np.float32).flatten()
        f0, voiced_flag, _voiced_prob = librosa.pyin(
            wav,
            fmin=self.fmin_hz,
            fmax=self.fmax_hz,
            sr=sr,
            frame_length=self.frame_length,
            hop_length=self.hop_length,
        )
        f0 = np.asarray(f0, dtype=np.float32)
        # Unvoiced frames -> NaN (pyin already returns NaN there, but be safe)
        if voiced_flag is not None:
            f0 = np.where(voiced_flag, f0, np.nan).astype(np.float32)
        midi = _hz_to_midi_safe(f0)
        return f0, midi

    # ------------------------------------------------------------------
    # DTW + transposition
    # ------------------------------------------------------------------
    def align_dtw(
        self,
        hum_wav: np.ndarray,
        target_wav: np.ndarray,
        sr: int,
        hum_midi: Optional[np.ndarray] = None,
    ) -> tuple[np.ndarray, float]:
        """Chroma-based DTW alignment hum<->target, plus average transposition
        in cents that would move target -> hum.

        Transposition is computed as the signed semitone distance between
        the hum's tonal centre (estimated from its voiced MIDI contour via
        `estimate_key`) and the target's tonal centre (estimated by KS
        correlation on the chroma frames touched by the DTW path).

        Returns
        -------
        path : np.ndarray, shape (T, 2), columns = (hum_frame, target_frame)
        transpose_cents : float
        """
        hum_wav = np.asarray(hum_wav, dtype=np.float32).flatten()
        target_wav = np.asarray(target_wav, dtype=np.float32).flatten()

        chroma_hum = librosa.feature.chroma_cqt(
            y=hum_wav, sr=sr, hop_length=self.hop_length
        ).astype(np.float32)
        chroma_tgt = librosa.feature.chroma_cqt(
            y=target_wav, sr=sr, hop_length=self.hop_length
        ).astype(np.float32)

        _D, wp = librosa.sequence.dtw(
            X=chroma_hum, Y=chroma_tgt, metric="cosine"
        )
        # librosa returns the path from end -> start; flip so it reads
        # start -> end and rename columns.
        path = np.asarray(wp[::-1], dtype=np.int64)  # (T, 2): (hum, target)

        # Hum tonic from its voiced F0/MIDI is more robust than from chroma:
        # a short arpeggio confounds KS over chroma but is unambiguous in F0.
        if hum_midi is None:
            _, hum_midi = self.extract_pitch(hum_wav, sr=sr)
        hum_name, hum_mode, _, _ = estimate_key(hum_midi)
        if hum_mode == "unclear":
            hum_root_pc: Optional[int] = None
        else:
            hum_root_pc = PITCH_CLASS_NAMES.index(hum_name)

        tgt_root_pc = _root_pc_from_chroma_path(chroma_tgt, path[:, 1])

        if hum_root_pc is None or tgt_root_pc is None:
            transpose_cents = 0.0
        else:
            diff = (hum_root_pc - tgt_root_pc) % 12
            if diff > 6:
                diff -= 12
            transpose_cents = float(diff * 100.0)

        return path, transpose_cents

    # ------------------------------------------------------------------
    # Top-level
    # ------------------------------------------------------------------
    def process(
        self,
        hum_wav: np.ndarray,
        target_wav: Optional[np.ndarray] = None,
        sr: int = 22050,
    ) -> dict:
        """Run the full humming-interaction pipeline.

        Parameters
        ----------
        hum_wav    : mono waveform of the user's hum (float32 expected).
        target_wav : optional current generated soundtrack to align against.
        sr         : sample rate of both waveforms.

        Returns
        -------
        dict with keys:
          pitch_contour_hz, midi_contour,
          tonal_center, mode, key_confidence,
          dtw_alignment (optional), transpose_cents (optional).
        """
        hum_wav = np.asarray(hum_wav, dtype=np.float32).flatten()

        f0_hz, midi = self.extract_pitch(hum_wav, sr=sr)
        tonal_center, mode, key_conf, _hist = estimate_key(midi)

        result: dict = {
            "pitch_contour_hz": f0_hz.astype(np.float32),
            "midi_contour": midi.astype(np.int32),
            "tonal_center": tonal_center,
            "mode": mode,
            "key_confidence": float(key_conf),
        }

        if target_wav is not None:
            path, cents = self.align_dtw(
                hum_wav=hum_wav,
                target_wav=np.asarray(target_wav, dtype=np.float32).flatten(),
                sr=sr,
                hum_midi=midi,
            )
            result["dtw_alignment"] = path
            result["transpose_cents"] = float(cents)

        return result
