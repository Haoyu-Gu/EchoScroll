# T5 · FAD 真嵌入评估（替换 random-projection 兜底）

> Fréchet Audio Distance：把生成音频与一个 reference 分布的 (μ, Σ) 算高斯距离。
> 主仓库 M9_evaluation 默认 random-projection 兜底（数值稳定但缺乏区分力）。
> 本任务用 **VGGish** 或 **OpenL3** 嵌入提供真 FAD。

---

## 模型依赖（二选一）

| 模型 | repo | 大小 | 协议 | 推荐 |
|---|---|---|---|---|
| VGGish (TF→Torch port) | `harritaylor/torchvggish` (pip 装) | 280 MB | Apache-2.0 | ✅ 标准做法 |
| OpenL3 | `openl3` (pip 装) | 18 MB | MIT | 备选，更轻量 |

```bash
pip install torchvggish openl3 frechet_audio_distance
```

## 数据依赖

| 用途 | 路径 | 大小 |
|---|---|---|
| 生成音频（要评的） | `audio_gen/`（T2 / T7 输出） | 24–48 段 |
| Reference 分布 | DEAM `$ECHOSCROLL_DATA/audio/deam/audio/` | 1.3 GB (1802 曲) |
| 备选 reference | MusicCaps 自爬 wav（如有），或 PMEmo / 13-dim | — |

> FAD 的 reference 选择敏感：建议主报 **vs DEAM**（最稳定），辅报 **vs 13-dim 中乐**（看中乐子分布相近度）。

## 运行

```bash
pip install -r requirements.txt

python compute_fad.py \
    --gen audio_gen/ \
    --ref $ECHOSCROLL_DATA/audio/deam/audio/ \
    --embedder vggish \
    --out fad_real.json
```

## 期望产出

```json
{
  "embedder": "vggish",
  "ref_dir": "/data/.../deam/audio",
  "n_ref": 1802,
  "groups": [
    {"name": "A_baseline",       "n": 8, "fad": 32.4},
    {"name": "B_va",             "n": 8, "fad": 26.1},
    {"name": "C_va_rag",         "n": 8, "fad": 22.8},
    {"name": "D_va_rag_lora",    "n": 8, "fad": 18.5}
  ],
  "delta_C_minus_A": -9.6,
  "delta_D_minus_A": -13.9
}
```

→ 期望 **D < C < B < A**，差值越大效果越显著。

## 接报告

直接抽进结题报告 §6 Evaluation；FAD 减小百分比可入 PPT 主结果柱图。
