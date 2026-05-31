# T6 · LP-MusicCaps 自动给中国乐打 caption

> T3 LoRA 微调的训练对越多越准。主仓库 `build_audio_captions.py` 用模板法做了 3193 对（古筝 99 + 二胡 1253 + 13-dim 1841），但模板化太重。
> 这一步用 LP-MusicCaps 给同一批音频跑机器 caption，再与模板互补 / 去重。

---

## 模型依赖

| 模型 | repo | 大小 | 协议 |
|---|---|---|---|
| LP-MusicCaps captioner | `seungheondoh/lp-music-caps` (GitHub + HF) | 1.0 GB | MIT |

```bash
# 模型在 GitHub repo 里，HF 仅放权重
git clone https://github.com/seungheondoh/lp-music-caps.git
huggingface-cli download seungheondoh/lp-music-caps
```

## 数据依赖

| 数据 | 路径 | 大小 |
|---|---|---|
| 古筝 99 | `$ECHOSCROLL_DATA/audio/ccmusic_guzheng99/` | 2.0 GB |
| 二胡 1253 | `$ECHOSCROLL_DATA/audio/ccmusic_erhu/` | 172 MB |
| 13-dim 1841 | `$ECHOSCROLL_DATA/audio/13dim/` | 152 MB |
| （可选）CCMusic CTIS 3974 / 国乐 200+ | `$ECHOSCROLL_DATA/audio/ccmusic_ctis/` | 3.7 GB（未下，可补） |

## 运行

```bash
pip install -r requirements.txt

python caption_audio.py \
    --audio-root $ECHOSCROLL_DATA/audio \
    --datasets ccmusic_guzheng99,ccmusic_erhu,13dim \
    --out caps_extended.jsonl \
    --max-per-dataset 0     # 0 = 全跑
```

每 10 s 片段约 0.8 s 推理 on 4090；5000 段 ≈ **2 h**。

## 期望产出

```jsonl
{"audio": "ccmusic_guzheng99/000123.wav",
 "duration_s": 18.4,
 "caption_template": "Solo guzheng with continuous left-hand vibrato, gentle expressive bends.",
 "caption_lpmc": "A solo guzheng piece in a pentatonic mode, with delicate ornamentation and a calm, traditional Chinese atmosphere.",
 "instrument": "guzheng",
 "tags_lpmc": ["traditional", "instrumental", "pentatonic", "calm"]}
```

## 合并回主仓库

```bash
python merge_with_template.py \
    --template $ECHOSCROLL_DATA/captions/instrument_captions.jsonl \
    --lpmc caps_extended.jsonl \
    --out $ECHOSCROLL_DATA/captions/instrument_captions_v2.jsonl \
    --combine "template + lpmc"
```

`combine` 三种模式：
- `template`：只保留模板
- `lpmc`：只保留机器
- `template + lpmc`：拼接为同一条（caption + "\n" + caption_lpmc）→ T3 用

合并后供 T3 重训。
