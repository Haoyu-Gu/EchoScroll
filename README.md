# EchoScroll

> **Where Chinese Painting Listens to Itself.**
> 让中国画自己讲述它的音乐。
>
> An end-to-end pipeline that maps a Chinese painting to a piece of generated music conditioned on its visual semantics, art-historical context, and emotional geometry — instead of falling back to a flat "Chinese style" tag.

**Live demo (presentation):** https://haoyu-gu.github.io/EchoScroll/
**Live demo (creation preview, design-school aligned):** https://haoyu-gu.github.io/EchoScroll/creation/

---

## What is EchoScroll

EchoScroll is a 9-module research system that aligns a painting's visual content, its art-historical context, and Russell-style valence–arousal coordinates in a shared latent space, then conditions a fine-tuned MusicGen-small to produce music with matching mood, mode, tempo, instrumentation, and dynasty cues. Every stage is interactive: drag a V–A point and the music re-conditions; hum a motif and the system re-pitches the output to your key.

Built for the AI Systems Integrated Design course, Spring 2026 — but written to stand on its own.

---

## Repository layout

```
EchoScroll/
├── README.md                  this file
├── echoscroll/                main pipeline · 9 modules · ~9,400 LOC Python
│   ├── M1_multimodal_encoder/   CLIP-ViT-L/14 + BGE-M3 + metadata fusion
│   ├── M2_affective_projection/ MLP 768→256→2 onto Russell V–A circumplex
│   ├── M3_art_rag/              Art-history RAG over 1,129 chunks
│   ├── M4_music_generator/      MusicGen-small + 8-slot V–A conditioning
│   ├── M5_editing_layer/        BPM / segment / fade edits (librosa, CPU)
│   ├── M6_prompt_translator/    V–A + descriptors → MusicGen text prompt
│   ├── M7_humming_interaction/  pYIN + DTW key alignment for humming input
│   ├── M8_frontend_backend/     FastAPI + React seed for the full UI
│   ├── M9_evaluation/           FAD + human-rating + summary metrics
│   ├── scripts/                 end-to-end integration smoke + builders
│   └── *.py / *.md              gallery, painting unification, READMEs
├── docs/                      single-page demo (HTML + CSS + JS, no backend)
│   └── this is what GitHub Pages serves at /
├── training_tasks/            7 GPU baking scripts (T1–T7) for the server
└── extras/                    演示物料 / 数据集 / 音频配对 中文文档
```

| Part | Files | Lines |
|---|---|---|
| `echoscroll/` Python | 38 `.py` | 9,416 |
| `docs/` (demo HTML/CSS/JS) | 3 files | 6,716 |
| `training_tasks/` Python | 13 `.py` | 1,256 |
| Documentation (MD) | ~20 files | ~3,800 |
| **Total** | — | **~21,000 lines** |

---

## Quick start

### 1 · Open the demo (zero install)

In your browser: **https://haoyu-gu.github.io/EchoScroll/**

Or locally:
```bash
cd docs
python3 -m http.server 8080
# open http://localhost:8080
```

The demo runs entirely client-side: V–A dragging, real-music swap, full-length playback, prompt inspection, Concert Mode auto-tour — no server needed. It bundles 4 real MusicGen-generated tracks (paintings `p1` and `p5`) plus 7 procedural mock variants so that interactions stay responsive.

### 2 · Run the main pipeline (CPU)

Each module ships a self-contained `demo.py` that runs in seconds without GPU:

```bash
cd echoscroll
pip install -r requirements.txt   # if you have one; otherwise install per-module deps
python -m M1_multimodal_encoder.demo
python -m M2_affective_projection.demo
python -m M3_art_rag.demo
# ...etc
```

End-to-end smoke test (touches every module):
```bash
python -m scripts.integration_smoke
```

### 3 · Reproduce the music samples (GPU)

`training_tasks/T7_demo_batch_generate/` produces all 48 demo audios on a single A100 / 4090 in about 1 hour:
```bash
cd training_tasks/T7_demo_batch_generate
pip install -r requirements.txt
python batch_generate.py \
    --paintings-json paintings.json \
    --adapter /path/to/T3/lora_checkpoint \
    --duration 16 \
    --out audio/
```

For the full baking pipeline (V–A training → MusicGen LoRA → RAG indexing → FAD eval), see `training_tasks/README.md` and `extras/数据集与训练任务说明书.md`.

---

## The 9 modules at a glance

| ID | Cn / En | What it does | Key file |
|---|---|---|---|
| **M1** | 多模态编码 · Multimodal Encoder | Visual (CLIP-ViT-L/14) + bilingual text (BGE-M3) + metadata hash → 768-d fused embedding | `M1_multimodal_encoder/encoder.py` |
| **M2** | 情感投影 · Affective Projection | MLP 768→256→2 onto Russell V–A circumplex, MSE + NT-Xent joint supervision | `M2_affective_projection/projection.py` |
| **M3** | 艺术史 RAG · Art-history Retrieval | Top-k retrieval over 1,129 expert-written art chunks; 8 dataset subsets | `M3_art_rag/rag_store.py` |
| **M4** | 音乐生成 · Music Generator | MusicGen-small + 8-slot V–A conditioning + optional LoRA | `M4_music_generator/generator.py` |
| **M5** | 编辑层 · Editing Layer | librosa phase-vocoder BPM, segment replacement, crossfade — CPU only | `M5_editing_layer/editor.py` |
| **M6** | Prompt 翻译 · Prompt Translator | V–A + descriptors → natural-language MusicGen prompt | `M6_prompt_translator/translator.py` |
| **M7** | 哼唱交互 · Humming Interaction | pYIN F0 extraction + DTW key alignment on user-hummed motifs | `M7_humming_interaction/humming.py` |
| **M8** | 前后端 · Frontend / Backend | FastAPI server + React seed for the full interactive UI | `M8_frontend_backend/backend/main.py` |
| **M9** | 评测 · Evaluation | FAD baseline, Likert human-rating forms, aggregated metrics | `M9_evaluation/metrics.py` |

Each `M*/` follows the same shape: `<main>.py + viz.py + demo.py + README.md + figures/`.

---

## The demo

The `docs/` folder is a single-page showcase site with **no build step and no backend**. The whole experience — V–A dragging, real-music swap, descriptors, RAG cards, the 8-painting atlas, the module topology, dataflow diagram, and Concert Mode auto-tour — runs from one HTML, one CSS, one JS.

Highlights:

- **Interactive V–A circumplex** — drag the pin around Russell's valence–arousal space, watch descriptors and the prompt-translator output update live, and have the player auto-swap to the nearest pre-baked audio variant.
- **Real-music note panel** — when you select paintings `p1` (Mi Youren · *Cloudy Mountains*) or `p5` (Bada Shanren · *Landscape after Guo Zhongshu*), a green badge appears: these are **real** MusicGen-LoRA outputs, not synthesized previews. Click *完整聆听 · 4:48* to play the full 5-minute track; click *▾ 看 prompt* to inspect the exact MusicGen prompt that produced it.
- **题跋 · 因人而读** — four audience-specific entry cards (答辩老师 30s, 美术馆策展 1min, 古典音乐学者 2min, 美术学生 5s) that pivot the same project for different readers.
- **Concert Mode** — clicks through all 8 paintings on a 12-second timer with crossfaded audio, for unattended kiosk-style display.

The full Python pipeline is **not** invoked at runtime by the demo. All data (V–A coordinates, descriptors, RAG snippets, prompts) is inlined into `app.js` so that the demo runs offline on any laptop without GPU or network.

---

## Documentation

| File | What's inside |
|---|---|
| `echoscroll/RESULTS.md` | Headline metrics, FAD, per-module results |
| `echoscroll/MODULES.md` | Deep dive per module, with formulas and signatures |
| `echoscroll/SHOWCASE.md` | Eight-painting case studies |
| `echoscroll/CONVENTIONS.md` | Codebase conventions (file shapes, naming, etc.) |
| `extras/数据集与训练任务说明书.md` | Full dataset catalog and GPU job specs (中文) |
| `extras/演示物料清单.md` | Live-demo material list and failure recovery plan |
| `extras/Demo音频样本与配对.md` | What audio samples the demo needs and how they pair |

---

## Status

- ✅ All 9 modules pass `scripts/integration_smoke.py` on CPU with mocks
- ✅ Demo deployed to GitHub Pages
- ✅ 4 real MusicGen-LoRA samples (paintings p1 and p5) bundled into the demo
- ⏳ Remaining 36 of 48 planned real samples — pending GPU run of `T7_demo_batch_generate`
- ⏳ T1 (V–A training), T3 (LoRA), T5 (FAD eval) — pending GPU server slot

---

## Course context

AI Systems Integrated Design · Spring 2026 · Group 5.
This repo packages the implementation and the demo. The 1,441-line LaTeX final report is delivered separately.

---

## License

MIT. See `LICENSE`.
