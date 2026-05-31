"""
EchoScroll FastAPI backend (skeleton / stubs).

All endpoints return plausible fake data so the React front-end can be wired
up and demoed without M1-M7 being present. Replace the bodies marked with
``# TODO: wire to M*`` once the corresponding modules are integrated.

Run:
    uvicorn backend.main:app --reload
"""

from __future__ import annotations

import asyncio
import json
import shutil
import uuid
import wave
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .schemas import (
    Descriptors,
    EditPromptRequest,
    EditPromptResponse,
    EditVARequest,
    EditVAResponse,
    GenerateRequest,
    GenerateResponse,
    HummingResponse,
    PreviewProgress,
    RetrievedDoc,
    UploadResponse,
)


# -------------------- paths -----------------------------------------------

ROOT_DIR = Path("/tmp/echoscroll")
UPLOAD_DIR = ROOT_DIR / "uploads"
AUDIO_DIR = ROOT_DIR / "audio"
STUB_WAV = ROOT_DIR / "stub.wav"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# -------------------- stub audio synth ------------------------------------


def _write_sine_wav(path: Path, freq: float = 220.0, duration_s: float = 10.0,
                    sample_rate: int = 22050) -> None:
    """Write a mono 16-bit PCM sine wave to ``path``."""
    n = int(sample_rate * duration_s)
    t = np.arange(n, dtype=np.float32) / sample_rate
    # gentle fade-in / fade-out so the demo doesn't click
    envelope = np.minimum(np.minimum(t * 5.0, 1.0),
                          np.maximum(0.0, (duration_s - t) * 5.0))
    samples = 0.3 * envelope * np.sin(2 * np.pi * freq * t)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


if not STUB_WAV.exists():
    _write_sine_wav(STUB_WAV, freq=220.0, duration_s=10.0)


# -------------------- in-memory painting registry -------------------------

_PAINTINGS: dict[str, dict] = {}


def _va_for_painting(painting_id: str) -> tuple[float, float]:
    """Deterministic fake V-A so the same upload returns a stable point."""
    h = abs(hash(painting_id))
    v = ((h % 1000) / 1000.0) * 2 - 1
    a = (((h // 1000) % 1000) / 1000.0) * 2 - 1
    # bias toward upper half-plane (interesting paintings are rarely flatlines)
    return round(v * 0.7, 3), round(a * 0.7, 3)


def _stub_descriptors(va: tuple[float, float]) -> Descriptors:
    v, a = va
    tempo = int(72 + a * 40)  # high arousal -> faster
    dynamics = "mf" if a > 0 else "p"
    mode = "pentatonic-gong" if v >= 0 else "pentatonic-yu"
    return Descriptors(
        mode=mode,
        tempo_bpm=max(40, min(160, tempo)),
        instrumentation=["guqin", "xiao", "erhu"] if v >= 0 else ["guqin", "pipa"],
        dynamics=dynamics,
        texture="sparse" if a < 0 else "moderate",
        timbre="warm" if v >= 0 else "veiled",
        articulation="legato",
        style_tags=["traditional-chinese", "ink-wash"],
    )


def _stub_retrieved(painting_id: str) -> list[RetrievedDoc]:
    return [
        RetrievedDoc(
            doc_id=f"art-{painting_id[:6]}-001",
            title="Northern Song landscape conventions",
            snippet="Monumental compositions and atmospheric perspective characterise...",
            score=0.81,
        ),
        RetrievedDoc(
            doc_id=f"art-{painting_id[:6]}-002",
            title="Literati ideals and the guqin",
            snippet="The guqin embodied the scholarly aesthetic of restraint and depth...",
            score=0.74,
        ),
    ]


# -------------------- app -------------------------------------------------

app = FastAPI(title="EchoScroll Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"service": "echoscroll-backend", "version": app.version}


# -------------------- /upload ---------------------------------------------


@app.post("/upload", response_model=UploadResponse)
async def upload(
    image: UploadFile = File(...),
    title: Optional[str] = Form(None),
    artist: Optional[str] = Form(None),
    dynasty: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
) -> UploadResponse:
    """Accept a painting + metadata, store it under /tmp/echoscroll/uploads."""
    painting_id = uuid.uuid4().hex[:12]
    suffix = Path(image.filename or "upload.png").suffix or ".png"
    dest = UPLOAD_DIR / f"{painting_id}{suffix}"
    with dest.open("wb") as fh:
        shutil.copyfileobj(image.file, fh)

    _PAINTINGS[painting_id] = {
        "id": painting_id,
        "title": title,
        "artist": artist,
        "dynasty": dynasty,
        "text": text,
        "local_path": str(dest),
    }
    return UploadResponse(
        painting_id=painting_id,
        title=title,
        preview_url=f"/preview/{painting_id}",
    )


@app.get("/preview/{painting_id}")
def preview(painting_id: str) -> FileResponse:
    rec = _PAINTINGS.get(painting_id)
    if rec is None:
        raise HTTPException(404, "painting not found")
    return FileResponse(rec["local_path"])


# -------------------- /generate -------------------------------------------


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    """Stub: would call M1->M2->M3->M4 in sequence."""
    if req.painting_id not in _PAINTINGS:
        # accept unknown ids (the frontend may demo without uploading)
        _PAINTINGS[req.painting_id] = {"id": req.painting_id}
    va = _va_for_painting(req.painting_id)
    # TODO: wire to M4_music_generator
    return GenerateResponse(
        audio_url=f"/audio/{req.painting_id}",
        va=va,
        descriptors=_stub_descriptors(va),
        retrieved_context=_stub_retrieved(req.painting_id),
    )


# -------------------- /edit/va --------------------------------------------


@app.post("/edit/va", response_model=EditVAResponse)
async def edit_va(req: EditVARequest) -> EditVAResponse:
    # TODO: wire to M5_editing_layer
    return EditVAResponse(
        audio_url=f"/audio/{req.painting_id}?v={req.va_target[0]:.2f}&a={req.va_target[1]:.2f}",
        va=req.va_target,
    )


# -------------------- /edit/prompt ----------------------------------------


@app.post("/edit/prompt", response_model=EditPromptResponse)
async def edit_prompt(req: EditPromptRequest) -> EditPromptResponse:
    # TODO: wire to M6_prompt_translator
    va = _va_for_painting(req.painting_id)
    descriptors = _stub_descriptors(va)
    # Pretend the colloquial prompt nudges arousal up if it mentions "faster"
    if "faster" in req.colloquial_prompt.lower() or "快" in req.colloquial_prompt:
        descriptors.tempo_bpm = min(160, descriptors.tempo_bpm + 20)
        va = (va[0], min(1.0, va[1] + 0.2))
    return EditPromptResponse(
        audio_url=f"/audio/{req.painting_id}",
        descriptors=descriptors,
        va=va,
    )


# -------------------- /edit/humming ---------------------------------------


@app.post("/edit/humming", response_model=HummingResponse)
async def edit_humming(audio: UploadFile = File(...)) -> HummingResponse:
    # Consume the upload so the client doesn't hang on large files
    _ = await audio.read()
    # TODO: wire to M7_humming_interaction
    return HummingResponse(
        midi_contour=[60, 62, 64, 67, 69, 67, 64, 62, 60],
        tonal_center="D",
        transpose_cents=-12,
    )


# -------------------- /audio/{id} -----------------------------------------


@app.get("/audio/{painting_id}")
def audio(painting_id: str) -> FileResponse:
    """Serves the stock stub wav. Query params are ignored by the stub."""
    return FileResponse(STUB_WAV, media_type="audio/wav", filename=f"{painting_id}.wav")


# -------------------- /ws/preview -----------------------------------------


@app.websocket("/ws/preview")
async def ws_preview(ws: WebSocket) -> None:
    """
    Streams fake progress events for a generation request. The client sends
    one JSON message ``{"painting_id": "..."}`` to start the stream.
    """
    await ws.accept()
    try:
        raw = await ws.receive_text()
        msg = json.loads(raw)
        painting_id = msg.get("painting_id", "unknown")

        stages = [
            ("encode_image", "Encoding painting with CLIP..."),
            ("retrieve_context", "Retrieving art-history context..."),
            ("project_va", "Projecting to V-A space..."),
            ("translate_prompt", "Translating to musical descriptors..."),
            ("generate_audio", "Generating audio with MusicGen..."),
            ("finalise", "Finalising track..."),
        ]
        for i, (stage, message) in enumerate(stages):
            progress = (i + 1) / len(stages)
            evt = PreviewProgress(stage=stage, progress=progress, message=message)
            await ws.send_text(evt.model_dump_json())
            await asyncio.sleep(0.4)

        # final payload event
        va = _va_for_painting(painting_id)
        done = PreviewProgress(
            stage="done",
            progress=1.0,
            message="ready",
            payload={"audio_url": f"/audio/{painting_id}", "va": list(va)},
        )
        await ws.send_text(done.model_dump_json())
    except WebSocketDisconnect:
        return
    except Exception as exc:  # pragma: no cover - defensive
        try:
            await ws.send_text(json.dumps({"stage": "error", "message": str(exc)}))
        finally:
            await ws.close()
