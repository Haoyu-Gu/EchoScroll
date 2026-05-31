"""
EchoScroll M4: Music Generator.

Wraps MusicGen (``facebook/musicgen-small`` by default) with V--A and LoRA
conditioning hooks. A pure-CPU mock fallback (``MockMusicGenerator``) is
provided so that the MacBook demo can run without downloading any weights.

Self-contained module. No imports from other M* modules.

I/O contract
------------
Input to ``generate``: a ``GenerationCondition`` dict::

    {
      "text_prompt":        str,
      "va":                 (valence: float, arousal: float),   # each in [-1, 1]
      "retrieved_context":  list[str] | None,
      "duration_s":         int,
      "control_descriptors": dict | None,
    }

Output: ``{"wav": np.ndarray (mono, float32), "sample_rate": 32000,
"prompt_used": str}``.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


SAMPLE_RATE = 32000
DEFAULT_MODEL_ID = "facebook/musicgen-small"
RETRIEVED_CONTEXT_CHAR_BUDGET = 200


# ---------------------------------------------------------------------------
# Device helper
# ---------------------------------------------------------------------------

def _select_device() -> str:
    """Return ``'mps'`` on Apple Silicon, else ``'cpu'``. CUDA not assumed here."""
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def va_to_mood_adjectives(valence: float, arousal: float) -> list[str]:
    """Map a V--A point to 1-2 mood adjectives.

    Quadrants of the V--A plane (centered at 0):
        (+v, +a) -> "joyful"      / bright, lively
        (+v, -a) -> "serene"      / calm, warm
        (-v, +a) -> "tense"       / agitated, dark
        (-v, -a) -> "melancholic" / quiet, somber

    Points close to an axis pick up a softer secondary descriptor.
    """
    v = float(np.clip(valence, -1.0, 1.0))
    a = float(np.clip(arousal, -1.0, 1.0))

    if v >= 0 and a >= 0:
        base = "joyful"
    elif v >= 0 and a < 0:
        base = "serene"
    elif v < 0 and a >= 0:
        base = "tense"
    else:
        base = "melancholic"

    adjectives = [base]
    # Soft secondary descriptor when one axis is much stronger than the other.
    if abs(v) > 0.5 and abs(a) < 0.25:
        adjectives.append("warm" if v >= 0 else "somber")
    elif abs(a) > 0.5 and abs(v) < 0.25:
        adjectives.append("energetic" if a >= 0 else "still")
    return adjectives


def _truncate_context(snippets: Iterable[str], char_budget: int) -> str:
    """Concatenate retrieved snippets up to ``char_budget`` characters."""
    out: list[str] = []
    remaining = char_budget
    for s in snippets:
        s = (s or "").strip()
        if not s:
            continue
        if len(s) + 2 > remaining:  # +2 for separator
            if remaining > 8:
                out.append(s[: remaining - 1].rstrip() + "...")
            break
        out.append(s)
        remaining -= len(s) + 2
    return "; ".join(out)


def build_prompt(condition: dict) -> str:
    """Build the final natural-language prompt sent to MusicGen.

    Composition order: ``<text_prompt>, <mood adjectives>, <control hints>,
    context: <retrieved snippets>``. All components are optional.
    """
    parts: list[str] = []

    text_prompt = (condition.get("text_prompt") or "").strip()
    if text_prompt:
        parts.append(text_prompt)

    va = condition.get("va")
    if va is not None:
        v, a = float(va[0]), float(va[1])
        moods = va_to_mood_adjectives(v, a)
        parts.append(", ".join(moods) + " mood")

    ctrl = condition.get("control_descriptors") or {}
    if isinstance(ctrl, dict) and ctrl:
        ctrl_bits = []
        for k in ("tempo", "instrumentation", "texture", "dynamics", "register"):
            if k in ctrl and ctrl[k] not in (None, ""):
                ctrl_bits.append(f"{k}: {ctrl[k]}")
        if ctrl_bits:
            parts.append("; ".join(ctrl_bits))

    snippets = condition.get("retrieved_context") or []
    if snippets:
        ctx = _truncate_context(snippets, RETRIEVED_CONTEXT_CHAR_BUDGET)
        if ctx:
            parts.append(f"context: {ctx}")

    return ". ".join(parts).strip() or "instrumental Chinese-style soundtrack"


# ---------------------------------------------------------------------------
# LoRA wiring (no training here)
# ---------------------------------------------------------------------------

@dataclass
class LoRAConfig:
    """Thin wrapper around the LoRA hyper-parameters we care about."""

    r: int = 8
    alpha: int = 16
    dropout: float = 0.05
    target_modules: tuple[str, ...] = ("q_proj", "v_proj")
    bias: str = "none"
    task_type: str = "FEATURE_EXTRACTION"


def prepare_lora(
    model: Any,
    r: int = 8,
    alpha: int = 16,
    target_modules: list[str] | None = None,
    dropout: float = 0.05,
) -> Any:
    """Wrap MusicGen's text encoder with PEFT-LoRA adapters.

    Targets attention ``q_proj`` / ``v_proj`` of MusicGen's text encoder.
    Returns the (now PEFT-wrapped) ``model``. We do *not* train here --
    this only confirms that the wiring is valid. A separate fine-tune
    script is out of scope for this module.
    """
    from peft import LoraConfig, get_peft_model

    if target_modules is None:
        target_modules = ["q_proj", "v_proj"]

    peft_cfg = LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        bias="none",
        target_modules=list(target_modules),
        task_type="FEATURE_EXTRACTION",
    )

    # MusicGenForConditionalGeneration owns a ``text_encoder`` submodule.
    text_encoder = getattr(model, "text_encoder", None)
    if text_encoder is None:
        raise AttributeError(
            "MusicGen model has no .text_encoder; cannot attach LoRA."
        )

    model.text_encoder = get_peft_model(text_encoder, peft_cfg)
    return model


# ---------------------------------------------------------------------------
# Real MusicGen wrapper
# ---------------------------------------------------------------------------

class MusicGenWrapper:
    """Lightweight wrapper around ``MusicgenForConditionalGeneration``.

    Usage::

        gen = MusicGenWrapper().load()
        out = gen.generate({"text_prompt": "...", "va": (0.2, -0.3),
                            "retrieved_context": [...], "duration_s": 10})
        gen.save_audio(out["wav"], "out.wav")
    """

    def __init__(self) -> None:
        self.model = None
        self.processor = None
        self.model_id: str | None = None
        self.device: str = _select_device()
        self.use_lora: bool = False

    def load(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        use_lora: bool = False,
        lora_dir: str | Path | None = None,
    ) -> "MusicGenWrapper":
        """Download (or read cached) MusicGen weights and move to device."""
        import torch
        from transformers import AutoProcessor, MusicgenForConditionalGeneration

        self.model_id = model_id
        self.processor = AutoProcessor.from_pretrained(model_id)
        model = MusicgenForConditionalGeneration.from_pretrained(model_id)

        if use_lora:
            model = prepare_lora(model)
            self.use_lora = True
            if lora_dir is not None:
                # Optional: load pretrained adapter weights.
                try:
                    from peft import PeftModel

                    model.text_encoder = PeftModel.from_pretrained(
                        model.text_encoder, str(lora_dir)
                    )
                except Exception as e:  # pragma: no cover - depends on user files
                    warnings.warn(f"Failed to load LoRA adapter from {lora_dir}: {e}")

        model.to(self.device)
        model.eval()
        self.model = model
        return self

    # ------------------------------------------------------------------ #
    def _tokens_for_duration(self, duration_s: int) -> int:
        """MusicGen-small uses a 50 Hz audio codec; pick a safe upper bound."""
        return max(64, int(duration_s) * 50 + 4)

    def generate(self, condition: dict) -> dict:
        """Generate a waveform conditioned on ``condition``.

        Returns ``{"wav": np.ndarray, "sample_rate": int, "prompt_used": str}``.
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("MusicGenWrapper.load() must be called first.")

        import torch

        prompt = build_prompt(condition)
        duration_s = int(condition.get("duration_s", 10))

        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt",
        ).to(self.device)

        max_new_tokens = self._tokens_for_duration(duration_s)
        with torch.no_grad():
            audio = self.model.generate(
                **inputs,
                do_sample=True,
                guidance_scale=3.0,
                max_new_tokens=max_new_tokens,
            )

        wav = audio[0, 0].detach().to("cpu").float().numpy()
        sr = int(getattr(self.model.config.audio_encoder, "sampling_rate", SAMPLE_RATE))

        return {"wav": wav, "sample_rate": sr, "prompt_used": prompt}

    # ------------------------------------------------------------------ #
    @staticmethod
    def save_audio(wav: np.ndarray, path: str | Path, sample_rate: int = SAMPLE_RATE) -> Path:
        """Write a mono float32 waveform to ``path`` as 16-bit PCM WAV."""
        return _save_wav(wav, path, sample_rate)


# ---------------------------------------------------------------------------
# Mock generator (CPU-only, zero downloads)
# ---------------------------------------------------------------------------

class MockMusicGenerator:
    """Sine-modulated waveform whose pitch and tempo come from V--A.

    Always works on CPU. Useful for the MacBook demo path and for
    deterministic CI tests of the pipeline. The audio is by no means
    musically interesting -- it is a placeholder that proves the I/O
    contract end-to-end.
    """

    sample_rate: int = SAMPLE_RATE

    def load(self, *_args, **_kwargs) -> "MockMusicGenerator":  # noqa: D401
        """No-op; kept for interface parity with :class:`MusicGenWrapper`."""
        return self

    def generate(self, condition: dict) -> dict:
        v, a = condition.get("va", (0.0, 0.0))
        v, a = float(np.clip(v, -1.0, 1.0)), float(np.clip(a, -1.0, 1.0))
        duration_s = int(condition.get("duration_s", 10))

        # Pitch: valence drives base frequency (sad/melancholic -> lower).
        # Range: ~196 Hz (G3) for v=-1 to ~523 Hz (C5) for v=+1.
        base_freq = 196.0 * (2.0 ** ((v + 1.0) * 0.5 * (math.log2(523.0 / 196.0))))
        # Tempo: arousal drives modulation rate (Hz).
        mod_rate = 0.5 + (a + 1.0) * 1.25  # 0.5 .. 3.0 Hz
        # Amplitude envelope intensity: arousal -> louder swells.
        depth = 0.25 + 0.35 * (a + 1.0) * 0.5

        n = int(self.sample_rate * duration_s)
        t = np.arange(n, dtype=np.float32) / float(self.sample_rate)

        # Slight vibrato so it doesn't sound like a test tone.
        vibrato = 1.0 + 0.01 * np.sin(2 * math.pi * 5.0 * t)
        carrier = np.sin(2 * math.pi * base_freq * vibrato * t)

        # Add a fifth above for a tiny bit of body; weight by |valence|.
        fifth = np.sin(2 * math.pi * (base_freq * 1.5) * t) * (0.3 + 0.2 * v)

        envelope = (1.0 - depth) + depth * (
            0.5 * (1.0 + np.sin(2 * math.pi * mod_rate * t))
        )

        wav = (0.7 * carrier + 0.3 * fifth) * envelope
        # Soft fade in / fade out to avoid clicks.
        fade = min(int(0.05 * self.sample_rate), n // 4)
        if fade > 0:
            wav[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
            wav[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)

        wav = (0.9 * wav / max(1e-6, float(np.max(np.abs(wav))))).astype(np.float32)
        prompt = build_prompt(condition)
        return {"wav": wav, "sample_rate": self.sample_rate, "prompt_used": prompt}

    @staticmethod
    def save_audio(wav: np.ndarray, path: str | Path, sample_rate: int = SAMPLE_RATE) -> Path:
        return _save_wav(wav, path, sample_rate)


# ---------------------------------------------------------------------------
# Shared WAV writer
# ---------------------------------------------------------------------------

def _save_wav(wav: np.ndarray, path: str | Path, sample_rate: int) -> Path:
    """Write a float32 [-1, 1] mono waveform as 16-bit PCM WAV."""
    from scipy.io import wavfile

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    arr = np.asarray(wav, dtype=np.float32).squeeze()
    if arr.ndim != 1:
        raise ValueError(f"Expected mono waveform, got shape {arr.shape}")

    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    if peak > 1.0:
        arr = arr / peak
    pcm = np.clip(arr * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(str(path), int(sample_rate), pcm)
    return path
