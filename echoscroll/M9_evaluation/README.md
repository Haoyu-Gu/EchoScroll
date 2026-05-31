# M9 · Evaluation

Objective + subjective evaluation for EchoScroll soundtracks (see proposal §3.2.6, §3.3.3).
Hybrid protocol: blinded human rating is the primary evidence, objective metrics are auxiliary.

## What's here

- `metrics.py` — V-A consistency, FAD-like distance, prompt-audio similarity (CLAP), basic MIR features.
- `human_rating.py` — Pydantic schema, CSV harness, per-system aggregation, blinding helper.
- `demo.py` — synthesises 2 fake "systems" of 10 × 1 s noise clips, runs every metric, writes a 12-row fake-rating CSV, prints a results table. Runs on CPU with no extra weights.
- `requirements.txt` — `numpy scipy librosa pydantic pandas scikit-learn` (CLAP / OpenL3 / VGGish are optional).

## Metric-by-metric prerequisites

| Function | Needs | Fallback |
| --- | --- | --- |
| `va_consistency` | numpy | none needed |
| `fad` + `extract_embeddings(encoder='random')` | numpy | always-on (deterministic random projection of mean log-mel) |
| `extract_embeddings(encoder='vggish' / 'openl3')` | `torchvggish` / `openl3` | silently falls back to `'random'` if import fails |
| `prompt_audio_similarity` | `laion_clap` checkpoint | hashed-string-vs-audio mock cosine — **not a research metric**, demo-only |
| `mir_features` | `librosa` | none — required |

## Human-rating CSV columns

| column | type | meaning |
| --- | --- | --- |
| `painting_id` | str | identifier of the painting shown to the rater |
| `system_label` | str | blinded system label (A / B / C / …); resolve via `blind_pair_template().blinding_map` |
| `painting_music_relevance` | int 1-5 | does the music match the painting? |
| `emotional_consistency` | int 1-5 | does the music's affect match the painting's affect? |
| `cultural_appropriateness` | int 1-5 | does the music fit the Chinese-painting cultural context? |
| `audio_quality` | int 1-5 | technical audio quality (fluency, clarity) |
| `overall_preference` | int 1-5 | overall preference |

`aggregate(csv_path)` returns per-system and pooled `mean / std / n` for every Likert dimension.
`blind_pair_template(painting_path, system_audios)` produces one rater-facing JSON row with the
system→label mapping kept separately for the experimenter.

## Running

```bash
pip install -r requirements.txt
python demo.py
```

The demo writes everything to a temp directory and prints the table to stdout.
