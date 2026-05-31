# EchoScroll · Implementation Scripts

依据 `开题/EchoScroll_proposal/main.pdf` §3.2.1–3.2.6 的描述把数据加工到模型可消费的样子，并跑通一次端到端 smoke test。

## 4 个脚本

### 1. `build_rag_corpus.py` —— §3.2.4 Art-history RAG 语料

把 Met + Cleveland 的画作描述抽出来切成 ~500 char 的 chunk，加 dynasty / painter / motif / source 元数据，写到 `data/rag/chunks.jsonl`。

```
met chunks:          230
cleveland chunks:    899
total:              1129
dynasty: Qing 441 / Ming 361 / Southern Song 163 / Yuan 102 / Song 30 / Northern Song 8 / Tang 4
```

→ 这就是论文里说的"50M tokens 中英艺术史语料"的 **博物馆策展文** 那一部分的最小可用形态（~155K tokens 估算）。后续接 BGE-M3 + FAISS 索引就是真 RAG。

### 2. `build_va_labels.py` —— §3.2.3 V-A 训练标签

读 EmoArt-130k `Annotation.json`（132,895 张画的离散 V-A + 12 类情感），用两条规则映射到连续 V-A：
- coarse: `Low/High → ∓0.5`, `Negative/Positive → ∓0.5`
- 偏移: 16 类情感各有一对小偏移（Calm 偏低唤起、Anger 偏高唤起负价等）

输出 `data/annotations/emoart_va_labels.csv`（111 MB，17 列）：
```
top emotions:  Calm 74350 / Excited 20595 / Contentment 20406 / Sad 5827 / Alarmed 5407 …
rows with local image: 7512   ← 9 个 style 的图本地落了
```

→ M2 真训练直接用这份 CSV 当 ground truth。

### 3. `build_audio_captions.py` —— §3.2.2 音乐 caption 模板

给 CCMusic Guzheng_Tech99 / erhu_playing_tech / 13-Dim Music Emotions 三个数据集每条 audio 生成一句结构化 caption（仪器+技法+情感），写到 `data/captions/instrument_captions.jsonl`：

```
guzheng: 99 条    (按 7 类古筝技法分别给 caption)
erhu:    1253 条  (按 7 类弓法分别给 caption)
13-dim:  1841 条  (按 top-2 情感维度生成 caption)
total:   3193 条
```

→ MusicGen LoRA 微调时的 (audio, text) 配对监督，直接拿来用。

### 4. `integration_smoke.py` —— 端到端 smoke

一次性触摸 M2 / M3 / M4 / M5 / M6 / M9 六个模块，证明 pipeline 的形状对得上：

```
painting              Cleveland Ming "Poet Lin Bu Wandering in the Moonlight"
M3 (mock embed)       1129-chunk 语料检索 top-5 → 张雄山水 / 黄慎 / 治画论 / 钱榖 …
M2 (random init)      z (768d) → (v=-0.03, a=+0.11) → "tender"
M6 (rule)             → tempo=moderate, mode=pentatonic_gong, inst=[guqin, xiao]
M4 (mock gen)         8s @ 32kHz, prompt 含 RAG 上下文
M5 (phase vocoder)    ×1.5 拉慢 → 12s
M9 (librosa MIR)      tempo / prompt-audio sim
```

输出全在 `scripts/out/integration_smoke/`：
- `painting_metadata.json` —— 入口画作
- `retrieved_chunks.json` —— top-5 RAG 结果
- `va.json` —— M2 预测
- `descriptors.json` —— M6 输出
- `soundtrack.wav` —— M4 生成
- `soundtrack_slow.wav` —— M5 变速
- `metrics.json` —— M9 指标

⚠️ **注意**：这是 smoke test，**不是生产管线**——M2 用随机权重、M3 用 hash embed、M4 用 Mock 振荡器。证明的是接口形状对得上、数据流没断。

## 跑法

```bash
cd echoscroll/scripts
python3 build_rag_corpus.py        # ~2 秒
python3 build_va_labels.py         # ~30 秒（加载 200 MB JSON）
python3 build_audio_captions.py    # ~5 秒
python3 integration_smoke.py       # ~3 秒
```

## 产物落点

```
data/
├── rag/
│   └── chunks.jsonl                       454 KB · 1129 chunks
├── annotations/
│   └── emoart_va_labels.csv               111 MB · 132895 rows
└── captions/
    └── instrument_captions.jsonl          529 KB · 3193 rows

echoscroll/scripts/out/integration_smoke/  端到端 smoke 全套输出
```
