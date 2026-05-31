# M7 — Humming Interaction

Pure-DSP module (no neural net, no torch). Given a 2-5 s mono hum and
optionally the currently generated soundtrack, extract:

- **Pitch contour** — frame-level F0 via `librosa.pyin` (YIN), fmin=C2,
  fmax=C7. Returned as both Hz (`NaN` unvoiced) and rounded MIDI (`-1`
  unvoiced).
- **Tonal centre + mode** — Krumhansl-Schmuckler key-profile correlation
  over **three** profiles: `major` (KS), `minor` (KS), and a custom
  `pentatonic_gong` profile (Chinese 宫调式, weights concentrated on
  scale degrees 0/2/4/7/9). Best Pearson `r` < 0.30 → `"unclear"`.
- **DTW alignment** (optional, when `target_wav` is given) — chroma-CQT
  features + `librosa.sequence.dtw` (cosine metric). The average pitch
  offset (in cents) needed to transpose the target onto the hum is
  estimated by comparing the octave-folded medians of the voiced F0
  envelopes.

**API**:
```python
from humming import HummingProcessor
proc = HummingProcessor()
out = proc.process(hum_wav, target_wav=None, sr=22050)
# out keys: pitch_contour_hz, midi_contour, tonal_center, mode,
#           key_confidence, [dtw_alignment, transpose_cents]
```

**Run**: `python demo.py` — synthesises an A-major arpeggio hum, checks
detected key is `"A" / "major"`, then DTW-aligns it to a C-major target
and prints the estimated transposition in cents (~±300).
