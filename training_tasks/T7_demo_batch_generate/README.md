# T7 · Demo 48 段终用音频批量烘焙

> 离线把 Demo 答辩用的所有 painting × variant 组合烤完，
> Demo 现场不接 GPU、不接网络、直接播本地 wav。
> 这是 `演示物料清单.md` §5 / §C 的兑现脚本。

---

## 模型依赖

| 模型 | repo | 大小 |
|---|---|---|
| MusicGen-small | `facebook/musicgen-small` | 1.5 GB |
| T3 LoRA adapter | （本地，T3 训练产物） | ~50 MB |

## 数据依赖

`paintings.json`（与 T2 同源、本目录已附）

## 6 种变体

| variant | V-A 偏移 | 用途 |
|---|---|---|
| `default` | (v, a) 原值 | 主推 |
| `va_low`  | (v, a-0.4) | 演示 V-A 拖低唤起 |
| `va_high` | (v, a+0.4) | 演示 V-A 拖高唤起 |
| `va_pos`  | (v+0.4, a) | 演示 V-A 拖右（更愉悦） |
| `slow`    | default 后跑 phase-vocoder ×0.7（M5） | 演示编辑层减速 |
| `fast`    | default 后跑 phase-vocoder ×1.3 | 演示编辑层加速 |

## 运行

```bash
pip install -r requirements.txt

python batch_generate.py \
    --paintings-json paintings.json \
    --adapter /path/to/T3/checkpoints/lora_chinese_instr \
    --duration 16 \
    --out audio/ \
    --use-lora true
```

8 画 × 6 变体 = **48 段**；4090 单线程 ≈ **1 h**。

## 期望产出

```
audio/
├── manifest.json
├── p1_default.wav    p1_va_low.wav    p1_va_high.wav    p1_va_pos.wav    p1_slow.wav    p1_fast.wav
├── p2_default.wav    ...
...
└── p8_fast.wav
```

每段 16 s × 32 kHz int16 ≈ 1 MB；48 段共 **~50 MB** 进 zip 没压力。

## 接 Demo

```bash
cp audio/*.wav /path/to/echoscroll_demo/assets/audio/
# 然后改 app.js 里的 audioVariants[] 让映射对上
```

主仓库 `app.js` 里 `audioMap` 的预设位置可参考演示物料清单 §B "8 画 × 6 变体音频映射表"。
