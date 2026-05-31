# T2 · MusicGen baseline 烘焙（A / B / C × 8）

> 服务器上一口气把答辩用的 24 段 baseline 音频跑完。
> 不微调，只调 prompt：用三种系统设定对比，证明 EchoScroll 的 V-A + RAG 加成。

## 三系统对比

| ID | 系统名 | Prompt 构造 | 用意 |
|---|---|---|---|
| **A** | text-only baseline | "Chinese ink-wash landscape music, slow tempo" | 商用 Suno 同水位 |
| **B** | +V-A | A + "valence X arousal Y, mood word" | 验证 V-A 头有效 |
| **C** | **+V-A + RAG**（EchoScroll 全开） | B + top-3 RAG 检索的画派 / 笔法描述 | 完整方法 |

## 模型依赖

| 模型 | HF repo | 大小 | 协议 |
|---|---|---|---|
| MusicGen-small | `facebook/musicgen-small` | 1.5 GB | CC-BY-NC 4.0 |
| EnCodec 32 kHz | 自动随 MusicGen 下 | 280 MB | — |

```bash
huggingface-cli download facebook/musicgen-small
```

## 数据依赖

`paintings.json` 已经在本目录内（8 画作 + V-A + 词 + RAG context，全部从主仓库 `app.js` 提取）。
不需要额外数据。

## 运行

```bash
pip install -r requirements.txt
python generate_baselines.py --duration 12 --out audio/
```

每段 12 s × 24 段 ≈ 5 min wall-clock on 4090；
若服务器慢，把 `--duration 8` 或先 `--paintings 1,2,3` 抽样。

## 期望产出

```
audio/
├── manifest.json                      # 24 条 metadata
├── p1_A.wav   p1_B.wav   p1_C.wav      # 8 paintings × 3 systems
├── p2_A.wav   p2_B.wav   p2_C.wav
...
└── p8_A.wav   p8_B.wav   p8_C.wav
```

每个 wav：32 kHz mono int16，约 600 KB / 12 s。

## 接 Demo / 评测

- 放进 `echoscroll_demo/assets/audio/baselines/` 供答辩对照
- 喂给 T5 的 FAD 评估
- 喂给 H9 盲评（人工随机化后 anonymise）
