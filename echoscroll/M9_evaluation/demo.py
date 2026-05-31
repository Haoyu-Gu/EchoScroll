"""EchoScroll M9 · End-to-end demo.

Synthesise two fake "systems" (10 short noise wavs each), compute all
objective metrics + a CLAP-style prompt similarity for one clip, fabricate
a 12-row human-rating CSV, aggregate it and print a single results table.

Runs CPU-only on a MacBook with only numpy / scipy / librosa / pandas /
pydantic installed (no laion_clap, no openl3 — those are optional).
"""

from __future__ import annotations

import random
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile

from human_rating import HumanRatingForm, aggregate, blind_pair_template, to_csv
from metrics import (
    extract_embeddings,
    fad,
    mir_features,
    prompt_audio_similarity,
    va_consistency,
)


N_CLIPS_PER_SYSTEM = 10
CLIP_SECONDS = 1.0
SR = 16000
SYSTEMS = ("echoscroll", "baseline")


def _write_fake_clips(out_dir: Path, system: str, n: int, seed: int) -> list[Path]:
    rng = np.random.default_rng(seed=seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        # noise with a faint system-specific drift so embeddings differ slightly
        n_samples = int(CLIP_SECONDS * SR)
        y = rng.standard_normal(n_samples).astype(np.float32) * 0.1
        drift = 0.05 if system == "echoscroll" else -0.05
        t = np.linspace(0, CLIP_SECONDS, n_samples, endpoint=False, dtype=np.float32)
        y = y + drift * np.sin(2 * np.pi * (220.0 if system == "echoscroll" else 180.0) * t)
        # to int16
        y_int = np.clip(y, -1.0, 1.0)
        y_int = (y_int * 32767).astype(np.int16)
        p = out_dir / f"{system}_{i:02d}.wav"
        wavfile.write(p, SR, y_int)
        paths.append(p)
    return paths


def _fake_va(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, size=(n, 2))


def _fake_human_ratings(painting_ids: list[str], system_labels: list[str], seed: int = 0) -> list[HumanRatingForm]:
    """12 rows total, fabricated with random.choice([3, 4, 5])."""
    rng = random.Random(seed)
    rows: list[HumanRatingForm] = []
    # round-robin painting / system, but make sure echoscroll trends slightly higher
    plan = [
        ("p001", "A"), ("p001", "B"),
        ("p002", "A"), ("p002", "B"),
        ("p003", "A"), ("p003", "B"),
        ("p004", "A"), ("p004", "B"),
        ("p005", "A"), ("p005", "B"),
        ("p006", "A"), ("p006", "B"),
    ]
    for painting_id, label in plan:
        rows.append(
            HumanRatingForm(
                painting_id=painting_id,
                system_label=label,
                painting_music_relevance=rng.choice([3, 4, 5]),
                emotional_consistency=rng.choice([3, 4, 5]),
                cultural_appropriateness=rng.choice([3, 4, 5]),
                audio_quality=rng.choice([3, 4, 5]),
                overall_preference=rng.choice([3, 4, 5]),
            )
        )
    return rows


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="echoscroll_m9_demo_") as tmp:
        tmp_dir = Path(tmp)
        echo_dir = tmp_dir / "echoscroll"
        base_dir = tmp_dir / "baseline"

        echo_paths = _write_fake_clips(echo_dir, "echoscroll", N_CLIPS_PER_SYSTEM, seed=11)
        base_paths = _write_fake_clips(base_dir, "baseline", N_CLIPS_PER_SYSTEM, seed=22)

        # ----- Objective metric 1: V-A consistency
        painting_va = _fake_va(N_CLIPS_PER_SYSTEM, seed=1)
        echo_va = painting_va + np.random.default_rng(7).normal(scale=0.1, size=painting_va.shape)
        base_va = np.random.default_rng(13).uniform(-1, 1, size=painting_va.shape)
        va_echo = va_consistency(painting_va, echo_va)
        va_base = va_consistency(painting_va, base_va)

        # ----- Objective metric 2: FAD (random-projection embeddings)
        ref_emb = extract_embeddings(echo_paths, encoder="random")
        gen_emb = extract_embeddings(base_paths, encoder="random")
        fad_score = fad(gen_emb, ref_emb)

        # ----- Objective metric 3: CLAP-style prompt-audio similarity
        prompt = "calm guqin melody evoking a misty Song-dynasty landscape"
        clap_echo = prompt_audio_similarity(prompt, echo_paths[0])
        clap_base = prompt_audio_similarity(prompt, base_paths[0])

        # ----- Objective metric 4: MIR features
        try:
            mir_echo = mir_features(echo_paths[0])
            mir_base = mir_features(base_paths[0])
        except Exception as e:
            mir_echo = {"error": f"librosa unavailable: {e}"}
            mir_base = {"error": f"librosa unavailable: {e}"}

        # ----- Blinding helper sanity check
        blind = blind_pair_template(
            painting_path=tmp_dir / "fake_painting.jpg",
            system_audios={"echoscroll": echo_paths[0], "baseline": base_paths[0]},
            seed=42,
        )

        # ----- Human rating harness
        csv_path = tmp_dir / "fake_ratings.csv"
        rows = _fake_human_ratings(
            painting_ids=[f"p{i:03d}" for i in range(1, 7)],
            system_labels=list("AB"),
        )
        to_csv(rows, csv_path)
        agg = aggregate(csv_path)

        # ----- Print results
        print("=" * 72)
        print("EchoScroll M9 · Evaluation demo")
        print("=" * 72)

        obj_table = pd.DataFrame(
            {
                "echoscroll": [va_echo, "—", clap_echo],
                "baseline":   [va_base, "—", clap_base],
                "joint":      ["—", fad_score, "—"],
            },
            index=[
                "V-A consistency (Pearson, higher better)",
                "FAD (gen vs ref, lower better)",
                "CLAP-style prompt similarity (cos, higher better)",
            ],
        )
        print("\n[1] Objective metrics")
        print(obj_table.to_string())

        print("\n[2] MIR features — echoscroll[0]")
        for k, v in mir_echo.items():
            print(f"    {k:>26s} : {v}")
        print("\n[2] MIR features — baseline[0]")
        for k, v in mir_base.items():
            print(f"    {k:>26s} : {v}")

        print("\n[3] Blinded rater template (one painting)")
        for s in blind["samples"]:
            print(f"    label={s['label']}  audio={Path(s['audio_path']).name}")
        print(f"    (blinding_map kept by experimenter: {blind['blinding_map']})")

        print("\n[4] Human-rating aggregation (per blinded system, 12 fabricated rows)")
        for system_label in sorted(k for k in agg if k != "_overall"):
            stats = agg[system_label]
            row = "  ".join(
                f"{field[:18]:<18}={stats[field]['mean']:.2f}+/-{stats[field]['std']:.2f}"
                for field in (
                    "painting_music_relevance",
                    "emotional_consistency",
                    "cultural_appropriateness",
                    "audio_quality",
                    "overall_preference",
                )
            )
            print(f"  system {system_label}: {row}")

        print("\nDemo complete. (All metrics computed on CPU-only fake data.)")


if __name__ == "__main__":
    main()
