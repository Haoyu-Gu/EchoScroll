# EchoScroll · Implementation Root

> 中国画 → V-A 情感向量 → MusicGen 配乐 的完整端到端系统。
> 完整研究方案在 `../开题/EchoScroll_proposal/main.pdf`。

## 入口文档

| 文档 | 内容 |
|---|---|
| [`CONVENTIONS.md`](./CONVENTIONS.md) | 共用工程约定（技术栈 / V-A 数据契约 / 元数据 schema） |
| [`MODULES.md`](./MODULES.md) | **9 模块代码追踪**：每模块文件、行数、Public API、figures、跑法 |
| [`SHOWCASE.md`](./SHOWCASE.md) | **27 张可视化图**索引 + [`GALLERY.png`](./GALLERY.png) 拼图 |
| [`../开题/EchoScroll_data_plan/data/INVENTORY.md`](../开题/EchoScroll_data_plan/data/INVENTORY.md) | **14 个数据集**清点：kind、size、schema、样本 |

## 速览

- **9 模块** × ~880 行/模块 = **7,925 行 Python**
- **27 张可视化图**（每模块 3 张，全 CPU 可重生成）
- **2983 张统一画作** parquet ([`data/processed/paintings_unified.parquet`](../开题/EchoScroll_data_plan/data/processed/paintings_unified.parquet))
- **13 GB 数据**已落本地（11 完整 + 2 部分）

## 模块图

```
M1 Multimodal Encoder    CLIP-ViT-L/14 + BGE-M3 + 哈希元数据 → fused z (768d)
M2 Affective Projection  MLP 768→256→2 + Russell 8-quadrant + NT-Xent
M3 Art-history RAG       BGE-M3 + FAISS IndexFlatIP + 20 条种子语料
M4 Music Generator       MusicGen-small + LoRA wiring + MockMusicGenerator
M5 Editing Layer         beat-track + 段位替换 + phase vocoder BPM + style 重写
M6 Prompt Translator     LLM (Anthropic/OpenAI/Qwen) + 规则后备 → 8-slot 受控词表
M7 Humming Interaction   pYIN + Krumhansl-Schmuckler 调性 + chroma-CQT DTW
M8 Frontend + Backend    FastAPI 8 端点 + WebSocket / React + WaveSurfer
M9 Evaluation            V-A 一致性 + FAD + CLAP + librosa MIR + Pydantic 人评
```

## 数据库

| 类别 | 已落 |
|---|---|
| **中国画** | Met 230 张 + Cleveland 561 张 + zqman 2192 + AmazarashiEndure 927 + mingyy 12/89 shards (7K 张) + ArtBench-10 1K |
| **情感画作** | WikiArt-Emotions 4105 + EmoArt 标签 132K（图像部分缺）|
| **音乐 V-A** | DEAM 1802 song 标注 + 13-dim 1841 段 |
| **中国民乐** | Guzheng_Tech99（99 首古筝帧级技法）+ erhu_playing_tech（1253 二胡） |
| **Caption** | MusicCaps 5527 行 + MusicBench JSON（含节拍/和弦/调性）|

合并后的统一 schema 在 [`paintings_unified.parquet`](../开题/EchoScroll_data_plan/data/processed/paintings_unified.parquet)：
```
id, source, title, artist, dynasty, period, school, subject,
medium, license, image_url, image_local_path, caption, description
```

朝代分布（Top）：Qing 346 / Ming 218 / Southern Song 101 / Yuan 68 / Song 30 / Tang 3 / Han 3。
*zqman 没朝代标签所以 2202 null。*

## 怎么用

```bash
# 1. 每个模块独立跑（demo + 出图）
for m in M*/; do
  (cd "$m" && pip install -q -r requirements.txt && python demo.py && python viz.py)
done

# 2. 合并拼图
python build_gallery.py

# 3. 重新刷数据清点
python inspect_data.py        # 写 data/INVENTORY.md
python inspect_modules.py     # 写 MODULES.md
python build_unified_paintings.py  # 写 data/processed/paintings_unified.{parquet,csv}
```

## 还没做的（后续）

- **模块集成**：M8 的 8 个 stub 端点真接到 M1→M2→M3→M4→M5→M6→M7
- **LoRA 真训练**：在 CCMusic + Guzheng_Tech99 + erhu 上微调 MusicGen
- **V-A 自标 Pilot**：2000 张分层抽样 + Label Studio 圆环 GUI
- **mingyy + EmoArt 续传**：当前 7K + 9 styles，缺的部分可后台再拉
