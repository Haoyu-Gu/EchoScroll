# T1 · M2 V-A 头训练

> 把 EmoArt-130k 的离散标签 + dominant_emotion 转好的连续 V-A 当监督，
> 在 CLIP 图像特征上面训一个 2 层 MLP，输出 valence / arousal ∈ [-1, 1]。
> 这一步出来的 `va_head.pt` 是整个 EchoScroll pipeline 的"画 → 情感"语义桥。

---

## 模型依赖

| 模型 | HF repo | 大小 | 角色 | 协议 |
|---|---|---|---|---|
| OpenCLIP ViT-L/14 | `openai/clip-vit-large-patch14` | 1.7 GB | 冻结的图像编码器 | MIT |

```bash
huggingface-cli download openai/clip-vit-large-patch14
```

## 数据依赖

| 数据 | 路径 | 大小 | 来源 |
|---|---|---|---|
| EmoArt-130k 局部图（9 个 style 的 tar.gz） | `$ECHOSCROLL_DATA/images/emoart/` | 3.6 GB | `huggingface-cli download --repo-type dataset printblue/EmoArt-130k` |
| V-A 标签（Annotation.json → 连续 V-A 转换好的 CSV，13.3 万行 17 列） | `$ECHOSCROLL_DATA/annotations/emoart_va_labels.csv` | 111 MB | 由 `echoscroll/scripts/build_va_labels.py` 离线生成（本仓库已经做了，可直接拷） |

> EmoArt 全集 webdataset 是 ~50 GB，本任务**只需要 parquet 子集 ~5 GB**。
> 若服务器上没下，跑 `bash download_data.sh` 自动拉。

## 运行

```bash
# 装环境
pip install -r requirements.txt

# 配数据根
export ECHOSCROLL_DATA=/path/to/data

# 训练
python train.py \
    --epochs 5 \
    --batch-size 256 \
    --lr 3e-4 \
    --lambda-contrast 0.1 \
    --out checkpoints/va_head.pt
```

## 期望产出

| 文件 | 说明 |
|---|---|
| `checkpoints/va_head.pt` | 2 层 MLP（768 → 256 → 2）权重 |
| `checkpoints/train_curves.png` | loss + Pearson r 训练曲线 |
| `checkpoints/eval_metrics.json` | 验证集 Pearson r (V / A) + MSE |
| `checkpoints/predictions_val.csv` | 验证集 pred vs gt |

## 评估

```bash
python eval.py --checkpoint checkpoints/va_head.pt
```

期望验证集 Pearson r：**V ≥ 0.55, A ≥ 0.50**（参考 EmoArt 论文 baseline，离散→连续后的上界）。

## 接 EchoScroll

训完把 `va_head.pt` 拷到主仓库：

```bash
cp checkpoints/va_head.pt \
    /path/to/echoscroll/M2_affective_projection/checkpoints/va_head.pt
```

主仓库的 `M2_affective_projection/projection.py::AffectiveProjection.load_state_dict()` 会自动捡到它。
