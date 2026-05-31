"""EchoScroll M9 · Human-rating harness.

Pydantic schema + CSV I/O + per-system aggregation, plus a helper that
produces a blinded JSON row suitable for handing to a human rater.

Schema (HumanRatingForm)
------------------------
- painting_id                     : str
- system_label                    : str  (A / B / C — blinded; resolve via mapping)
- painting_music_relevance        : int  (1-5)
- emotional_consistency           : int  (1-5)
- cultural_appropriateness        : int  (1-5)
- audio_quality                   : int  (1-5)
- overall_preference              : int  (1-5)
"""

from __future__ import annotations

import json
import random
import string
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
from pydantic import BaseModel, Field, field_validator


# =====================================================================
# Pydantic schema
# =====================================================================

class HumanRatingForm(BaseModel):
    """One rater's response for one (painting, system) pair."""

    painting_id: str
    system_label: str = Field(..., description="Blinded label, e.g. 'A', 'B', 'C'")
    painting_music_relevance: int = Field(..., ge=1, le=5)
    emotional_consistency: int = Field(..., ge=1, le=5)
    cultural_appropriateness: int = Field(..., ge=1, le=5)
    audio_quality: int = Field(..., ge=1, le=5)
    overall_preference: int = Field(..., ge=1, le=5)

    @field_validator("system_label")
    @classmethod
    def _label_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("system_label must be non-empty")
        return v.strip()


RATING_FIELDS = (
    "painting_music_relevance",
    "emotional_consistency",
    "cultural_appropriateness",
    "audio_quality",
    "overall_preference",
)


CSV_COLUMNS = ("painting_id", "system_label", *RATING_FIELDS)


# =====================================================================
# CSV harness
# =====================================================================

def to_csv(records: Iterable[HumanRatingForm | dict], path: str | Path) -> Path:
    """Write a list of HumanRatingForm (or dict) records to CSV.

    The CSV header always matches `CSV_COLUMNS`. Dict inputs are validated
    through `HumanRatingForm` before being written.
    """
    path = Path(path)
    rows = []
    for r in records:
        if isinstance(r, HumanRatingForm):
            rows.append(r.model_dump())
        else:
            rows.append(HumanRatingForm(**r).model_dump())
    df = pd.DataFrame(rows, columns=list(CSV_COLUMNS))
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def aggregate(csv_path: str | Path) -> dict:
    """Return per-system mean +/- std for every Likert dimension.

    Output shape::

        {
          "A": {
            "painting_music_relevance":  {"mean": ..., "std": ..., "n": ...},
            "emotional_consistency":     {...},
            ...
          },
          "B": {...},
          ...
          "_overall": { same fields, pooled across all rows }
        }
    """
    df = pd.read_csv(csv_path)
    missing = [c for c in CSV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    out: dict = {}
    for system_label, group in df.groupby("system_label"):
        out[str(system_label)] = {
            field: {
                "mean": float(group[field].mean()),
                "std": float(group[field].std(ddof=1)) if len(group) > 1 else 0.0,
                "n": int(len(group)),
            }
            for field in RATING_FIELDS
        }

    out["_overall"] = {
        field: {
            "mean": float(df[field].mean()),
            "std": float(df[field].std(ddof=1)) if len(df) > 1 else 0.0,
            "n": int(len(df)),
        }
        for field in RATING_FIELDS
    }
    return out


# =====================================================================
# Blinding helper
# =====================================================================

def blind_pair_template(
    painting_path: str | Path,
    system_audios: dict[str, str | Path],
    seed: int | None = None,
) -> dict:
    """Produce one rater-facing JSON row: painting + shuffled blinded audios.

    Parameters
    ----------
    painting_path  : path to the painting image shown to the rater.
    system_audios  : mapping `system_name -> audio_path`. The system names
                     are hidden behind blinded labels A, B, C, ... in the
                     order produced by a deterministic shuffle.
    seed           : optional seed for the shuffle (per-painting reproducibility).

    Returns
    -------
    dict with::

        {
          "painting_id":   str,        # derived from filename
          "painting_path": str,
          "samples":       [{"label": "A", "audio_path": "..."}, ...],
          "blinding_map":  {"A": "system_name", ...}   # rater MUST NOT see this
        }
    """
    painting_path = Path(painting_path)
    items = list(system_audios.items())
    rng = random.Random(seed)
    rng.shuffle(items)

    labels = list(string.ascii_uppercase)
    if len(items) > len(labels):
        raise ValueError(f"too many systems for single-letter blinding ({len(items)})")

    samples = []
    blinding_map = {}
    for label, (system_name, audio_path) in zip(labels, items):
        samples.append({"label": label, "audio_path": str(audio_path)})
        blinding_map[label] = system_name

    return {
        "painting_id": painting_path.stem,
        "painting_path": str(painting_path),
        "samples": samples,
        "blinding_map": blinding_map,
    }


def write_blind_pair(template: dict, path: str | Path) -> Path:
    """Write a blind-pair template to disk as JSON (utility)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


__all__ = [
    "HumanRatingForm",
    "RATING_FIELDS",
    "CSV_COLUMNS",
    "to_csv",
    "aggregate",
    "blind_pair_template",
    "write_blind_pair",
]
