# M1 — Multimodal Encoder

Encodes a Chinese painting `(image, text, metadata)` into a fused multimodal
vector `z ∈ R^768`, plus per-modality embeddings `e_img / e_txt / e_meta` for
debugging and RAG queries.

- **Vision**: `openai/clip-vit-large-patch14` (vision tower, 768-dim).
- **Text**: `BAAI/bge-m3` SBERT (Chinese+English, CLS-pooled, 1024-dim).
- **Metadata**: deterministic hash-based pseudo-embedding (256-dim) over fields
  `artist / dynasty / school / subject / medium / title`. Zero-init MVP; a real
  learned lookup can drop in later without changing the API.
- **Fusion**: `z = GELU(W_v e_img + W_t e_txt + W_m e_meta + b)` (`nn.Module`).

**Run**: `python demo.py` (auto-uses MPS on Apple Silicon, else CPU). The demo
generates a synthetic ink-wash dummy image so no asset download is needed.
First run pulls ≈ 1.7 GB (CLIP-L/14) + ≈ 2.3 GB (bge-m3) of weights from the
HuggingFace cache; subsequent runs are fast.

**API**:
```python
from encoder import MultimodalEncoder
enc = MultimodalEncoder()
out = enc.encode(image=pil_img, text="远山含黛", metadata={"dynasty": "Song"})
# out = {"z": (768,), "e_img": (768,), "e_txt": (1024,), "e_meta": (256,)}
```
