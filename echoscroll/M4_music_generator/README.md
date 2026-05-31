# M4 · Music Generator

Wraps **MusicGen** (`facebook/musicgen-small`) with V–A and LoRA conditioning
hooks for EchoScroll.

**I/O contract**

- Input: a `GenerationCondition` dict
  `{"text_prompt": str, "va": (v, a), "retrieved_context": list[str]|None,
  "duration_s": int, "control_descriptors": dict|None}`.
- Output: `{"wav": np.ndarray (mono, float32), "sample_rate": 32000,
  "prompt_used": str}`.

**How**: `build_prompt` templates the text prompt, maps V–A to mood adjectives
(`serene` / `tense` / `joyful` / `melancholic`), appends optional control
descriptors, and concatenates retrieved RAG snippets (total ≤ 200 chars).
`MusicGenWrapper.generate` then drives `MusicgenForConditionalGeneration`.

**Mock vs Real**:
- `MockMusicGenerator` (default in `demo.py`) — pure-CPU sine generator whose
  pitch comes from valence and tempo from arousal. Zero downloads.
- `MusicGenWrapper` (real) — downloads `facebook/musicgen-small` (~2 GB).
  Enable with `python demo.py --real`. Uses `mps` on Apple Silicon, else `cpu`.

**LoRA**: `prepare_lora(model, r=8, alpha=16, target_modules=["q_proj","v_proj"])`
attaches PEFT adapters to MusicGen's text encoder attention. Training is **out
of scope** here — a separate fine-tune script (TBD) will own dataset, loss and
adapter checkpoints.
