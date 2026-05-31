# EchoScroll · 共用工程约定

> 给所有模块作者读的一份共识文档。每个 `M*/` 子模块**完全独立**，**禁止** 跨模块 import；
> 但所有模块都应遵循下面的约定。

## 项目总览

EchoScroll = **中国画 → V-A 情感向量 → MusicGen 配乐** 的端到端可交互系统。
完整方案在 `开题/EchoScroll_proposal/main.pdf` §3.2，Table 4 列出了核心模块。

## 技术栈

- **Python ≥ 3.10**
- **PyTorch ≥ 2.1**，CUDA 可选（MacBook MPS / 服务器 CUDA 都要兼容）
- **HuggingFace** `transformers` / `datasets` / `peft` / `diffusers` / `huggingface_hub`
- **关键模型默认值**（每个模块可在 README 里换）：
  - 视觉编码：`openai/clip-vit-large-patch14`（patch14, 336 输入）
  - 文本编码：`BAAI/bge-m3`（中英双语 SBERT 升级版）
  - 音乐生成：`facebook/musicgen-small`（300 M）
  - 节拍/时间步：自实现 librosa-based，或 `madmom`
  - 音高：`librosa.pyin` (YIN) 或 `crepe`
  - DTW：`librosa.sequence.dtw`
  - 向量库：FAISS（CPU 版即可）
- **LLM（prompt translator）**：本地优先 `Qwen2.5-7B-Instruct` 走 transformers；备选 OpenAI/Anthropic API（环境变量 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）

## 共用 V-A 数据契约

所有模块涉及 V-A 的位置统一用：

```python
@dataclass
class VA:
    valence: float   # ∈ [-1, 1], negative = sad/melancholic, positive = joyful
    arousal: float   # ∈ [-1, 1], low = calm/static, high = energetic/intense
```

## 共用元数据 schema

画作元数据用 dict 表达（不强制 dataclass）：

```python
{
  "id": str,
  "title": str | None,
  "artist": str | None,
  "dynasty": str | None,
  "school": str | None,
  "subject": str | None,
  "medium": str | None,
  "license": str,
  "image_url": str | None,
  "local_path": str,
}
```

## MacBook 友好原则

每个模块的 `demo.py` 必须能在 **MacBook（无 GPU）** 上跑通：
- 跑不动大模型时，用更小的替身或 mock。例：MusicGen 用 `musicgen-small`（300M），不行就 mock 一个 sine wave 输出
- 必要时在 README 列出"MacBook 上跑不动"清单（如：MusicGen-medium fine-tune、LoRA 训练）
- 但**接口形态保持服务器一致**——切换模型只换权重不动 API

## 每个模块的目录约定

```
M*_module_name/
├── README.md          ← 5-10 行：I/O 契约、模型选型、跑法
├── requirements.txt   ← 仅本模块所需，越小越好
├── <core>.py          ← 核心类/函数
├── demo.py            ← 一个用 dummy 输入跑通的端到端示例
└── tests/             ← 可选；pytest 或简单 assert 都行
```

## 不做的事

- ❌ 不要写"框架"——不要 abstract base class、不要 plugin loader、不要 config 引擎
- ❌ 不要 import 其他 M* 模块
- ❌ 不要为不存在的需求写 fallback（"如果没有 GPU 就……"——是的；"如果模型不存在就……"——不要）
- ❌ 不要写完美 typing——基本 typing 即可，别 `TypeVar/Generic/Protocol` 套娃
- ❌ 不要写 README 之外的 markdown 文档

## 做的事

- ✅ 函数签名干净、单一职责
- ✅ 模块根目录 `demo.py` 能 `python demo.py` 直接出结果
- ✅ 数据用 huggingface `datasets`，张量用 torch，音频用 `torchaudio`/`librosa`
- ✅ 输入输出都是 plain dict / torch.Tensor / numpy / pathlib.Path —— 不要新造类型
