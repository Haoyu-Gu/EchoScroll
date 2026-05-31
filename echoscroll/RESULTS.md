# EchoScroll · 当前实验成果

> 截至 2026-05-13。本文档汇总目前所有可量化、可复现的结果。
> 完整方案在 `../开题/EchoScroll_proposal/main.pdf`。

## TL;DR

四档成果：

1. **功能验证** — 9 模块独立 demo 全部通过，含 19 个硬测试数字
2. **数据加工** — 4 个 pipeline 真把 Met / Cleveland / EmoArt / CCMusic 加工到模型可消费形态
3. **端到端 smoke** — 真画作 ▶ M3 ▶ M2 ▶ M6 ▶ M4 ▶ M5 ▶ M9 全链路无断
4. **27 张可视化** — 每模块 3 张，含一张 3×3 总览 GALLERY.png

---

## 1. 功能验证（19 个硬数字）

每个数字来自对应模块的 `demo.py` 或 `viz.py` 在 MacBook CPU 上的真实运行。

| # | 模块 | 测试 | 输入 | 输出 / 验证 |
|---|---|---|---|---|
| 1 | M2 | 9 个 Russell 圆环规范点 | (±1, 0) / (0, ±1) / (±√2/2, ±√2/2) / (0, 0) | 全部映射到正确情感词（calm / excited / tense / depressed / serene / tender） |
| 2 | M3 | Cleveland API 真拉 30 张 | Chinese Art + Painting + CC0 + has_image | 30/30 成功，朝代覆盖南宋 10/元 7/明 4/清 4/北宋系 3 |
| 3 | M3 | Met API 真拉 20 张 | departmentId=6 + q=painting + 中国文化过滤 | 20/20 成功，含 Bi Chang、《Emperor Xuanzong's Flight to Shu》 |
| 4 | M3 | 全量过滤 | 8599 候选 | 230 张 CC0 中国画落地 |
| 5 | M4 Mock | V-A=(-0.3, -0.5) "literati landscape" | 10 s duration | 32 kHz mono int16 WAV, 640,044 bytes |
| 6 | M5 beat-track | 10 s 合成信号 + 4 噪声脉冲 @ 1.0/3.5/6.0/8.5 s | librosa.beat.beat_track | 检出 4 beats @ **1.024 / 3.520 / 6.016 / 8.496 s** |
| 7 | M5 BPM ×0.5 | 10 s 输入 | tgt=src/2 | **20.00 s** 输出，音高完全不变 |
| 8 | M5 BPM ×1.5 | 10 s 输入 | tgt=src×1.5 | **6.67 s** 输出 |
| 9 | M5 段位替换 | 中段噪声替换 + 50ms cross-fade | librosa | 输出 **9.90 s**（误差 < 1%） |
| 10 | M6 规则 | "再空一点" | 中文口语 | `texture=sparse` ✅ |
| 11 | M6 规则 | "更激烈" | 中文口语 | `tempo=fast, dynamics=f, articulation=staccato` ✅ |
| 12 | M6 规则 | "make it gentler" | 英文 | `tempo=slow, dynamics=p, articulation=legato` ✅ |
| 13 | M6 规则 | "古风一点，加点琴" | 混合 | `mode=pentatonic_gong, instrumentation=[piano,guqin,xiao]` ✅ |
| 14 | M7 pYIN | A 大调三和弦 hum (220/277/330/440 Hz × 6) | 22050 Hz 3 s | 检出 F0 contour 与谱一致 |
| 15 | M7 KS 调性 | 上述 hum 的 12 PC 直方图 | major / minor / pentatonic_gong 模板对比 | **A major, r = 0.957** ✅ |
| 16 | M7 DTW 转调 | A 大调 hum vs C 大调 target | chroma-CQT + librosa.sequence.dtw | **transpose_cents = -300.0**（精确 3 半音）✅ |
| 17 | M9 FAD | 2 系统 × 10 假音频 | random-projection 后备 embed | FAD 计算无 NaN，PSD 平方根稳定 |
| 18 | M9 MIR | mock 8s WAV | librosa.feature | spectral_centroid=383 Hz, ZCR=0.034, RMS=0.443 |
| 19 | M8 backend | FastAPI 路由就绪 | uvicorn 启动 | 8 端点 + WebSocket 全部 import + serve 测试通过 |

---

## 2. 数据加工产物（来自 `echoscroll/scripts/`）

按报告 §3.2.1–3.2.4 把原始资源加工到模型可消费形态。

### 2.1 RAG 语料 `data/rag/chunks.jsonl`

来自 Met + Cleveland 真实策展文，每条切成 ≤500 char chunk 并加 dynasty / painter / motif / source 元数据。

| 来源 | chunks |
|---|---:|
| Met | 230 |
| Cleveland | 899 |
| **合计** | **1,129** |

朝代分布：Qing 441 / Ming 361 / Southern Song 163 / Yuan 102 / Song 30 / Northern Song 8 / Tang 4 / Han 3 / Jin 1 / None 16

> 直接 BGE-M3 编码 + FAISS IndexFlatIP 即可上线真 RAG。

### 2.2 V-A 训练标签 `data/annotations/emoart_va_labels.csv`

读 EmoArt-130k Annotation.json（200 MB），离散标签映射到连续 V-A，加 dominant_emotion 偏移（Calm 偏低唤起 / Anger 偏高唤起负价等）。

- **132,895 行**（111 MB CSV，17 列）
- **rows_with_local_image = 7,512**（9 个 style 的 tar.gz 已落本地）

Top dominant_emotion 分布：

| emotion | count |
|---|---:|
| Calm | 74,350 |
| Excited | 20,595 |
| Contentment | 20,406 |
| Sad | 5,827 |
| Alarmed | 5,407 |
| Frustrated | 3,313 |
| Happy | 942 |
| Annoyed | 557 |

→ M2 真训练直接用这份 CSV。

### 2.3 仪器音频 caption `data/captions/instrument_captions.jsonl`

按技法 / 情感模板生成的 (audio, text) 对。

| 数据集 | 条数 | caption 风格示例 |
|---|---:|---|
| Guzheng_Tech99 | 99 | "Solo guzheng with continuous left-hand vibrato, gentle expressive bends." |
| erhu_playing_tech | 1,253 | "Solo erhu with slow vibrato, plaintive sustained tone." |
| 13-Dim Music Emotions | 1,841 | "Instrumental piece evoking a calm/relaxing/serene and beautiful mood." |
| **合计** | **3,193** | — |

→ MusicGen LoRA 微调监督对，直接拿来用。

### 2.4 统一画作 manifest `data/processed/paintings_unified.parquet`

Met + Cleveland + zqman manifest 合并到统一 schema。

| source | rows |
|---|---:|
| zqman | 2,192 |
| cleveland | 561 |
| met | 230 |
| **合计** | **2,983** |

朝代分布（标注的部分）：Qing 346 / Ming 218 / Southern Song 101 / Yuan 68 / Song 30 / Tang 3 / Han 3 / Northern Song 5 / Jin 1

字段：`id / source / title / artist / dynasty / period / school / subject / medium / license / image_url / image_local_path / caption / description`。

---

## 3. 端到端 smoke 测试（六模块串成 pipeline）

入口：**Cleveland 馆藏 · Ming 朝 ·《Poet Lin Bu Wandering in the Moonlight》**（painting_id = `cle_132015`）

| 步骤 | 模块 | 输入 | 输出 |
|---|---|---|---|
| 1 | M3 (hash-mock embed) | 画 metadata 字符串 | 1129 chunks 中检索 top-5 → Zhang Xiong Qing landscape (0.350), Huang Shen swift style (0.329), 治画论 (0.314), Zhe school painting (0.314), Bada Shanren 's monks (0.311) |
| 2 | M2 (random-init MLP) | 由 painting_id 派生的 z ∈ ℝ^768 | V-A = **(-0.028, +0.108)** → "**tender**" |
| 3 | M6 (rule) | V-A 当前状态 + "make it more contemplative, ancient style with guqin" | tempo=moderate · **mode=pentatonic_gong** · meter=4/4 · register=mid · **inst=[guqin, xiao]** · texture=moderate · articulation=legato · dyn=mp |
| 4 | M4 Mock | V-A + descriptors + top-3 RAG context | 8 s @ 32 kHz mono WAV (500 KB) |
| 5 | M5 phase-vocoder | 8 s wav, src=120 / tgt=80 | **12.0 s** wav (750 KB, 音高不变) |
| 6 | M9 librosa | smoke wav + 拼好的 prompt | spectral_centroid=383.6 Hz, ZCR=0.034, RMS=0.443, prompt-audio sim=-0.043 |

**完整生成 prompt（M4 内部拼出来的）**：
> `Chinese landscape painting soundtrack. tense mood. tempo: moderate; instrumentation: ['guqin', 'xiao']; texture: moderate; dynamics: mp; register: mid. context: Landscape. Zhang Xiong. Hanging scroll; ink and color on paper...`

→ **接口形状全对得上，6 模块复合无断点**。M2 权重随机所以 V-A 语义层不可信，但 pipeline 结构通过验证。

---

## 4. 可视化（27 张图 + 1 张总览）

| 模块 | 图 1 | 图 2 | 图 3 |
|---|---|---|---|
| M1 | 4 画作 modality 范数柱图 | 余弦相似度 4×4 矩阵 | 融合架构示意 |
| M2 | Russell 圆环 100 散点（按 8 词着色）| 8 词频统计 | 50 步 Adam 训练 MSE/InfoNCE 曲线 |
| M3 | 3 查询 top-5 检索分（EN/EN/ZH）| 20 语料 PCA 散点（朝代上色） | RAG pipeline 示意 |
| M4 | 3 V-A → 波形对比 | 3 V-A → mel-spec 对比 | V-A→pitch 等高线 |
| M5 | 波形 + onset envelope + 4 红虚线 beat | 原始 / ×0.5 / ×1.5 三联 | 红框删 → 绿框换 |
| M6 | 8 prompt 翻译表 | slot×value 热图（彩色编码值）| router → LLM/Rule → 8-slot |
| M7 | 波形 + F0 曲线（log y 轴）| 12 PC 直方图 + 3 KS 模板 | DTW cost 矩阵 + chroma |
| M8 | 三层架构图（Browser/FastAPI/M*）| 时序图（upload→generate→edit）| V-A 圆环面板 UI mockup |
| M9 | 3 系统 × 5 维 人评柱图（带 std） | V-A 一致性散点 + Pearson r | 6 维雷达（FAD/V-A/CLAP/etc） |

总览：`GALLERY.png`（3×3 拼图）

---

## 5. 还**没**有的（坦诚说明）

| 报告 §3.3.3 期望 | 当前状态 | 缺什么 |
|---|---|---|
| 真 M2 模型权重 | ❌ 随机初始化 | 用 emoart_va_labels.csv 训 5–10 epoch（几小时 CPU） |
| 真 MusicGen 音频 | ❌ Mock sine + 颤音 | 拉 facebook/musicgen-small（2 GB） |
| 真 BGE-M3 RAG 索引 | ❌ hash 后备 embed | 拉 BAAI/bge-m3（2 GB） |
| 真 V-A 一致性 Pearson r | ❌ 合成 30 对 | 需先有真训练+真生成 |
| 真 FAD on real audio | ❌ random-proj 后备 | 需 VGGish/OpenL3 + 真 generated audio |
| 真盲评 CSV | ❌ random.choice([3,4,5]) 12 行 | 需召集 ≥ 20 人评估，~6 周 |
| 真 LoRA 微调 | ❌ PEFT wiring 完成但未训练 | 需 GPU 24h+，建议服务器跑 |

→ 目前算 "**功能 + 数据流验证完成**"，下一阶段是 "**模型实测**"。

---

## 6. 复现命令

```bash
# 1. 每个模块独立 demo + viz
for m in echoscroll/M*/; do
  (cd "$m" && pip install -q -r requirements.txt && python demo.py && python viz.py)
done

# 2. 数据加工 4 个 pipeline
cd echoscroll/scripts
python build_rag_corpus.py            # ~2 s
python build_va_labels.py             # ~30 s
python build_audio_captions.py        # ~5 s
python integration_smoke.py           # ~3 s

# 3. 刷新所有报告
cd echoscroll
python build_unified_paintings.py
python inspect_data.py                # 刷 data/INVENTORY.md
python inspect_modules.py             # 刷 MODULES.md
python build_gallery.py               # 刷 GALLERY.png
```

---

## 7. 文件索引

| 路径 | 内容 |
|---|---|
| `echoscroll/RESULTS.md` | **本文档** |
| `echoscroll/GALLERY.png` | 3×3 模块总览 |
| `echoscroll/SHOWCASE.md` | 27 图带说明的索引 |
| `echoscroll/MODULES.md` | 9 模块代码追踪 |
| `echoscroll/CONVENTIONS.md` | 共用工程约定 |
| `echoscroll/M*/figures/*.png` | 每模块 3 张图 |
| `echoscroll/scripts/out/integration_smoke/` | 端到端 smoke 完整输出 |
| `data/INVENTORY.md` | 18 个数据集详单 |
| `data/rag/chunks.jsonl` | 1129 RAG chunks |
| `data/annotations/emoart_va_labels.csv` | 132895 V-A 标签 |
| `data/captions/instrument_captions.jsonl` | 3193 仪器 caption |
| `data/processed/paintings_unified.{parquet,csv}` | 2983 画作合并 manifest |
