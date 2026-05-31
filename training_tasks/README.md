# EchoScroll · 训练任务包

> 7 个独立训练 / 推理任务，每个目录是一个自包含工程。
> 服务器拿到 zip 后，对照各任务自己的 README 装环境、拉数据、跑脚本。

## 总览

| ID | 任务 | GPU 时长 | 输入 | 产出 |
|---|---|---|---|---|
| **T1** | M2 V-A 头训练（EmoArt 132K） | 4090 ~6 h | EmoArt 局部图 + va_labels.csv | `va_head.pt` + Pearson r |
| **T2** | MusicGen baseline 烘焙（A/B/C × 8） | 4090 ~30 min | paintings.json + MusicGen-small | 24 段 wav |
| **T3** | MusicGen LoRA 微调（中国乐适配） | 4090 ~24 h | 古筝/二胡音频 + caption | LoRA adapter ~50 MB |
| **T4** | BGE-M3 真嵌入 + FAISS 索引 | 4090 ~10 min | chunks.jsonl 1129 行 | `faiss_bge_m3.index` |
| **T5** | FAD 真嵌入评估 | 4090 ~30 min | T2/T3 输出 + DEAM 参考 | `fad_real.json` |
| **T6** | LP-MusicCaps 自动 caption | 4090 ~2 h | 古筝/二胡音频目录 | `caps_extended.jsonl` |
| **T7** | Demo 48 段终用音频烘焙 | 4090 ~1 h | T3 LoRA + 8 画作 prompt | 48 段 wav + manifest |

## 依赖关系

```
T4 (RAG 索引) ───────┐
                    ▼
T1 (V-A 训练) ──► T2 (baseline) ────┐
                                    ▼
T6 (caption 扩充) ──► T3 (LoRA 微调) ──► T7 (Demo 烘焙) ──► T5 (FAD)
```

**关键路径**：T6 → T3 → T7 是 24+ 小时硬墙，建议拿到 zip 当天就启动。
**可并行**：T1 / T2 / T4 互不阻塞。

## 通用前置

每个任务的 `requirements.txt` 都列了自己的依赖；通用部分见 `shared/requirements.txt`。

```bash
# 服务器一次性
conda create -n echoscroll python=3.10 -y && conda activate echoscroll
pip install -r shared/requirements.txt

# 每个任务再装自己的
pip install -r T1_m2_va_training/requirements.txt
# ...
```

## 数据约定

所有任务默认读取 **本地数据根** `$ECHOSCROLL_DATA`，缺省指向：

```bash
export ECHOSCROLL_DATA=/path/to/echoscroll_data_kit/data
```

子目录约定与 `开题/EchoScroll_data_plan/data/` 完全一致：

```
$ECHOSCROLL_DATA/
├── images/{met_asian_art, cleveland_chinese, emoart, ...}
├── audio/{ccmusic_guzheng99, ccmusic_erhu, deam, ...}
├── annotations/emoart_va_labels.csv
├── captions/instrument_captions.jsonl
├── rag/chunks.jsonl
└── processed/paintings_unified.parquet
```

各任务里给的所有路径都用这个根，自己改 `--data-root` 参数即可指到别处。

## 模型权重总账

| 任务 | 模型 | HF repo | 大小 | 协议 |
|---|---|---|---|---|
| T1 | OpenCLIP ViT-L/14 | `openai/clip-vit-large-patch14` | 1.7 GB | MIT |
| T2 / T3 / T7 | MusicGen-small | `facebook/musicgen-small` | 1.5 GB | CC-BY-NC 4.0 |
| T2 / T3 / T7 | EnCodec 32 kHz | 随 MusicGen 一起下 | — | 同上 |
| T4 | BGE-M3 | `BAAI/bge-m3` | 2.2 GB | MIT |
| T5 | VGGish 或 OpenL3 | `harritaylor/torchvggish` | 280 MB | Apache-2.0 |
| T6 | LP-MusicCaps | `seungheondoh/lp-music-caps` | 1.0 GB | MIT |

合计落盘 **≈ 8 GB**，全部 HF 一键下，无 gated。

## 协议合规一句话

T3 LoRA 训练集（CCMusic 系列）**CC-BY-NC-ND 4.0**：训练可、释放衍生权重需保留 NC + ND；推荐 LoRA adapter **仅内部使用**，对外只发音频成品。

## 详细分任务说明

跳到各子目录阅读：

- [T1_m2_va_training/README.md](T1_m2_va_training/README.md)
- [T2_musicgen_baseline/README.md](T2_musicgen_baseline/README.md)
- [T3_musicgen_lora/README.md](T3_musicgen_lora/README.md)
- [T4_bge_m3_rag_index/README.md](T4_bge_m3_rag_index/README.md)
- [T5_fad_real_eval/README.md](T5_fad_real_eval/README.md)
- [T6_lp_musiccaps_caption/README.md](T6_lp_musiccaps_caption/README.md)
- [T7_demo_batch_generate/README.md](T7_demo_batch_generate/README.md)

更宏观的数据/任务说明书：见上一级目录 `数据集与训练任务说明书.md`。
