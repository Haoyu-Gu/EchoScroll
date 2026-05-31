"""EchoScroll M9 · Objective evaluation metrics.

Pure analysis code. No cross-module imports. CPU-only.

Functions
---------
- va_consistency(painting_va, audio_va)            : Pearson correlation on (B, 2) V-A arrays.
- fad(gen_embeddings, ref_embeddings)              : Frechet-Audio-Distance style metric on embedding arrays.
- extract_embeddings(audio_paths, encoder=...)     : Embedding extractor; default 'random' deterministic fallback.
- prompt_audio_similarity(prompt, audio_path)      : CLAP cosine; mock fallback if laion_clap not installed.
- mir_features(audio_path)                         : librosa-based tempo / key / spectral features.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


# =====================================================================
# 1. V-A consistency
# =====================================================================

def va_consistency(painting_va: np.ndarray, audio_va: np.ndarray) -> float:
    """Pearson correlation between two (B, 2) V-A arrays.

    The two channels (valence, arousal) are flattened and Pearson correlation
    is computed across the joint vector. Higher = better alignment.

    Returns NaN for degenerate inputs (constant series).
    """
    p = np.asarray(painting_va, dtype=np.float64).reshape(-1)
    a = np.asarray(audio_va, dtype=np.float64).reshape(-1)
    if p.shape != a.shape:
        raise ValueError(f"shape mismatch: {p.shape} vs {a.shape}")
    if p.size < 2:
        return float("nan")
    p_std = p.std()
    a_std = a.std()
    if p_std < 1e-12 or a_std < 1e-12:
        return float("nan")
    return float(np.corrcoef(p, a)[0, 1])


# =====================================================================
# 2. FAD-like distributional distance
# =====================================================================

def _matrix_sqrt_psd(mat: np.ndarray) -> np.ndarray:
    """Symmetric matrix square root via eigendecomposition (PSD safe)."""
    sym = (mat + mat.T) / 2.0
    w, v = np.linalg.eigh(sym)
    w = np.clip(w, 0.0, None)
    return (v * np.sqrt(w)) @ v.T


def fad(gen_embeddings: np.ndarray, ref_embeddings: np.ndarray) -> float:
    """Frechet-Audio-Distance style distributional distance.

        FAD = ||mu_g - mu_r||^2 + tr(Sigma_g + Sigma_r - 2 (Sigma_g Sigma_r)^{1/2})

    Inputs are (N, D) embedding matrices (e.g., VGGish, OpenL3, or the
    random-projection fallback in `extract_embeddings`).
    """
    g = np.asarray(gen_embeddings, dtype=np.float64)
    r = np.asarray(ref_embeddings, dtype=np.float64)
    if g.ndim != 2 or r.ndim != 2:
        raise ValueError("embeddings must be 2-D (N, D)")
    if g.shape[1] != r.shape[1]:
        raise ValueError(f"feature dim mismatch: {g.shape[1]} vs {r.shape[1]}")

    mu_g = g.mean(axis=0)
    mu_r = r.mean(axis=0)
    sig_g = np.cov(g, rowvar=False) if g.shape[0] > 1 else np.zeros((g.shape[1], g.shape[1]))
    sig_r = np.cov(r, rowvar=False) if r.shape[0] > 1 else np.zeros((r.shape[1], r.shape[1]))

    # numerical safety
    eps = 1e-6 * np.eye(sig_g.shape[0])
    sig_g = sig_g + eps
    sig_r = sig_r + eps

    diff = mu_g - mu_r
    cov_prod = _matrix_sqrt_psd(sig_g @ sig_r)
    # the eigh-based sqrt above already enforces PSD; take real part defensively
    cov_prod = np.real(cov_prod)
    score = float(diff @ diff + np.trace(sig_g + sig_r - 2.0 * cov_prod))
    # FAD is defined to be non-negative; clip tiny negative numerical noise.
    return max(score, 0.0)


# =====================================================================
# 2b. Embedding extractor (random-projection fallback)
# =====================================================================

def _load_audio_mono(path: str | Path, sr: int = 16000):
    """Load mono audio at `sr`. Try librosa; if missing, fall back to scipy.io.wavfile."""
    path = str(path)
    try:
        import librosa  # type: ignore

        y, _ = librosa.load(path, sr=sr, mono=True)
        return np.asarray(y, dtype=np.float32)
    except Exception:
        from scipy.io import wavfile  # type: ignore

        rate, data = wavfile.read(path)
        y = data.astype(np.float32)
        if y.ndim > 1:
            y = y.mean(axis=1)
        if np.issubdtype(data.dtype, np.integer):
            y = y / float(np.iinfo(data.dtype).max)
        # naive resample if needed
        if rate != sr:
            n_target = int(round(len(y) * sr / rate))
            if n_target > 1:
                xp = np.linspace(0.0, 1.0, num=len(y), endpoint=False)
                xq = np.linspace(0.0, 1.0, num=n_target, endpoint=False)
                y = np.interp(xq, xp, y).astype(np.float32)
        return y


def _logmel_frames(y: np.ndarray, sr: int = 16000, n_mels: int = 64) -> np.ndarray:
    """Return (n_mels,) mean log-mel vector. librosa preferred, else STFT fallback."""
    try:
        import librosa  # type: ignore

        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
        logmel = np.log1p(mel).mean(axis=1)
        return logmel.astype(np.float32)
    except Exception:
        # Minimal STFT magnitude average as a stand-in.
        n_fft = 512
        hop = 256
        if len(y) < n_fft:
            y = np.pad(y, (0, n_fft - len(y)))
        n_frames = 1 + (len(y) - n_fft) // hop
        win = np.hanning(n_fft).astype(np.float32)
        spec = np.empty((n_fft // 2 + 1, n_frames), dtype=np.float32)
        for i in range(n_frames):
            seg = y[i * hop : i * hop + n_fft] * win
            spec[:, i] = np.abs(np.fft.rfft(seg))
        # bin into n_mels groups
        bins = np.linspace(0, spec.shape[0], n_mels + 1, dtype=int)
        out = np.zeros(n_mels, dtype=np.float32)
        for i in range(n_mels):
            lo, hi = bins[i], max(bins[i + 1], bins[i] + 1)
            out[i] = np.log1p(spec[lo:hi].mean())
        return out


def _random_projection_embed(y: np.ndarray, sr: int, dim: int = 128) -> np.ndarray:
    """Deterministic random-projection embedding.

    Mean log-mel (n_mels=64) projected through a *fixed* Gaussian matrix
    seeded by a constant, so the same audio always maps to the same vector.
    """
    feats = _logmel_frames(y, sr=sr, n_mels=64)
    rng = np.random.default_rng(seed=20260513)
    proj = rng.standard_normal(size=(feats.shape[0], dim)).astype(np.float32)
    emb = feats @ proj
    norm = np.linalg.norm(emb) + 1e-9
    return (emb / norm).astype(np.float32)


def extract_embeddings(
    audio_paths: Sequence[str | Path],
    encoder: str = "random",
    dim: int = 128,
    sr: int = 16000,
) -> np.ndarray:
    """Extract (N, D) embeddings for a list of audio files.

    Supported encoders:
      - 'random'  : deterministic mean-log-mel + fixed Gaussian projection (always available).
      - 'vggish'  : attempt torchvggish; on failure, fall back to 'random'.
      - 'openl3'  : attempt openl3; on failure, fall back to 'random'.

    The fallback keeps the MacBook demo always-runnable.
    """
    paths = [Path(p) for p in audio_paths]
    if not paths:
        return np.zeros((0, dim), dtype=np.float32)

    if encoder == "vggish":
        try:
            import torch  # type: ignore
            from torchvggish import vggish, vggish_input  # type: ignore

            model = vggish()
            model.eval()
            out = []
            with torch.no_grad():
                for p in paths:
                    examples = vggish_input.wavfile_to_examples(str(p))
                    feats = model(examples)
                    out.append(feats.mean(dim=0).cpu().numpy())
            return np.stack(out, axis=0).astype(np.float32)
        except Exception:
            encoder = "random"

    if encoder == "openl3":
        try:
            import openl3  # type: ignore
            import soundfile as sf  # type: ignore

            out = []
            for p in paths:
                y, file_sr = sf.read(str(p))
                if y.ndim > 1:
                    y = y.mean(axis=1)
                emb, _ = openl3.get_audio_embedding(y, file_sr, content_type="music")
                out.append(emb.mean(axis=0))
            return np.stack(out, axis=0).astype(np.float32)
        except Exception:
            encoder = "random"

    # 'random' fallback (and unknown encoders default here)
    embs = []
    for p in paths:
        y = _load_audio_mono(p, sr=sr)
        embs.append(_random_projection_embed(y, sr=sr, dim=dim))
    return np.stack(embs, axis=0).astype(np.float32)


# =====================================================================
# 3. CLAP-style prompt-audio similarity
# =====================================================================

def _hash_unit_vector(text: str, dim: int = 128) -> np.ndarray:
    """Deterministic unit vector from a string (mock CLAP text embedding)."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big", signed=False) % (2**32 - 1)
    rng = np.random.default_rng(seed=seed)
    v = rng.standard_normal(size=dim).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def prompt_audio_similarity(prompt: str, audio_path: str | Path) -> float:
    """Cosine similarity in [-1, 1] between a text prompt and an audio file.

    Tries LAION-CLAP first; if `laion_clap` is unavailable (or the model
    cannot be loaded), falls back to a deterministic hashed-string-vs-audio
    mock similarity. The mock is *not* meaningful as a research metric — it
    is only here so the demo always runs on a MacBook with no extra weights.
    See README.md for details.
    """
    audio_path = str(audio_path)
    try:
        import laion_clap  # type: ignore
        import torch  # type: ignore

        model = laion_clap.CLAP_Module(enable_fusion=False)
        model.load_ckpt()  # downloads default checkpoint
        with torch.no_grad():
            audio_emb = model.get_audio_embedding_from_filelist(x=[audio_path], use_tensor=False)
            text_emb = model.get_text_embedding([prompt], use_tensor=False)
        a = audio_emb[0]
        t = text_emb[0]
        a = a / (np.linalg.norm(a) + 1e-9)
        t = t / (np.linalg.norm(t) + 1e-9)
        return float(np.dot(a, t))
    except Exception:
        # mock fallback
        y = _load_audio_mono(audio_path, sr=16000)
        audio_vec = _random_projection_embed(y, sr=16000, dim=128)
        text_vec = _hash_unit_vector(prompt, dim=128)
        return float(np.dot(audio_vec, text_vec))


# =====================================================================
# 4. MIR features
# =====================================================================

_PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# Krumhansl-Kessler major/minor profiles (rough key estimation)
_KK_MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_KK_MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)


def _estimate_key(chroma_mean: np.ndarray) -> str:
    """Rough key estimate: best-correlated rotation of major/minor KK profile."""
    chroma = chroma_mean / (chroma_mean.sum() + 1e-9)
    best = ("C", "major", -np.inf)
    for mode_name, profile in (("major", _KK_MAJOR), ("minor", _KK_MINOR)):
        p = profile / profile.sum()
        for i in range(12):
            rotated = np.roll(p, i)
            # correlation
            corr = np.corrcoef(chroma, rotated)[0, 1]
            if not np.isfinite(corr):
                continue
            if corr > best[2]:
                best = (_PITCH_CLASSES[i], mode_name, corr)
    return f"{best[0]} {best[1]}"


def mir_features(audio_path: str | Path) -> dict:
    """Basic MIR features via librosa.

    Returns
    -------
    dict with keys: tempo, key, spectral_centroid_mean, spectral_bandwidth_mean,
    rms_energy_mean, zero_crossing_rate_mean.
    """
    import librosa  # required for this function

    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    if y.size == 0:
        return {
            "tempo": 0.0,
            "key": "unknown",
            "spectral_centroid_mean": 0.0,
            "spectral_bandwidth_mean": 0.0,
            "rms_energy_mean": 0.0,
            "zero_crossing_rate_mean": 0.0,
        }

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key = _estimate_key(chroma_mean)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()
    rms = librosa.feature.rms(y=y).mean()
    zcr = librosa.feature.zero_crossing_rate(y=y).mean()

    return {
        "tempo": float(np.asarray(tempo).reshape(-1)[0]),
        "key": key,
        "spectral_centroid_mean": float(centroid),
        "spectral_bandwidth_mean": float(bandwidth),
        "rms_energy_mean": float(rms),
        "zero_crossing_rate_mean": float(zcr),
    }


__all__ = [
    "va_consistency",
    "fad",
    "extract_embeddings",
    "prompt_audio_similarity",
    "mir_features",
]
