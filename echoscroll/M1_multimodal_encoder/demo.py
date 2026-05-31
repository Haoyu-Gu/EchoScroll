"""
Demo for EchoScroll M1 Multimodal Encoder.

Builds a synthetic Chinese-painting-like dummy image (no external download),
feeds it through MultimodalEncoder together with a bilingual text prompt and
a metadata dict, then prints shapes and the L2 norm of the fused vector z.

Run:   python demo.py
Device: auto-selects MPS on Apple Silicon, otherwise CPU.
First run will download CLIP-ViT-L/14 (~1.7GB) and bge-m3 (~2.3GB) weights.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from encoder import MultimodalEncoder


def make_dummy_painting(size: int = 336) -> Image.Image:
    """Tiny synthetic 'ink-wash landscape' so the demo runs offline."""
    img = Image.new("RGB", (size, size), (236, 228, 210))  # paper tone
    draw = ImageDraw.Draw(img)

    # Distant mountains (light grey)
    draw.polygon(
        [(0, size * 0.55), (size * 0.35, size * 0.30),
         (size * 0.55, size * 0.45), (size * 0.80, size * 0.28),
         (size, size * 0.50), (size, size * 0.62), (0, size * 0.62)],
        fill=(180, 180, 180),
    )
    # Foreground mountains (dark ink)
    draw.polygon(
        [(0, size * 0.78), (size * 0.20, size * 0.55),
         (size * 0.45, size * 0.72), (size * 0.70, size * 0.50),
         (size, size * 0.72), (size, size), (0, size)],
        fill=(70, 70, 70),
    )
    # A red seal stamp
    draw.rectangle(
        [(size * 0.85, size * 0.04), (size * 0.96, size * 0.14)],
        fill=(170, 30, 30),
    )
    return img.filter(ImageFilter.GaussianBlur(radius=1.2))


def main() -> None:
    print("[M1] Building MultimodalEncoder ...")
    encoder = MultimodalEncoder()
    print(f"[M1] Device = {encoder.device}")

    image = make_dummy_painting()
    text = "远山含黛, 江上孤舟. A serene literati landscape with distant misty peaks."
    metadata = {
        "title": "Misty Mountains (synthetic)",
        "artist": "Anonymous",
        "dynasty": "Song",
        "school": "Literati",
        "subject": "landscape",
        "medium": "ink on paper",
    }

    print("[M1] Encoding (this may take a while on first run while weights download)...")
    out = encoder.encode(image=image, text=text, metadata=metadata)

    z = out["z"]
    e_img = out["e_img"]
    e_txt = out["e_txt"]
    e_meta = out["e_meta"]

    print("\n=== EchoScroll M1 Multimodal Encoder ===")
    print(f"  e_img  shape = {e_img.shape}   dtype = {e_img.dtype}")
    print(f"  e_txt  shape = {e_txt.shape}   dtype = {e_txt.dtype}")
    print(f"  e_meta shape = {e_meta.shape}   dtype = {e_meta.dtype}")
    print(f"  z      shape = {z.shape}   dtype = {z.dtype}")
    print(f"  ||z||_2     = {float(np.linalg.norm(z)):.4f}")
    print(f"  z[:5]       = {np.round(z[:5], 4).tolist()}")

    # Sanity: text-only and image-only paths.
    print("\n[M1] Text-only encode:")
    out_t = encoder.encode(text="A peaceful guqin melody.")
    print(f"  ||z||_2 (text only)  = {float(np.linalg.norm(out_t['z'])):.4f}")

    print("[M1] Empty input encode (all zeros except bias path):")
    out_e = encoder.encode()
    print(f"  ||z||_2 (empty)      = {float(np.linalg.norm(out_e['z'])):.4f}")


if __name__ == "__main__":
    main()
