# EchoScroll · Module Showcase

> 9 模块 × 3 图 = **27 张可视化**。每张都由对应模块的 `viz.py` 在 MacBook CPU 上直接产出。
> 顶级 3×3 拼图在 [`GALLERY.png`](./GALLERY.png)。

![Gallery](./GALLERY.png)

---

## M1 · Multimodal Encoder

CLIP-ViT-L/14（视觉，768d）+ BGE-M3（中英文，1024d）+ 哈希元数据（256d）→ `FusionHead` → fused `z ∈ ℝ^768`。
*图为可视化用 mock embedding；真模型要 4 GB 下载。*

| | |
|---|---|
| ![](./M1_multimodal_encoder/figures/fig_modality_norms.png) | 4 幅画的 4 类向量 L2 范数对比 |
| ![](./M1_multimodal_encoder/figures/fig_similarity_heatmap.png) | 4 个 z 向量的余弦相似度矩阵 |
| ![](./M1_multimodal_encoder/figures/fig_fusion_diagram.png) | 融合架构示意（3 路输入 → 3 个 W 矩阵 → GELU） |

## M2 · Affective Projection

MLP 768 → 256 → 2（tanh），监督 = MSE + λ·NT-Xent，输出 V-A ∈ [-1,1]²，Russell 8 象限分类。

| | |
|---|---|
| ![](./M2_affective_projection/figures/fig_circumplex.png) | 100 随机预测 + 4 象限渲染 + 8 个方位词 |
| ![](./M2_affective_projection/figures/fig_word_distribution.png) | 8 类词频统计 |
| ![](./M2_affective_projection/figures/fig_loss_components.png) | 50 步 Adam 训练的 MSE / InfoNCE 曲线 |

## M3 · Art-history RAG

BGE-M3 + FAISS IndexFlatIP，20 条种子语料（唐 → 清）+ 朝代 substring 过滤。

| | |
|---|---|
| ![](./M3_art_rag/figures/fig_retrieval_scores.png) | 3 个查询的 top-5 余弦分（EN / EN / ZH） |
| ![](./M3_art_rag/figures/fig_corpus_pca.png) | 20 条语料的 2D PCA 散点（按朝代上色） |
| ![](./M3_art_rag/figures/fig_query_pipeline.png) | painting + text → BGE-M3 → FAISS → top-k |

## M4 · Music Generator

MusicGen-small 真版（`--real` 拉 2 GB）+ MockMusicGenerator（CPU，sine + 颤音）；prompt 拼接 V-A → 情绪形容词 + retrieved snippets。

| | |
|---|---|
| ![](./M4_music_generator/figures/fig_waveforms_va.png) | 3 个 V-A 配置的 5s 波形对比 |
| ![](./M4_music_generator/figures/fig_mel_spectrograms.png) | 同 3 配置的 log-mel 谱图 |
| ![](./M4_music_generator/figures/fig_va_to_pitch_map.png) | mock 的 V-A → 基频 Hz 等高线（valence-only 决定 pitch） |

## M5 · Editing Layer

`librosa.beat.beat_track` 检测 → 段位替换（50ms cross-fade）→ phase-vocoder BPM ×α → style transfer 词表重写。

| | |
|---|---|
| ![](./M5_editing_layer/figures/fig_beat_detection.png) | 波形 + onset envelope，红虚线标 4 个 beat |
| ![](./M5_editing_layer/figures/fig_bpm_stretch.png) | 原始 / ×0.5 / ×1.5 三联（音高不变） |
| ![](./M5_editing_layer/figures/fig_segment_replace.png) | 红框（删）→ 绿框（换） |

## M6 · Prompt Translator

自动选 Anthropic → OpenAI → 本地 Qwen → 规则后备；输出 8-slot 受控词表（tempo / mode / meter / register / instruments / texture / articulation / dynamics）。

| | |
|---|---|
| ![](./M6_prompt_translator/figures/fig_prompt_table.png) | 8 个示例 prompt 的 8-slot 翻译表（diff 高亮） |
| ![](./M6_prompt_translator/figures/fig_slot_heatmap.png) | 同 8 例的 slot×value 热图 |
| ![](./M6_prompt_translator/figures/fig_pipeline.png) | router → LLM / Rule 双路径 → 8-slot JSON |

## M7 · Humming Interaction

pYIN 提 F0 → 12 PC 直方图 + Krumhansl-Schmuckler（major / minor / pentatonic_gong）→ chroma-CQT DTW 对齐 → 转调 cents。

| | |
|---|---|
| ![](./M7_humming_interaction/figures/fig_pitch_contour.png) | A 大调三和弦 hum 的波形 + F0 曲线 |
| ![](./M7_humming_interaction/figures/fig_pitch_class_histogram.png) | 12 PC 直方图 + 3 条 KS 模板重叠（实测 r=0.957） |
| ![](./M7_humming_interaction/figures/fig_dtw_alignment.png) | DTW cost 矩阵 + hum/target chroma + 转调 -300 cents |

## M8 · Frontend + Backend

FastAPI 8 端点（含 WebSocket）+ React+TS+WaveSurfer 6 组件。所有端点 stub，schema 与 M1-M9 数据形状一致。

| | |
|---|---|
| ![](./M8_frontend_backend/figures/fig_system_arch.png) | 3 层架构图（Browser / FastAPI / M1-M9） |
| ![](./M8_frontend_backend/figures/fig_endpoint_flow.png) | 上传 → 生成 → 拖 V-A → 重生成 时序图 |
| ![](./M8_frontend_backend/figures/fig_va_panel_mockup.png) | V-A 圆环面板 UI mockup |

## M9 · Evaluation

V-A 一致性（Pearson）+ FAD（eigh-PSD 平方根）+ CLAP / hash 后备 + librosa MIR + Pydantic 人评 CSV。

| | |
|---|---|
| ![](./M9_evaluation/figures/fig_human_rating.png) | 3 系统 × 5 评测维度的均值±std 分组柱状 |
| ![](./M9_evaluation/figures/fig_va_consistency_scatter.png) | 画 V-A vs 音频 V-A 的散点 + Pearson r |
| ![](./M9_evaluation/figures/fig_metric_summary.png) | 6 维雷达图（A / B / C 三系统） |

---

## 复现

每个模块根目录都有 `viz.py`，独立运行：

```bash
cd echoscroll/M2_affective_projection
pip install -r requirements.txt   # 第一次
python viz.py                     # 写 figures/*.png

# 或一次性全跑
cd echoscroll
for m in M1_multimodal_encoder M2_affective_projection M3_art_rag \
        M4_music_generator M5_editing_layer M6_prompt_translator \
        M7_humming_interaction M8_frontend_backend M9_evaluation; do
  echo "=== $m ==="
  (cd "$m" && python viz.py)
done
python build_gallery.py            # 拼出 GALLERY.png
```

## 哪些 viz 跑了真模型 / 哪些用 mock

| 模块 | 真组件 / mock |
|---|---|
| M1 | 真 `FusionHead`，mock 单模态向量（避开 4 GB 下载）|
| M2 | 全真（随机初始化 + 真 forward + 真 Adam 训练循环）|
| M3 | mock embedder（避 2 GB BGE-M3），真 FAISS / 真 PCA |
| M4 | 真 `MockMusicGenerator`（pitch-from-valence sine + 颤音）|
| M5 | 全真（librosa beat-track / 相位声码器 / cross-fade splice）|
| M6 | 全真（规则后备路径，6+2 prompt 实测翻译）|
| M7 | 全真（pYIN F0 / KS 调性 / chroma-CQT DTW）|
| M8 | 纯架构示意（matplotlib patches；非浏览器截图）|
| M9 | 全真（random-projection FAD 后备 + 真 librosa MIR）|
