# M5 · Editing Layer

Pure-DSP, CPU-only refinement of a MusicGen-generated soundtrack. Inputs are a
mono `float32` waveform (sr ≈ 32 kHz) plus an edit request; outputs are the
edited waveform and a log of what changed.

Four operations, all exposed both as module-level functions in `editor.py` and
as methods of `EditingLayer`:

1. **Beat detection / segmentation** — `detect_beats(wav, sr)` uses
   `librosa.beat.beat_track`; `segment(wav, sr, beat_times)` slices at beat
   boundaries.
2. **BPM adjustment** — `change_bpm(wav, sr, src_bpm, tgt_bpm)` calls
   `librosa.effects.time_stretch` (an STFT phase vocoder with phase advance
   `phi'[m,k] = phi'[m-1,k] + alpha*(phi[m,k] - phi[m-1,k])`). This preserves
   pitch and only stretches time.
3. **Segment replacement** — `replace_segment(wav, sr, beat_times, idx,
   replacement)` splices the new clip in with a 50 ms equal-power cross-fade
   at each boundary.
4. **Style-transfer prompt rewrite** — `style_transfer_prompt(prompt, style)`
   swaps the style adjective in a MusicGen text prompt; the actual
   re-generation is delegated to M4.

Run `python demo.py` to synthesise a 10 s test wav (A4 + E5 with 4 noise
bursts as fake beats) and emit `out_input.wav`, `out_bpm_x0.5.wav`,
`out_bpm_x1.5.wav` and `out_replace_mid.wav`. No torch, no NN models, no
cross-imports.
