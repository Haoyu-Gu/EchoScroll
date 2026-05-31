"""
EchoScroll M1: Multimodal Encoder.

Image (CLIP-ViT-L/14) + Text (BAAI/bge-m3 SBERT) + Metadata (hash-based pseudo
embedding for MVP) --> fused multimodal vector z in R^d.

Self-contained module. No imports from other M* modules.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from transformers import AutoModel, AutoTokenizer, CLIPModel, CLIPProcessor


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

CLIP_MODEL_ID = "openai/clip-vit-large-patch14"
SBERT_MODEL_ID = "BAAI/bge-m3"

# Native hidden sizes for the chosen backbones.
CLIP_IMAGE_DIM = 768   # CLIP-ViT-L/14 vision projection output
SBERT_TEXT_DIM = 1024  # bge-m3 hidden size
META_RAW_DIM = 256     # hash-bucket dim per metadata field

# Metadata fields recognised by the encoder (extras ignored).
META_FIELDS = ("artist", "dynasty", "school", "subject", "medium", "title")

# Fused output dim.
FUSED_DIM = 768


# ---------------------------------------------------------------------------
# Fusion head
# ---------------------------------------------------------------------------

class FusionHead(nn.Module):
    """Project each modality to a common dim, sum, then non-linearity.

        z = GELU(W_v e_img + W_t e_txt + W_m e_meta + b)
    """

    def __init__(
        self,
        img_dim: int = CLIP_IMAGE_DIM,
        txt_dim: int = SBERT_TEXT_DIM,
        meta_dim: int = META_RAW_DIM,
        out_dim: int = FUSED_DIM,
    ) -> None:
        super().__init__()
        self.W_v = nn.Linear(img_dim, out_dim, bias=False)
        self.W_t = nn.Linear(txt_dim, out_dim, bias=False)
        self.W_m = nn.Linear(meta_dim, out_dim, bias=True)  # bias lives here

    def forward(
        self,
        e_img: torch.Tensor,
        e_txt: torch.Tensor,
        e_meta: torch.Tensor,
    ) -> torch.Tensor:
        h = self.W_v(e_img) + self.W_t(e_txt) + self.W_m(e_meta)
        return F.gelu(h)


# ---------------------------------------------------------------------------
# Metadata pseudo-embedding (deterministic, no training required)
# ---------------------------------------------------------------------------

def _hash_field_to_vec(field: str, value: str, dim: int) -> np.ndarray:
    """Hash a (field, value) pair into a deterministic dense vector in [-1, 1].

    Uses BLAKE2b with the dim derived from repeated digests; this is a stand-in
    for a learned per-field lookup table so the module runs without training.
    """
    out = np.zeros(dim, dtype=np.float32)
    seed = f"{field}::{value}".encode("utf-8")
    # Produce enough bytes by digesting incrementally with counter salts.
    needed = dim * 4
    buf = bytearray()
    counter = 0
    while len(buf) < needed:
        h = hashlib.blake2b(seed + counter.to_bytes(4, "little"), digest_size=64)
        buf.extend(h.digest())
        counter += 1
    raw = np.frombuffer(bytes(buf[:needed]), dtype=np.uint32).astype(np.float64)
    # Map to [-1, 1].
    out[:] = (raw / np.float64(2**32 - 1)) * 2.0 - 1.0
    # L2-normalise so each field contributes comparable magnitude.
    n = np.linalg.norm(out) + 1e-8
    return (out / n).astype(np.float32)


def metadata_to_vec(metadata: dict[str, Any] | None, dim: int = META_RAW_DIM) -> np.ndarray:
    """Average per-field hash vectors; empty metadata -> zero vector."""
    if not metadata:
        return np.zeros(dim, dtype=np.float32)
    vecs = []
    for field in META_FIELDS:
        val = metadata.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        vecs.append(_hash_field_to_vec(field, str(val).strip(), dim))
    if not vecs:
        return np.zeros(dim, dtype=np.float32)
    return np.mean(np.stack(vecs, axis=0), axis=0).astype(np.float32)


# ---------------------------------------------------------------------------
# Main encoder
# ---------------------------------------------------------------------------

class MultimodalEncoder:
    """Encodes (image, text, metadata) into a fused vector + per-modality vectors.

    Models are loaded lazily on first .encode() call so import is cheap.
    """

    def __init__(
        self,
        clip_model_id: str = CLIP_MODEL_ID,
        sbert_model_id: str = SBERT_MODEL_ID,
        device: str | None = None,
        out_dim: int = FUSED_DIM,
    ) -> None:
        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = torch.device(device)
        self.clip_model_id = clip_model_id
        self.sbert_model_id = sbert_model_id
        self.out_dim = out_dim

        # Lazy attributes
        self._clip_model: CLIPModel | None = None
        self._clip_processor: CLIPProcessor | None = None
        self._sbert_model = None
        self._sbert_tokenizer = None

        # Fusion head: built after we know the actual hidden sizes.
        self.fusion: FusionHead | None = None

    # -- Lazy loaders --------------------------------------------------------

    def _ensure_clip(self) -> None:
        if self._clip_model is None:
            self._clip_processor = CLIPProcessor.from_pretrained(self.clip_model_id)
            model = CLIPModel.from_pretrained(self.clip_model_id)
            model.eval()
            self._clip_model = model.to(self.device)

    def _ensure_sbert(self) -> None:
        if self._sbert_model is None:
            self._sbert_tokenizer = AutoTokenizer.from_pretrained(self.sbert_model_id)
            model = AutoModel.from_pretrained(self.sbert_model_id)
            model.eval()
            self._sbert_model = model.to(self.device)

    def _ensure_fusion(self, img_dim: int, txt_dim: int) -> None:
        if self.fusion is None:
            self.fusion = FusionHead(
                img_dim=img_dim,
                txt_dim=txt_dim,
                meta_dim=META_RAW_DIM,
                out_dim=self.out_dim,
            ).to(self.device)
            self.fusion.eval()

    # -- Per-modality encoders ----------------------------------------------

    def encode_image(self, image: Image.Image | str | Path) -> np.ndarray:
        """Return CLIP image projection embedding (numpy, shape [img_dim])."""
        self._ensure_clip()
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        else:
            image = image.convert("RGB")
        inputs = self._clip_processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            feats = self._clip_model.get_image_features(**inputs)  # [1, 768]
        feats = feats / (feats.norm(dim=-1, keepdim=True) + 1e-8)
        return feats[0].detach().to("cpu").float().numpy()

    def encode_text(self, text: str | None) -> np.ndarray:
        """Return SBERT (bge-m3) CLS-pooled embedding. Empty text -> zeros."""
        self._ensure_sbert()
        # Determine hidden dim once.
        hidden = int(self._sbert_model.config.hidden_size)
        if text is None or not str(text).strip():
            return np.zeros(hidden, dtype=np.float32)
        toks = self._sbert_tokenizer(
            str(text),
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        toks = {k: v.to(self.device) for k, v in toks.items()}
        with torch.no_grad():
            out = self._sbert_model(**toks)
        # bge-m3 dense embedding = first token (CLS) hidden state, then L2-norm.
        cls = out.last_hidden_state[:, 0]  # [1, hidden]
        cls = cls / (cls.norm(dim=-1, keepdim=True) + 1e-8)
        return cls[0].detach().to("cpu").float().numpy()

    def encode_metadata(self, metadata: dict[str, Any] | None) -> np.ndarray:
        return metadata_to_vec(metadata, dim=META_RAW_DIM)

    # -- Top-level API ------------------------------------------------------

    def encode(
        self,
        image: Image.Image | str | Path | None = None,
        text: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, np.ndarray]:
        """Encode any subset of (image, text, metadata) into a fused vector.

        Missing modalities are replaced with zero vectors at their native dim.
        Returns {"z", "e_img", "e_txt", "e_meta"}, all numpy arrays.
        """
        # Image branch.
        if image is not None:
            e_img = self.encode_image(image)
        else:
            self._ensure_clip()
            e_img = np.zeros(CLIP_IMAGE_DIM, dtype=np.float32)

        # Text branch (also returns zeros internally for empty string).
        self._ensure_sbert()
        e_txt = self.encode_text(text)

        # Metadata branch.
        e_meta = self.encode_metadata(metadata)

        # Build fusion head now that we know the real dims.
        self._ensure_fusion(img_dim=e_img.shape[0], txt_dim=e_txt.shape[0])

        t_img = torch.from_numpy(e_img).unsqueeze(0).to(self.device)
        t_txt = torch.from_numpy(e_txt).unsqueeze(0).to(self.device)
        t_meta = torch.from_numpy(e_meta).unsqueeze(0).to(self.device)
        with torch.no_grad():
            z = self.fusion(t_img, t_txt, t_meta)  # [1, out_dim]
        z_np = z[0].detach().to("cpu").float().numpy()

        return {
            "z": z_np,
            "e_img": e_img,
            "e_txt": e_txt,
            "e_meta": e_meta,
        }


__all__ = ["MultimodalEncoder", "FusionHead", "metadata_to_vec"]
