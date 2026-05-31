"""End-to-end smoke test that touches every module on a REAL painting.

NOT a production integration — but proves the pipeline shape composes:
  unified painting → M2 (random-init) → V-A → M6 (rule) → 8-slot → M4 (mock) → wav
  + M3 (mock embed) retrieval against real RAG corpus chunks
  + M5 BPM stretch on the produced wav
  + M9 metric on the result

Output:
  scripts/out/integration_smoke/
      painting_metadata.json
      retrieved_chunks.json
      descriptors.json
      va.json
      soundtrack.wav
      soundtrack_slow.wav
      metrics.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/echoscroll")
DATA = Path("/Users/guhaoyu/Desktop/总文件夹/2026春/人工智能系统综合设计/开题/EchoScroll_data_plan/data")
OUT_DIR = ROOT / "scripts" / "out" / "integration_smoke"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# import the modules directly via sys.path (allowed for smoke-test ONLY;
# modules themselves stay isolated as per CONVENTIONS.md)
for m in ("M2_affective_projection", "M4_music_generator", "M5_editing_layer",
          "M6_prompt_translator", "M9_evaluation"):
    sys.path.insert(0, str(ROOT / m))


def pick_painting() -> dict:
    df = pd.read_parquet(DATA / "processed/paintings_unified.parquet")
    # prefer one with a real dynasty + cleveland (richer description)
    candidates = df[df["source"].eq("cleveland") & df["dynasty"].notna()]
    row = candidates.iloc[0].to_dict() if len(candidates) else df.iloc[0].to_dict()
    return row


def rag_query_against_real_corpus(painting: dict, top_k: int = 5) -> list[dict]:
    """Use a tiny hash-based mock embedder against the just-built data/rag/chunks.jsonl."""
    chunks_path = DATA / "rag" / "chunks.jsonl"
    if not chunks_path.exists():
        return []
    chunks = []
    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    def hashvec(text: str, dim: int = 64) -> np.ndarray:
        rng = np.random.default_rng(hash(text) % (2 ** 32))
        v = rng.standard_normal(dim).astype(np.float32)
        v /= np.linalg.norm(v) + 1e-12
        return v

    q_text = " ".join(filter(None, [painting.get("title"), painting.get("artist"),
                                    painting.get("dynasty"), painting.get("description")]))
    q = hashvec(q_text)
    scored = []
    for c in chunks:
        score = float(np.dot(q, hashvec(c["text"])))
        scored.append((score, c))
    scored.sort(reverse=True, key=lambda kv: kv[0])
    return [{"score": s, **c} for s, c in scored[:top_k]]


def m2_predict_va(painting: dict) -> tuple[float, float]:
    import torch
    from projection import AffectiveProjection, va_to_word
    model = AffectiveProjection(in_dim=768, hidden_dim=256).eval()
    # synthesize a deterministic z from painting id so re-runs are stable
    rng = np.random.default_rng(hash(painting["id"]) % (2 ** 32))
    z = torch.from_numpy(rng.standard_normal((1, 768)).astype(np.float32))
    with torch.no_grad():
        v, a = model(z)
    v_f, a_f = float(v.item()), float(a.item())
    return v_f, a_f, va_to_word(v_f, a_f)


def m6_translate_state(state: dict) -> dict:
    from translator import RuleBasedTranslator
    t = RuleBasedTranslator()
    user_text = "make it more contemplative, ancient style with guqin"
    out = t.translate(user_text, current_state=state)
    return out


def m4_generate(va: tuple[float, float], descriptors: dict, retrieved: list[dict]) -> tuple[np.ndarray, int, str]:
    from generator import MockMusicGenerator, build_prompt
    gen = MockMusicGenerator()
    ctx_texts = [r["text"] for r in retrieved[:3]]
    condition = {
        "text_prompt": "Chinese landscape painting soundtrack",
        "va": va,
        "retrieved_context": ctx_texts,
        "duration_s": 8,
        "control_descriptors": descriptors,
    }
    prompt = build_prompt(condition)
    out = gen.generate(condition)
    return out["wav"], out["sample_rate"], prompt


def m5_slow_down(wav: np.ndarray, sr: int) -> np.ndarray:
    import editor
    return editor.change_bpm(wav, sr, src_bpm=120.0, tgt_bpm=80.0)


def m9_quick_metrics(wav: np.ndarray, sr: int, prompt: str) -> dict:
    import tempfile, scipy.io.wavfile as wavfile
    from metrics import mir_features, prompt_audio_similarity
    f = OUT_DIR / "soundtrack.wav"
    wavfile.write(f, sr, (wav * 32767).astype(np.int16))
    return {
        "mir_features": mir_features(str(f)),
        "prompt_audio_similarity": prompt_audio_similarity(prompt, str(f)),
    }


def main():
    print("=" * 60)
    print("EchoScroll · End-to-end smoke test")
    print("=" * 60)

    painting = pick_painting()
    print(f"\nPicked painting: {painting.get('id')}  '{painting.get('title')}'  ({painting.get('dynasty')})")
    (OUT_DIR / "painting_metadata.json").write_text(
        json.dumps({k: (v if not pd.isna(v) else None) for k, v in painting.items()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # --- M3-style RAG retrieval against real corpus ---
    retrieved = rag_query_against_real_corpus(painting)
    print(f"\nM3 RAG top-5 from {len(open(DATA / 'rag/chunks.jsonl').readlines())} chunks:")
    for r in retrieved:
        snippet = r["text"][:80].replace("\n", " ")
        print(f"  score={r['score']:.3f}  src={r['source']}  '{snippet}'")
    (OUT_DIR / "retrieved_chunks.json").write_text(
        json.dumps(retrieved, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    # --- M2 V-A prediction ---
    v, a, word = m2_predict_va(painting)
    print(f"\nM2 predicted V-A: ({v:+.3f}, {a:+.3f}) → {word}")
    (OUT_DIR / "va.json").write_text(
        json.dumps({"valence": v, "arousal": a, "word": word}, indent=2), encoding="utf-8",
    )

    # --- M6 prompt translator ---
    descriptors = m6_translate_state({"valence": v, "arousal": a})
    print(f"\nM6 descriptors: tempo={descriptors.get('tempo')}, mode={descriptors.get('mode')}, "
          f"texture={descriptors.get('texture')}, dyn={descriptors.get('dynamics')}, "
          f"inst={descriptors.get('instrumentation')}")
    (OUT_DIR / "descriptors.json").write_text(
        json.dumps(descriptors, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    # --- M4 (mock) music generation ---
    wav, sr, prompt = m4_generate((v, a), descriptors, retrieved)
    print(f"\nM4 generated: {len(wav) / sr:.1f}s @ {sr} Hz")
    print(f"   final prompt: {prompt[:200]}")

    # --- M5 BPM stretch ---
    slow = m5_slow_down(wav, sr)
    import scipy.io.wavfile as wavfile
    wavfile.write(OUT_DIR / "soundtrack_slow.wav", sr, (slow * 32767).astype(np.int16))
    print(f"\nM5 stretched ×1.5 (slowed): {len(slow) / sr:.1f}s")

    # --- M9 quick metrics ---
    metrics = m9_quick_metrics(wav, sr, prompt)
    print(f"\nM9 metrics:")
    print(f"   prompt-audio sim: {metrics['prompt_audio_similarity']:.3f}")
    print(f"   tempo (librosa):   {metrics['mir_features'].get('tempo')}")
    (OUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8",
    )

    print(f"\nAll outputs → {OUT_DIR}")


if __name__ == "__main__":
    main()
