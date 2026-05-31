"""Compute Frechet Audio Distance between a generated set and a reference set.

Supports VGGish (16 kHz, 128-d) or OpenL3 (48 kHz, 512-d) embedders.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm


def load_wav(path: Path, sr: int) -> np.ndarray:
    y, sr0 = sf.read(path, always_2d=False)
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr0 != sr:
        y = librosa.resample(y, orig_sr=sr0, target_sr=sr)
    return y.astype(np.float32)


# ---- embedders -----------------------------------------------------------

def embed_vggish(files):
    """VGGish: produces a 128-d embedding per 0.96-s frame."""
    import torch
    import torchvggish
    model = torchvggish.vggish()
    model.eval()
    out = []
    for f in tqdm(files, desc="vggish"):
        wav = load_wav(f, 16000)
        with torch.no_grad():
            emb = model.forward(torch.from_numpy(wav), fs=16000)
        out.append(emb.numpy().reshape(-1, 128))
    return np.concatenate(out, axis=0)


def embed_openl3(files):
    """OpenL3: 512-d music-trained embedding."""
    import openl3
    out = []
    for f in tqdm(files, desc="openl3"):
        wav = load_wav(f, 48000)
        emb, _ = openl3.get_audio_embedding(
            wav, 48000, content_type="music", embedding_size=512, hop_size=1.0)
        out.append(emb)
    return np.concatenate(out, axis=0)


EMBEDDERS = {"vggish": embed_vggish, "openl3": embed_openl3}


# ---- FAD -----------------------------------------------------------------

def frechet_distance(a: np.ndarray, b: np.ndarray) -> float:
    """μ/Σ-based gaussian distance; symmetric and ≥0."""
    from scipy.linalg import sqrtm
    mu_a, mu_b = a.mean(0), b.mean(0)
    cov_a = np.cov(a, rowvar=False) + 1e-6 * np.eye(a.shape[1])
    cov_b = np.cov(b, rowvar=False) + 1e-6 * np.eye(b.shape[1])
    cov_prod = sqrtm(cov_a @ cov_b)
    if np.iscomplexobj(cov_prod):
        cov_prod = cov_prod.real
    diff = mu_a - mu_b
    return float(diff @ diff + np.trace(cov_a + cov_b - 2 * cov_prod))


# ---- main ---------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True, help="dir of generated wavs (one .wav per sample)")
    ap.add_argument("--ref", required=True, help="dir of reference wavs")
    ap.add_argument("--embedder", choices=list(EMBEDDERS.keys()), default="vggish")
    ap.add_argument("--groups", default="",
                    help="optional: filename-prefix groups, e.g. 'A_=A_baseline,B_=B_va'")
    ap.add_argument("--out", default="fad_real.json")
    args = ap.parse_args()

    gen_files = sorted(Path(args.gen).glob("*.wav"))
    ref_files = sorted(Path(args.ref).rglob("*.wav"))
    assert gen_files, f"no wavs in {args.gen}"
    assert ref_files, f"no wavs in {args.ref}"
    print(f"[1/3] gen {len(gen_files)} | ref {len(ref_files)}")

    embed_fn = EMBEDDERS[args.embedder]
    print(f"[2/3] embedding ref")
    ref_emb = embed_fn(ref_files)
    print(f"      ref embeddings: {ref_emb.shape}")

    if not args.groups:
        groups = [(None, "ALL", gen_files)]
    else:
        groups = []
        for spec in args.groups.split(","):
            prefix, name = spec.split("=")
            sub = [f for f in gen_files if f.name.startswith(prefix)]
            groups.append((prefix, name, sub))

    out_groups = []
    for prefix, name, sub in groups:
        if not sub:
            continue
        print(f"[3/3] group {name} ({len(sub)})")
        sub_emb = embed_fn(sub)
        fad = frechet_distance(sub_emb, ref_emb)
        out_groups.append({"name": name, "n": len(sub), "fad": fad})
        print(f"      FAD={fad:.3f}")

    result = {"embedder": args.embedder,
              "ref_dir": str(Path(args.ref).resolve()),
              "n_ref": len(ref_files),
              "groups": out_groups}
    if len(out_groups) >= 2:
        result[f"delta_{out_groups[-1]['name']}_minus_{out_groups[0]['name']}"] = \
            out_groups[-1]["fad"] - out_groups[0]["fad"]
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
