# EchoScroll Demo · 音频样本与配对方案

> 给做 GPU 实验 / 生成的同学看的工作单。
> 看完你应该清楚：**要烤多少段、每段什么 V-A / prompt、文件名叫啥、放哪里、demo 怎么吃**。
> 配套生产脚本 `echoscroll_training_tasks.zip` 里的 **T2 + T7** 已经写好，直接跑。

---

## 0. TL;DR · 一句话

| 想做到 | 烤几段 | 跑哪个脚本 | 时长（4090） |
|---|---|---|---|
| **A 最小可演** | 8 段 = 每画一段默认 | T7 用 `--variants default` 单跑 | 10 min |
| **B 标准 demo** | 8 × 6 = **48 段**（每画 default + 3 V-A 变体 + 2 编辑变体） | **`T7_demo_batch_generate/batch_generate.py`** | ~1 h |
| **C 加评测对照** | B 之上 **+ 24 段** baseline (8 × A/B/C) | **`T2_musicgen_baseline/generate_baselines.py`** | +30 min |
| **D 加哼唱** | C 之上 +8 段哼唱预录 + 8 段对齐输出 | M7 处理（CPU，无需 GPU） | 半天 |

**推荐至少做到 B**；C 是结题报告 §6 评测的必备品。

---

## 1. 8 张画作 · 固定 V-A 锚点

这 8 个 V-A 是 `echoscroll_demo/app.js::PAINTINGS[].va` 写死的，**所有音频都围绕这 8 个锚点扩展**。

| ID | 画 | 朝代 | **V-A 锚点** | 词 | 主乐器（用于 prompt 模板）|
|---|---|---|---:|---|---|
| **p1** | 米友仁 · 云山图 | 南宋 | (−0.22, **−0.55**) | calm | guqin + xiao |
| **p2** | 杜堇 · 林逋月夜行吟 | 明 | (−0.03, +0.11) | tender | guqin + xiao |
| **p3** | 陈汝言 · 群仙山图 | 元 | (+0.35, −0.05) | tender | guzheng + dizi |
| **p4** | 巨然 · 溪山兰若图 | 北宋 | (−0.36, −0.34) | melancholic | xiao + guqin |
| **p5** | 八大山人 · 仿郭忠恕山水 | 清 | (−0.42, +0.18) | tense | pipa + erhu |
| **p6** | 佚名 · 溪山无尽图 | 北宋-金 | (−0.05, +0.45) | joyful | erhu + guzheng + dagu |
| **p7** | 倪静 · 寒梅图 | 元-明 | (−0.30, −0.42) | sad | xiao solo |
| **p8** | 刘世儒 · 雪梅图 | 明 | (+0.12, −0.50) | calm | guqin solo |

完整 prompt 模板与 RAG context 写在：
- `echoscroll_training_tasks/T2_musicgen_baseline/paintings.json`
- `echoscroll_training_tasks/T7_demo_batch_generate/paintings.json`
（两份内容相同，可视为单一来源。）

---

## 2. 每画需要的 6 种音频变体（B 标准 demo）

每张画都按统一规则生 6 段：4 段 MusicGen 直出（不同 V-A） + 2 段从 default 派生的 M5 编辑版。

| 变体名 | 生成方式 | V-A 偏移 | 用于演示哪个交互 |
|---|---|---|---|
| `default` | MusicGen + LoRA · 原 V-A | (0, 0) | **首播 · 主推** |
| `va_low` | MusicGen + LoRA · arousal −0.4 | (0, −0.4) | V-A 圆环往**下**拖 → 切此 |
| `va_high` | MusicGen + LoRA · arousal +0.4 | (0, +0.4) | V-A 圆环往**上**拖 → 切此 |
| `va_pos` | MusicGen + LoRA · valence +0.4 | (+0.4, 0) | V-A 圆环往**右**拖 → 切此 |
| `slow` | M5 phase-vocoder ×0.7 · 从 default 派生 | 同 default · 节奏 −30% | "M5 编辑层减速"按钮 |
| `fast` | M5 phase-vocoder ×1.3 · 从 default 派生 | 同 default · 节奏 +30% | "M5 编辑层加速"按钮 |

> **关键**：`slow / fast` 是从 `default` 派生的，**不重新调 MusicGen**——这是有意的，演示"编辑层不重新生成"。
> `va_low / va_high / va_pos` 必须真生，因为要听出音色/调性差异。

### 命名约定（务必严格，否则 demo 接不上）

```
p{1..8}_{default,va_low,va_high,va_pos,slow,fast}.wav
```

例如：

```
p1_default.wav   p1_va_low.wav   p1_va_high.wav   p1_va_pos.wav   p1_slow.wav   p1_fast.wav
p2_default.wav   ...
...
p8_fast.wav
```

48 段 × ~1 MB（16 s @ 32 kHz int16）≈ **50 MB**。

### 一键产出

```bash
cd echoscroll_training_tasks/T7_demo_batch_generate/
pip install -r requirements.txt
python batch_generate.py \
    --paintings-json paintings.json \
    --adapter /path/to/T3/checkpoints/lora_chinese_instr \
    --duration 16 \
    --use-lora true \
    --out audio/
```

跑完 `audio/` 里就是上面 48 段 + 一份 `manifest.json`（每段对应 prompt、duration、V-A 偏移、是否派生）。

---

## 3. V-A → 音频 的实时配对逻辑（demo 里怎么用）

`echoscroll_demo/app.js` 现在已有 **最近邻配对**（line 320 `nearestAudio`）。
机制：

1. 用户拖 V-A 圆环上的红点 → 触发 `dragMove(v, a)`
2. Web Audio 实时合成 sine 跟随播放（即时反馈）
3. 拖动停止后，与当前 painting 的 6 个变体的 **预设 V-A 坐标做欧氏距离**，自动切到最近的那段 wav

### 当前 `AUDIO_BANK`（mock 期临时表，**T7 烤完后要换成 per-painting**）

```js
// app.js 当前是全局共享 6 段 mock
const AUDIO_BANK = [
  { file: 'main_p2_lin_bu_8s.wav',         va: [0.0, 0.1],    label: '原版' },
  { file: 'main_p2_lin_bu_slow_12s.wav',   va: [-0.2, -0.5],  label: 'M5 拉慢' },
  { file: 'm5_bpm_slow.wav',               va: [-0.3, -0.65], label: '×0.5 BPM' },
  { file: 'm5_bpm_fast.wav',               va: [0.0, 0.6],    label: '×1.5 BPM' },
  { file: 'm5_segment_replace.wav',        va: [-0.4, 0.3],   label: '段位替换' },
  { file: 'm4_mock_literati_10s.wav',      va: [0.3, -0.1],   label: '文人意象' },
];
```

### T7 烤完后改成 per-painting（我会改 app.js，你不用动）

```js
// 每画一组 6 段；选画时整组替换
const AUDIO_BANK_BY_PAINTING = {
  p1: [
    { file: 'p1_default.wav',  va: [-0.22, -0.55], label: '主版' },
    { file: 'p1_va_low.wav',   va: [-0.22, -0.95], label: 'V-A 下拖' },
    { file: 'p1_va_high.wav',  va: [-0.22, -0.15], label: 'V-A 上拖' },
    { file: 'p1_va_pos.wav',   va: [+0.18, -0.55], label: 'V-A 右拖' },
    { file: 'p1_slow.wav',     va: [-0.22, -0.55], label: 'M5 ×0.7' },
    { file: 'p1_fast.wav',     va: [-0.22, -0.55], label: 'M5 ×1.3' },
  ],
  p2: [ /* ...同结构，把 va 锚点换成 (-0.03, +0.11)... */ ],
  // ...
};
```

→ **你只要按命名规则把 48 段 wav 给我，剩下我 patch app.js。**

---

## 4. 评测对照组（C 加评测）· 8 × A/B/C = 24 段

为答辩里的"对比 Suno-like 商用 baseline / 去 RAG 版 / 全开版"做证据。
**与上面 48 段独立**，文件名要明显区分。

| 系统 | Prompt 内容 | 用意 |
|---|---|---|
| **A · text-only** | "Chinese ink-wash landscape music, slow tempo" | 类比商用 Suno |
| **B · +V-A** | A + "valence X arousal Y, mood word" + 8-slot descriptors | 验证 V-A 头 |
| **C · +V-A+RAG**（EchoScroll 全开）| B + 该画 top-3 RAG context | 完整方法 |

### 命名约定

```
p{1..8}_{A,B,C}.wav     共 24 段
```

例：`p1_A.wav  p1_B.wav  p1_C.wav  ...  p8_C.wav`

### 一键产出

```bash
cd echoscroll_training_tasks/T2_musicgen_baseline/
pip install -r requirements.txt
python generate_baselines.py --duration 12 --out audio/
```

跑完 `audio/manifest.json` 写清每段对应的 prompt 全文。

---

## 5. 哼唱配对（D · 可选）

如果想演示 M7 哼唱交互，预录 **8 段哼唱输入 + 8 段对齐输出**：

| 文件 | 内容 | 怎么做 |
|---|---|---|
| `p{i}_humming_input.wav` | 3–5 s 哼唱 / 钢琴音符序列，每画一段 | 任意 DAW 或手机录都行 22.05 kHz mono |
| `p{i}_humming_aligned.wav` | 上面那段经 M7 pYIN + DTW 处理后 | 跑主仓库 `echoscroll/M7_humming_interaction/humming.py` |

哼唱内容建议（与画意契合的简短动机）：

| 画 | 哼唱动机 |
|---|---|
| p1 云山图 | A 小调下行三度 A-G-E（含 2 个长音） |
| p2 林逋月夜 | C 大调三和弦上行 C-E-G 每音 0.6 s |
| p3 群仙山图 | D 调五声上行 D-E-F♯-A-B |
| p4 溪山兰若图 | F 小调长音持续，单音渐强 |
| p5 仿郭忠恕 | 自由律动短音群：高低高低 |
| p6 溪山无尽图 | G 调铿锵节奏型 G-G-G-D-G |
| p7 寒梅图 | E 小调下行 E-D-C |
| p8 雪梅图 | C 大调高音点 C5-E5-G5 短促 |

→ M7 处理是 CPU 几秒搞定，不占 GPU。

---

## 6. 三组音频汇总（你最终要交给我的）

| 组 | 路径 | 段数 | 大小估算 | 必/选 |
|---|---|---|---:|---|
| **48 段 demo 主用**（§2）| `T7_demo_batch_generate/audio/p*_*.wav` | 48 | ~50 MB | **必** |
| **24 段评测对照**（§4）| `T2_musicgen_baseline/audio/p*_*.wav` | 24 | ~20 MB | 强烈建议 |
| **16 段哼唱**（§5）| 主仓库 M7 输出 | 16 | ~10 MB | 选 |

合计上限 **88 段 / ~80 MB**——zip 进 demo 完全没压力（当前 demo zip 12 MB，加完仍 < 100 MB）。

---

## 7. 协议 / 命名 / 输出格式硬约束（不要改）

- **采样率**：32000 Hz（MusicGen 自带 EnCodec 输出率，**不要重采样**）
- **声道**：mono
- **位深**：16-bit signed PCM
- **容器**：`.wav`（不要 mp3，浏览器有兼容性差异）
- **时长**：
  - default / va_* / A / B / C ：12–16 s
  - slow ：~20 s（×0.7 的派生）
  - fast ：~10 s（×1.3 的派生）
- **目录命名**：见 §2 / §4 严格遵守
- **manifest.json**：每个目录都要带一份，记录每段的 prompt / V-A / 派生关系

---

## 8. 烤完之后给我的交付方式

任选其一：

1. 服务器跑完，把 `audio/` 整个 scp 回本机我电脑
2. 或者把 `T7_demo_batch_generate/audio.zip` + `T2_musicgen_baseline/audio.zip` 发我
3. 我拿到后会做：
   - 拷到 `echoscroll_demo/assets/audio/`
   - 改 `app.js` 的 `PAINTINGS[i].audio` + `AUDIO_BANK_BY_PAINTING`
   - 重新打 `echoscroll_demo.zip`
   - 用 Concert Mode 自动巡演一遍验证 8 画都不哑

---

## 9. 如果出问题怎么办（GPU 排队 / 出来不好听 / 时间不够）

| 情况 | 回退 |
|---|---|
| GPU 排不上队 | 先跑 §4 那 24 段（最小，30 min），demo 用 §2 当前 mock 顶替；§2 留到 W3 末跑 |
| LoRA 没训完 | 跑 `--use-lora false`，纯 MusicGen-small 也能听 |
| 某画 default 不好听 | 调 `paintings.json` 的 prompt，**只重生那一画的 6 段**（脚本支持 `--paintings p3`） |
| 时间彻底来不及 | 至少保 §2 的 8 段 `default`，其余用当前 mock + 嘴上解释 |

---

## 10. 在哪里看更多

- 完整演示物料 / 失败恢复 / 答辩讲稿 → `演示物料清单.md`
- T7 详细文档 → `echoscroll_training_tasks/T7_demo_batch_generate/README.md`
- T2 详细文档 → `echoscroll_training_tasks/T2_musicgen_baseline/README.md`
- T3 LoRA 训练文档（48 段的"+LoRA"需要它先训完）→ `echoscroll_training_tasks/T3_musicgen_lora/README.md`

---

*有任何 prompt 不顺、V-A 偏移想换数、命名约定觉得别扭，直接和我说，我同步改 demo 端的映射逻辑。*
