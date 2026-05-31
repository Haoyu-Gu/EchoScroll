"""
Pydantic request / response models for the EchoScroll backend.

These shapes mirror what M1-M7 will actually return once wired in;
the routes in `main.py` currently fill them with stub data.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any

from pydantic import BaseModel, Field


# -------------------- Common ----------------------------------------------


class VA(BaseModel):
    """Valence-Arousal pair. Each axis is in [-1, 1]."""

    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=-1.0, le=1.0)


class Descriptors(BaseModel):
    """
    The 8-slot musical descriptor schema produced by M6 (prompt translator)
    and consumed by M4 (music generator).
    """

    mode: str = "pentatonic-gong"
    tempo_bpm: int = 72
    instrumentation: List[str] = Field(default_factory=lambda: ["guqin", "xiao", "erhu"])
    dynamics: str = "mp"
    texture: str = "sparse"
    timbre: str = "warm"
    articulation: str = "legato"
    style_tags: List[str] = Field(default_factory=lambda: ["traditional-chinese", "ink-wash"])


class RetrievedDoc(BaseModel):
    """A single retrieval hit from M3 art-history RAG."""

    doc_id: str
    title: str
    snippet: str
    score: float


# -------------------- /upload ---------------------------------------------


class UploadResponse(BaseModel):
    painting_id: str
    title: Optional[str] = None
    preview_url: str


# -------------------- /generate -------------------------------------------


class GenerateRequest(BaseModel):
    painting_id: str
    duration_s: float = 10.0
    user_prompt: Optional[str] = None


class GenerateResponse(BaseModel):
    audio_url: str
    va: Tuple[float, float]
    descriptors: Descriptors
    retrieved_context: List[RetrievedDoc] = Field(default_factory=list)


# -------------------- /edit/va --------------------------------------------


class EditVARequest(BaseModel):
    painting_id: str
    va_target: Tuple[float, float]


class EditVAResponse(BaseModel):
    audio_url: str
    va: Tuple[float, float]


# -------------------- /edit/prompt ----------------------------------------


class EditPromptRequest(BaseModel):
    painting_id: str
    colloquial_prompt: str


class EditPromptResponse(BaseModel):
    audio_url: str
    descriptors: Descriptors
    va: Tuple[float, float]


# -------------------- /edit/humming ---------------------------------------


class HummingResponse(BaseModel):
    midi_contour: List[int]
    tonal_center: str
    transpose_cents: int


# -------------------- /ws/preview -----------------------------------------


class PreviewProgress(BaseModel):
    stage: str
    progress: float  # 0..1
    message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
