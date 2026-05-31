# T3 · MusicGen LoRA 微调（中国乐适配）

> 让 MusicGen 学会古筝 / 二胡的音色与技法。
> **不全量训**——只在文本编码器（T5）上挂 LoRA adapter，~50 MB 训完即可上线。
> 这是项目 §3.2.3 与 §4.3 的 "improvement innovation"。

---

## 模型依赖

| 模型 | HF repo | 大小 | 协议 |
|---|---|---|---|
| MusicGen-small | `facebook/musicgen-small` | 1.5 GB | CC-BY-NC 4.0 |
| EnCodec 32 kHz | 自动随 MusicGen 下 | 280 MB | — |
| T5-base text encoder | 自动随 MusicGen 下 | 220 MB | Apache-2.0 |

> 如服务器 VRAM 充足（≥ 16 GB），可改 `facebook/musicgen-medium` 同套代码跑。

```bash
huggingface-cli download facebook/musicgen-small
```

## 数据依赖

| 数据 | 路径 | 大小 | 来源 |
|---|---|---|---|
| 古筝 Guzheng_Tech99 | `$ECHOSCROLL_DATA/audio/ccmusic_guzheng99/` | 2.0 GB | `huggingface-cli download --repo-type dataset ccmusic-database/Guzheng_Tech99` |
| 二胡 erhu_playing_tech | `$ECHOSCROLL_DATA/audio/ccmusic_erhu/` | 172 MB | `huggingface-cli download --repo-type dataset ccmusic-database/erhu_playing_tech` |
| caption | `$ECHOSCROLL_DATA/captions/instrument_captions.jsonl` | 3193 行 | 由 `echoscroll/scripts/build_audio_captions.py` 离线生成（已在主仓库做了） |

> 若想加规模：先跑 T6（LP-MusicCaps）把 caption 扩到 5000+ 再回来训。

## 协议提醒

CCMusic 全家 **CC-BY-NC-ND 4.0**：
- ✅ 训练可
- ❌ 不可重分发派生权重作商用
- 推荐：**LoRA adapter 仅内部使用**，对外只发音频成品

## 运行

```bash
pip install -r requirements.txt

# 1. 数据准备：把 audio 转 32 kHz mono，切 ≤ 30 s 段
python prepare_data.py --out data/train_pairs.jsonl

# 2. 训练 LoRA
python train_lora.py \
    --pairs data/train_pairs.jsonl \
    --epochs 8 \
    --batch-size 4 \
    --grad-accum 8 \
    --lr 1e-4 \
    --lora-rank 16 \
    --out checkpoints/lora_chinese_instr/
```

VRAM 占用 ~14 GB（batch 4, grad-accum 8 ⇒ 等效 32）。
4090 跑满 8 epoch 约 **24 h**。

## 期望产出

```
checkpoints/lora_chinese_instr/
├── adapter_config.json            # PEFT 标准格式
├── adapter_model.safetensors      # ~50 MB
├── train_loss.png
└── eval_samples/
    ├── guzheng_va_calm.wav        # 抽样推理验证
    ├── erhu_va_melancholic.wav
    └── ...
```

## 加载方式（给 T7 / EchoScroll 主仓库）

```python
from audiocraft.models import MusicGen
from peft import PeftModel
model = MusicGen.get_pretrained("facebook/musicgen-small")
model.lm.text_encoder = PeftModel.from_pretrained(
    model.lm.text_encoder, "checkpoints/lora_chinese_instr")
```

## 评估

```bash
python eval_samples.py --adapter checkpoints/lora_chinese_instr
# 输出 4 段验证 wav + 对照（带 adapter / 不带 adapter）
```

主观听感对比即可——客观 FAD 留给 T5。
