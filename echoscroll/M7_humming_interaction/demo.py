"""Demo for M7 Humming Interaction.

Synthesises a 3-second hum (A-major triad arpeggio: A4 / C#5 / E5 played as
six short notes), runs pitch extraction + key estimation, prints the stats
and asserts that the detected key is "A" / "major".

Then synthesises a 5-second pseudo-soundtrack rooted in C-major and runs
DTW alignment + cents-offset estimation against the hum.
"""

from __future__ import annotations

import numpy as np

from humming import HummingProcessor


SR = 22050


def _synth_note(freq: float, duration_s: float, sr: int = SR) -> np.ndarray:
    """Synthesise a soft hum-like tone with vibrato + harmonics + attack/decay."""
    t = np.linspace(0.0, duration_s, int(sr * duration_s), endpoint=False)
    vibrato = 1.0 + 0.005 * np.sin(2.0 * np.pi * 5.0 * t)
    phase = 2.0 * np.pi * freq * t * vibrato
    wave = (
        1.0 * np.sin(phase)
        + 0.35 * np.sin(2.0 * phase)
        + 0.15 * np.sin(3.0 * phase)
    )
    # Soft attack/decay envelope so pyin sees clean voiced regions.
    env = np.ones_like(t)
    edge = max(1, int(0.02 * sr))
    env[:edge] = np.linspace(0.0, 1.0, edge)
    env[-edge:] = np.linspace(1.0, 0.0, edge)
    return (wave * env * 0.3).astype(np.float32)


def synth_hum_a_major() -> np.ndarray:
    """6 notes ~0.5 s each = 3 s.  A-major triad arpeggio: A C# E A E C#.

    Pitches: A4 = 440 Hz family.  We use the proposal's example values
    (220, 277, 330) — i.e. A3 / C#4 / E4 — repeated to make six notes.
    """
    pitches_hz = [220.0, 277.18, 329.63, 440.0, 329.63, 277.18]
    notes = [_synth_note(f, 0.5) for f in pitches_hz]
    return np.concatenate(notes).astype(np.float32)


def synth_target_c_major() -> np.ndarray:
    """5-second pseudo-melody in C-major: C E G C E G C E."""
    pitches_hz = [
        261.63,  # C4
        329.63,  # E4
        392.00,  # G4
        523.25,  # C5
        392.00,  # G4
        329.63,  # E4
        261.63,  # C4
        329.63,  # E4
    ]
    notes = [_synth_note(f, 0.625) for f in pitches_hz]  # 8 * 0.625 = 5.0 s
    return np.concatenate(notes).astype(np.float32)


def main() -> None:
    proc = HummingProcessor()

    # ------------------------------------------------------------------
    # 1) Hum only -> pitch contour + key estimation.
    # ------------------------------------------------------------------
    hum = synth_hum_a_major()
    print(f"[hum]    {hum.shape[0] / SR:.2f}s @ {SR} Hz")

    out = proc.process(hum, sr=SR)
    f0 = out["pitch_contour_hz"]
    midi = out["midi_contour"]
    voiced_f0 = f0[np.isfinite(f0) & (f0 > 0)]

    print("--- pitch contour stats ---")
    print(f"  total frames         : {f0.shape[0]}")
    print(f"  voiced frames        : {int(voiced_f0.size)}")
    if voiced_f0.size > 0:
        print(
            f"  f0 Hz median / range : "
            f"{np.median(voiced_f0):.2f}  "
            f"[{voiced_f0.min():.2f}, {voiced_f0.max():.2f}]"
        )
        voiced_midi = midi[midi >= 0]
        print(
            f"  midi median / range  : "
            f"{int(np.median(voiced_midi))}  "
            f"[{int(voiced_midi.min())}, {int(voiced_midi.max())}]"
        )

    print("--- key estimation ---")
    print(f"  tonal_center   : {out['tonal_center']}")
    print(f"  mode           : {out['mode']}")
    print(f"  key_confidence : {out['key_confidence']:.3f}")

    assert out["tonal_center"] == "A", (
        f"expected tonal_center='A', got {out['tonal_center']!r}"
    )
    assert out["mode"] == "major", (
        f"expected mode='major', got {out['mode']!r}"
    )
    print("  [OK] detected A major")

    # ------------------------------------------------------------------
    # 2) Hum + target -> DTW + transpose estimation.
    # ------------------------------------------------------------------
    target = synth_target_c_major()
    print(f"\n[target] {target.shape[0] / SR:.2f}s @ {SR} Hz (C-major melody)")

    out2 = proc.process(hum, target_wav=target, sr=SR)
    path = out2["dtw_alignment"]
    cents = out2["transpose_cents"]

    print("--- DTW alignment ---")
    print(f"  alignment path shape : {path.shape}  (T, 2)")
    print(f"  hum  frame range     : [{path[:, 0].min()}, {path[:, 0].max()}]")
    print(f"  tgt  frame range     : [{path[:, 1].min()}, {path[:, 1].max()}]")
    print(f"  transpose_cents      : {cents:+.1f}  (target -> hum)")
    # A and C are 3 semitones apart; expect roughly +/-300 cents
    # (or its octave-equivalent inside our (-600, 600] cents window).
    print(
        f"  |cents| in [200, 400] ?  "
        f"{200.0 <= abs(cents) <= 400.0}"
    )


if __name__ == "__main__":
    main()
