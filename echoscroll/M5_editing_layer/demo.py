"""End-to-end demo for M5 (editing layer).

Synthesises a 10-second test waveform (A4 + E5 sines with an AM envelope and
four short noise bursts to act as fake transients), then exercises the four
editing ops:

    1. detect_beats / segment
    2. change_bpm (x0.5 slower, x1.5 faster)
    3. replace_segment (middle segment overwritten with white noise)
    4. style_transfer_prompt (a simple text rewrite)

Outputs are written to ./out_*.wav next to this script.
Run:  python demo.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from editor import EditingLayer


SR = 32000
DURATION_S = 10.0


def synth_test_wav(sr: int = SR, duration_s: float = DURATION_S) -> np.ndarray:
    """A4 + E5 sines with slow AM, plus 4 short noise bursts as fake beats."""
    rng = np.random.default_rng(42)
    n = int(round(sr * duration_s))
    t = np.arange(n, dtype=np.float32) / sr

    # Two sine tones an approximate perfect-fifth apart.
    a4 = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
    e5 = np.sin(2.0 * np.pi * 659.25 * t).astype(np.float32)

    # Slow amplitude envelope (2 Hz tremolo, half-depth).
    env = 0.5 * (1.0 + 0.5 * np.sin(2.0 * np.pi * 2.0 * t)).astype(np.float32)
    tone = 0.4 * env * (a4 + 0.7 * e5)

    # Four noise bursts at 1.0, 3.5, 6.0, 8.5 s — fake transients for the beat
    # tracker to latch on to.
    burst_times = [1.0, 3.5, 6.0, 8.5]
    burst_len = int(0.04 * sr)  # 40 ms
    burst_env = np.linspace(1.0, 0.0, burst_len, dtype=np.float32) ** 2
    for bt in burst_times:
        start = int(bt * sr)
        end = min(start + burst_len, n)
        burst = rng.standard_normal(end - start).astype(np.float32) * 0.6
        tone[start:end] += burst * burst_env[: end - start]

    # Normalise to avoid clipping when summed.
    peak = float(np.max(np.abs(tone))) or 1.0
    return (tone / peak * 0.9).astype(np.float32)


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    print(f"[M5 demo] output dir: {out_dir}")

    wav = synth_test_wav()
    sf.write(out_dir / "out_input.wav", wav, SR)
    print(f"[M5 demo] wrote out_input.wav  ({len(wav)/SR:.2f} s)")

    editor = EditingLayer(sr=SR)

    # --- op 1: beat detection + segmentation ----------------------------------
    beats = editor.detect_beats(wav)
    print(f"[M5 demo] detected {len(beats)} beats: {np.round(beats, 3).tolist()}")

    segments = editor.segment(wav, beats)
    print(f"[M5 demo] segmented into {len(segments)} chunks "
          f"(lengths in samples: {[len(s) for s in segments]})")

    # --- op 2: BPM stretch ----------------------------------------------------
    # We don't actually need to *know* the real BPM; the function only cares
    # about the ratio.  Use a nominal 120 BPM source.
    slow = editor.change_bpm(wav, src_bpm=120.0, tgt_bpm=60.0)   # x0.5 slower
    fast = editor.change_bpm(wav, src_bpm=120.0, tgt_bpm=180.0)  # x1.5 faster
    sf.write(out_dir / "out_bpm_x0.5.wav", slow, SR)
    sf.write(out_dir / "out_bpm_x1.5.wav", fast, SR)
    print(f"[M5 demo] wrote out_bpm_x0.5.wav  ({len(slow)/SR:.2f} s)")
    print(f"[M5 demo] wrote out_bpm_x1.5.wav  ({len(fast)/SR:.2f} s)")

    # --- op 3: segment replacement with white noise --------------------------
    if len(beats) >= 2 and len(segments) >= 3:
        # Replace a middle segment (one of the inner ones, not the head/tail).
        mid_idx = len(segments) // 2
        # Match the replacement length to the segment it overwrites so the
        # output is roughly the same duration as the input.
        target_len = len(segments[mid_idx])
        rng = np.random.default_rng(0)
        noise = (rng.standard_normal(target_len) * 0.3).astype(np.float32)

        spliced = editor.replace_segment(
            wav, beats, segment_idx=mid_idx, replacement_wav=noise,
            crossfade_ms=50.0,
        )
        sf.write(out_dir / "out_replace_mid.wav", spliced, SR)
        print(f"[M5 demo] replaced segment #{mid_idx} (len={target_len} samp) "
              f"with white noise; wrote out_replace_mid.wav "
              f"({len(spliced)/SR:.2f} s)")
    else:
        print("[M5 demo] not enough beats to demo segment replacement; "
              "skipping out_replace_mid.wav")

    # --- op 4: style-transfer prompt rewrite ---------------------------------
    old = "a calm guqin piece evoking misty mountains, slow tempo"
    new = editor.style_transfer_prompt(old, target_style="orchestral")
    print(f"[M5 demo] style rewrite:\n    old: {old!r}\n    new: {new!r}")

    # Edit log
    print("[M5 demo] edit log:")
    for entry in editor.log:
        print(f"    - {entry.op}: {entry.params}")


if __name__ == "__main__":
    main()
