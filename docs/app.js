/* ============================================================================
   EchoScroll · Showcase Demo · interaction layer v2
   ============================================================================ */

(() => {
'use strict';

// ============================================================================
// 1. Data
// ============================================================================

const PAINTINGS = [
  {
    id: 'p1', file: 'p1_miyouren_cloudy_mountains.jpg',
    title: '云山图', titleEn: 'Cloudy Mountains',
    artist: 'Mi Youren · 米友仁 (1072–1151)',
    dynasty: '南宋 · Southern Song', dynKey: '南宋',
    tags: ['山水', '水墨', 'CC0'],
    va: [-0.22, -0.55],
    audio: 'real_p1_va_neg_12s.wav',
    audioFull: 'real_p1_va_neg.mp3',
    audioFullLabel: '4:48',
    audioBank: [
      { file: 'real_p1_va_neg_12s.wav', va: [-0.5, -0.5], label: 'V(−0.5,−0.5)·苍凉' },
      { file: 'real_p1_va_pos_12s.wav', va: [+0.5, +0.5], label: 'V(+0.5,+0.5)·明朗' },
    ],
    isReal: true,
    prompt:
      `Instrumental Chinese literati landscape music inspired by Mi Youren's "Cloudy Mountains", Southern Song dynasty ink-wash aesthetics, mist-covered mountains, soft gray clouds, distant peaks fading into silence. Slow guqin and xiao duet, airy dizi textures, subtle pipa harmonics, very sparse percussion, deep low drone like distant earth and water.

Mood: wistful, tender, reflective, slow, flowing
BPM: ~50  ·  No vocals, no pop beat, no orchestral climax
Mode: pentatonic yu  ·  Instruments: guqin, xiao, dizi, pipa, light percussion`,
    rag: [
      { score: 0.42, text: 'Mi Youren built upon his father Mi Fu\'s "ink-dot mountains" style, dissolving solid form into atmospheric Song-dynasty mist.' },
      { score: 0.39, text: 'Southern Song literati painters favored intimate fan and album leaves over monumental compositions; brush economy carries the entire mood.' },
      { score: 0.36, text: 'Wet-ink "Mi-style mountains" prioritize atmospheric perspective over solid form, evoking calm dissolution.' },
    ],
  },
  {
    id: 'p2', file: 'p2_dujin_poet_lin_bu.jpg',
    title: '林逋月夜行吟', titleEn: 'The Poet Lin Bu Wandering in the Moonlight',
    artist: 'Du Jin · 杜堇 (1446–c. 1519)',
    dynasty: '明 · Ming', dynKey: '明',
    tags: ['人物', '设色', '故事画'],
    va: [-0.03, 0.11], audio: 'gua4_bi.mp3',
    rag: [
      { score: 0.35, text: 'Landscape with goats. Late Ming dynasty. Hanging scroll; ink and color on silk.' },
      { score: 0.33, text: 'Du Jin specialized in figure painting that animated Song literati anecdotes within Ming aesthetic conventions.' },
      { score: 0.31, text: 'Garden of Solitary Enjoyment refers to a Song-era site built in 1073 by the statesman Sima Guang as a metaphor for cultivated retreat.' },
    ],
  },
  {
    id: 'p3', file: 'p3_chenruyan_immortals.jpg',
    title: '群仙山图', titleEn: 'Mountains of the Immortals',
    artist: 'Chen Ruyan · 陈汝言 (c. 1331–1371)',
    dynasty: '元 · Yuan', dynKey: '元',
    tags: ['青绿山水', '神仙', '元代'],
    va: [0.35, -0.05], audio: 'gua2_xu.mp3',
    rag: [
      { score: 0.38, text: 'Yuan literati painters fused Daoist immortal-realm imagery with elevated, archaic blue-green palette to express otherworldly ideals.' },
      { score: 0.34, text: 'Chen Ruyan, a Yuan Four Masters circle painter, treats brushwork as scholarly self-expression rather than mere depiction.' },
      { score: 0.32, text: 'Daoist mountain pavilions and pine groves in Yuan painting cite a long tradition of "可游可居" — wandering and dwelling.' },
    ],
  },
  {
    id: 'p4', file: 'p4_juran_buddhist_retreat.jpg',
    title: '溪山兰若图', titleEn: 'Buddhist Retreat by Stream and Mountains',
    artist: 'Juran · 巨然 (active 960–985)',
    dynasty: '北宋 · Northern Song', dynKey: '北宋',
    tags: ['山水', '寺庙', '苍润'],
    va: [-0.36, -0.34], audio: 'gua1_shi.mp3',
    rag: [
      { score: 0.41, text: 'Juran continued Dong Yuan\'s southern-school lineage, characterized by long hemp-fiber texture strokes and dense vegetation.' },
      { score: 0.37, text: 'Buddhist mountain retreats in early Northern Song painting figure renunciation; monumental compositions express cosmic order.' },
      { score: 0.34, text: 'Hemp-fiber cun strokes (披麻皴) build soft, accumulating mountain mass typical of southern Tang to Northern Song masters.' },
    ],
  },
  {
    id: 'p5', file: 'p5_bada_landscape.jpg',
    title: '仿郭忠恕山水', titleEn: 'Landscape after Guo Zhongshu',
    artist: 'Bada Shanren · 八大山人 (1626–1705)',
    dynasty: '清 · Qing', dynKey: '清',
    tags: ['遗民', '简笔', '清初'],
    va: [-0.42, 0.18],
    audio: 'real_p5_va_neg_12s.wav',
    audioFull: 'real_p5_va_neg.mp3',
    audioFullLabel: '5:53',
    audioBank: [
      { file: 'real_p5_va_neg_12s.wav', va: [-0.5, -0.5], label: 'V(−0.5,−0.5)·孤寂' },
      { file: 'real_p5_va_pos_12s.wav', va: [+0.5, +0.5], label: 'V(+0.5,+0.5)·旷达' },
    ],
    isReal: true,
    prompt:
      `Instrumental Chinese literati landscape music inspired by Bada Shanren's "Landscape in the manner of Guo Zhongshu." Austere, sparse, and solitary, evoking steep cliffs, hidden dwellings, tiny wandering figures, and a vast sense of emptiness. Use dry guqin plucks, restrained xiao, occasional guzheng harmonics, very light temple bell or stone chime accents, and almost no percussion. The atmosphere should feel reclusive, cool, elegant, and slightly haunted, reflecting the inner loneliness and proud silence of a Ming loyalist painter.

Mood: wistful, tender, reflective, slow, flowing
BPM: ~70  ·  No vocals, no pop beat, no orchestral climax
Mode: pentatonic yu  ·  Instruments: dry guqin, restrained xiao, guzheng, temple bell, stone chime`,
    rag: [
      { score: 0.44, text: 'Bada Shanren, born a Ming prince, fused stark calligraphic brushwork with cryptic compositions as silent political dissent.' },
      { score: 0.39, text: 'The Four Monks of early Qing painting (Bada, Shitao, Hongren, Kuncan) prized "simplicity" — fewer strokes carrying greater weight.' },
      { score: 0.36, text: '"仿" inscriptions in late-period Bada works invite traditional reading while subverting it through eccentric proportions.' },
    ],
  },
  {
    id: 'p6', file: 'p6_streams_mountains.jpg',
    title: '溪山无尽图', titleEn: 'Streams and Mountains without End',
    artist: 'Anonymous · 佚名',
    dynasty: '北宋-金 · N. Song to Jin', dynKey: '北宋',
    tags: ['手卷', '巨幅', '北宗'],
    va: [-0.05, 0.45], audio: 'real_p1_va_pos.mp3',
    rag: [
      { score: 0.46, text: 'Monumental northern Song hanging scrolls express cosmic principle through commanding axial mountain compositions.' },
      { score: 0.41, text: 'Long handscrolls invite "可游" — a moving, unfolding pictorial journey across rivers, plateaus and human settlements.' },
      { score: 0.38, text: 'Northern landscape masters Li Cheng, Fan Kuan and Guo Xi developed axe-cut texture strokes (斧劈皴) for sharp, rocky surfaces.' },
    ],
  },
  {
    id: 'p7', file: 'p7_nijing_wintry_plum.jpg',
    title: '寒梅图', titleEn: 'Wintry Plum',
    artist: 'Ni Jing · 倪静',
    dynasty: '元-明 · Yuan-Ming', dynKey: '元',
    tags: ['花鸟', '梅', '岁寒'],
    va: [-0.30, -0.42], audio: 'real_p5_va_neg.mp3',
    rag: [
      { score: 0.40, text: 'Plum blossoms in winter symbolize moral integrity — beauty against adversity, a "junzi" emblem in literati art.' },
      { score: 0.37, text: 'Ink plum, bamboo and orchid (四君子) became favored subjects of Yuan literati painters expressing eremitic ideals.' },
      { score: 0.33, text: 'Sparse, calligraphic plum-blossom paintings let blank silk carry the loneliness of cold-season cultivation.' },
    ],
  },
  {
    id: 'p8', file: 'p8_liushiru_plum_snow.jpg',
    title: '雪梅图', titleEn: 'Plum in Snow',
    artist: 'Liu Shiru · 刘世儒',
    dynasty: '明 · Ming', dynKey: '明',
    tags: ['雪景', '梅', '设色'],
    va: [0.12, -0.50], audio: 'gua4_bi.mp3',
    rag: [
      { score: 0.39, text: 'Snow-and-plum compositions transform winter desolation into refined ornamental beauty in Ming literati flower painting.' },
      { score: 0.35, text: 'White silk left bare becomes snow; ink defines branches; minimal color carries early-spring optimism.' },
      { score: 0.32, text: 'Ming-dynasty bird-and-flower painting integrated Song precision with Yuan literati abstraction.' },
    ],
  },
];

const MODULES = [
  { id: 'M1', cn: '多模态编码', en: 'Multimodal Encoder',
    cat: 'perception',
    desc: 'CLIP-ViT-L/14 视觉编码 + BGE-M3 中英双语文本编码 + 元数据哈希嵌入。',
    stat: '768d · 754 LOC', lc: '754 LOC', fc: '3 figs',
    sig: { type: 'formula', html: `<div>z = σ(&nbsp;<em class="var-img">W<sub>v</sub>·e<sub>img</sub></em><span class="op">+</span><em class="var-txt">W<sub>t</sub>·e<sub>txt</sub></em><span class="op">+</span><em class="var-meta">W<sub>m</sub>·e<sub>meta</sub></em><span class="op">+ b</span>&nbsp;)</div>` },
    figs: ['M1_fig_modality_norms.png','M1_fig_similarity_heatmap.png','M1_fig_fusion_diagram.png'] },

  { id: 'M2', cn: '情感投影', en: 'Affective Projection',
    cat: 'perception',
    desc: 'MLP 768 → 256 → 2 把多模态向量映到 Russell 圆环；MSE + NT-Xent 联合监督。',
    stat: '8 sectors · 621 LOC', lc: '621 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust" preserveAspectRatio="xMidYMid meet">
        <g transform="translate(100,32)">
          <circle r="28" fill="none" stroke="currentColor" stroke-width="1"/>
          <line x1="-28" y1="0" x2="28" y2="0" stroke="currentColor" stroke-width="0.5" opacity="0.45"/>
          <line x1="0" y1="-28" x2="0" y2="28" stroke="currentColor" stroke-width="0.5" opacity="0.45"/>
          <path d="M0,0 L28,0 A28,28 0 0,1 0,28 Z" fill="#b88f4e" opacity="0.18"/>
          <path d="M0,0 L0,28 A28,28 0 0,1 -28,0 Z" fill="#2a6e96" opacity="0.18"/>
          <path d="M0,0 L-28,0 A28,28 0 0,1 0,-28 Z" fill="#b8302a" opacity="0.18"/>
          <path d="M0,0 L0,-28 A28,28 0 0,1 28,0 Z" fill="#5e8466" opacity="0.18"/>
          <g class="m2-orbit"><circle cx="0" cy="0" r="3.5" fill="#b8302a"/><circle cx="0" cy="0" r="1.4" fill="#fff"/></g>
        </g>
        <text x="14" y="10" font-size="8" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">arousal+</text>
        <text x="14" y="60" font-size="8" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">arousal−</text>
        <text x="155" y="38" font-size="8" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">val+</text>
      </svg>` },
    figs: ['M2_fig_circumplex.png','M2_fig_word_distribution.png','M2_fig_loss_components.png'] },

  { id: 'M3', cn: '艺术史检索', en: 'Art-history RAG',
    cat: 'perception',
    desc: 'BGE-M3 编码 + FAISS IndexFlatIP 检索；自建 1,129 chunks 中英艺术史语料。',
    stat: '1,129 chunks', lc: '1,214 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="k">0.42</span>&nbsp; Mi Youren · ink-dot mountains</span></div>
      <div class="row"><span><span class="k">0.39</span>&nbsp; Southern Song fan / album leaves</span></div>
      <div class="row"><span><span class="k">0.36</span>&nbsp; Wet-ink atmospheric perspective</span></div>` },
    figs: ['M3_fig_retrieval_scores.png','M3_fig_corpus_pca.png','M3_fig_query_pipeline.png'] },

  { id: 'M4', cn: '音乐生成', en: 'Music Generator',
    cat: 'generation',
    desc: 'MusicGen-small + LoRA wiring + Mock 后备；接受 V-A、RAG、口语指令三联条件。',
    stat: '32 kHz · 677 LOC', lc: '677 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust m4-svg" preserveAspectRatio="xMidYMid meet">
        <g class="m4-bars" fill="currentColor">
          ${Array.from({length: 26}, (_, i) => {
            const x = 8 + i * 7.3;
            const h = 8 + Math.abs(Math.sin(i * 0.7) + Math.sin(i * 0.31)) * 18;
            const y = 32 - h/2;
            return `<rect x="${x}" y="${y}" width="3.2" height="${h}" rx="1"/>`;
          }).join('')}
        </g>
      </svg>` },
    figs: ['M4_fig_waveforms_va.png','M4_fig_mel_spectrograms.png','M4_fig_va_to_pitch_map.png'] },

  { id: 'M5', cn: '编辑层', en: 'Editing Layer',
    cat: 'interaction',
    desc: '节拍检测 + 段位替换（cross-fade）+ 相位声码器 BPM 变速 + style 重写。',
    stat: '4 ops · 753 LOC', lc: '753 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="k">edit_ops</span> = [</span></div>
      <div class="row" style="padding-left: 14px"><span><span class="s">'beat-replace'</span>,&nbsp; <span class="s">'bpm-vocoder'</span>,</span></div>
      <div class="row" style="padding-left: 14px"><span><span class="s">'style-swap'</span>,&nbsp; <span class="s">'segment-regen'</span></span></div>
      <div class="row"><span>]&nbsp;&nbsp;<span class="k">→</span> <span class="n">±0.2%</span> dur</span></div>` },
    figs: ['M5_fig_beat_detection.png','M5_fig_bpm_stretch.png','M5_fig_segment_replace.png'] },

  { id: 'M6', cn: '口语翻译', en: 'Prompt Translator',
    cat: 'interaction',
    desc: '自动选择 Anthropic / OpenAI / Qwen / 规则后备；输出 8-slot 受控音乐参数。',
    stat: '8 slots · 967 LOC', lc: '967 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="s">"再空一点"</span><span class="arrow">→</span><span class="k">texture</span>: <span class="s">'sparse'</span></span></div>
      <div class="row"><span><span class="s">"更激烈"</span><span class="arrow">→</span><span class="k">tempo</span>: <span class="s">'fast'</span></span></div>
      <div class="row"><span><span class="s">"古风加琴"</span><span class="arrow">→</span><span class="k">inst</span>: [guqin]</span></div>` },
    figs: ['M6_fig_prompt_table.png','M6_fig_slot_heatmap.png','M6_fig_pipeline.png'] },

  { id: 'M7', cn: '哼唱交互', en: 'Humming Interaction',
    cat: 'interaction',
    desc: 'pYIN F0 提取 + Krumhansl-Schmuckler 调性识别 + chroma-CQT DTW 转调对齐。',
    stat: 'r=0.957 · 757 LOC', lc: '757 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust" preserveAspectRatio="xMidYMid meet">
        <line x1="6" y1="56" x2="194" y2="56" stroke="currentColor" stroke-width="0.4" opacity="0.4"/>
        <line x1="6" y1="32" x2="194" y2="32" stroke="currentColor" stroke-width="0.3" opacity="0.18" stroke-dasharray="2 3"/>
        <path class="m7-curve" d="M6,42 Q 28,12 50,28 T 90,18 T 130,30 T 170,16 T 194,24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        <g fill="currentColor">
          <circle cx="6" cy="42" r="1.6"/>
          <circle cx="50" cy="28" r="1.6"/>
          <circle cx="90" cy="18" r="1.6"/>
          <circle cx="130" cy="30" r="1.6"/>
          <circle cx="170" cy="16" r="1.6"/>
        </g>
        <text x="180" y="56" font-size="7" font-family="JetBrains Mono" fill="currentColor" opacity="0.6">A major</text>
      </svg>` },
    figs: ['M7_fig_pitch_contour.png','M7_fig_pitch_class_histogram.png','M7_fig_dtw_alignment.png'] },

  { id: 'M8', cn: '前后端', en: 'Frontend + Backend',
    cat: 'interface',
    desc: 'FastAPI 8 端点 + WebSocket 进度推送；React + TypeScript + WaveSurfer 6 组件。',
    stat: '8 endpoints · 1.1k LOC', lc: '1,105 LOC', fc: '3 figs',
    sig: { type: 'snippet', html: `
      <div class="row"><span><span class="k">POST</span> /upload</span><span style="opacity:0.5">multipart</span></div>
      <div class="row"><span><span class="k">POST</span> /generate</span><span style="opacity:0.5">audio.wav</span></div>
      <div class="row"><span><span class="k">POST</span> /edit/<span class="s">va | prompt | humming</span></span></div>
      <div class="row"><span><span class="k">WS</span>&nbsp;&nbsp; /ws/preview</span><span style="opacity:0.5">progress</span></div>` },
    figs: ['M8_fig_system_arch.png','M8_fig_endpoint_flow.png','M8_fig_va_panel_mockup.png'] },

  { id: 'M9', cn: '评测', en: 'Evaluation',
    cat: 'evaluation',
    desc: 'V-A 一致性 (Pearson) + FAD (eigh-PSD) + CLAP-style + librosa MIR + Pydantic 人评 CSV。',
    stat: '5 dims · 1.1k LOC', lc: '1,077 LOC', fc: '3 figs',
    sig: { type: 'svg', html: `
      <svg viewBox="0 0 200 64" class="mc-illust" preserveAspectRatio="xMidYMid meet">
        <line x1="6" y1="56" x2="194" y2="56" stroke="currentColor" stroke-width="0.4" opacity="0.5"/>
        <g class="m9-bar"><rect x="16" y="14" width="14" height="42" rx="1.5" fill="currentColor" opacity="0.95"/></g>
        <g class="m9-bar"><rect x="42" y="22" width="14" height="34" rx="1.5" fill="currentColor" opacity="0.85"/></g>
        <g class="m9-bar"><rect x="68" y="10" width="14" height="46" rx="1.5" fill="currentColor" opacity="0.92"/></g>
        <g class="m9-bar"><rect x="94" y="20" width="14" height="36" rx="1.5" fill="currentColor" opacity="0.78"/></g>
        <g class="m9-bar"><rect x="120" y="16" width="14" height="40" rx="1.5" fill="currentColor" opacity="0.88"/></g>
        <text x="23" y="11" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">VA</text>
        <text x="49" y="19" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">FAD</text>
        <text x="75" y="7" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">cult</text>
        <text x="101" y="17" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">qual</text>
        <text x="127" y="13" font-size="6.5" font-family="JetBrains Mono" fill="currentColor" text-anchor="middle">pref</text>
        <text x="170" y="34" font-size="9" font-family="Cormorant Garamond" font-style="italic" fill="currentColor" opacity="0.7">A &gt; B,C</text>
      </svg>` },
    figs: ['M9_fig_human_rating.png','M9_fig_va_consistency_scatter.png','M9_fig_metric_summary.png'] },
];

// Audio variants available for V-A driven swap
// AUDIO_BANK · 全部真音乐（无任何 mock / 合成）
const AUDIO_BANK = [
  { file: 'gua1_shi.mp3',         va: [-0.10, -0.40], label: '师卦·沉聚' },
  { file: 'gua2_xu.mp3',          va: [+0.45, +0.25], label: '需卦·明展' },
  { file: 'gua3_song.mp3',        va: [-0.50, +0.55], label: '讼卦·躁争' },
  { file: 'gua4_bi.mp3',          va: [+0.25, -0.10], label: '比卦·温润' },
  { file: 'real_p1_va_neg.mp3',   va: [-0.22, -0.55], label: '云山图·沉' },
  { file: 'real_p1_va_pos.mp3',   va: [+0.30, +0.50], label: '云山图·明' },
  { file: 'real_p5_va_neg.mp3',   va: [-0.42, +0.18], label: '八大山人·孤' },
  { file: 'real_p5_va_pos.mp3',   va: [+0.40, +0.40], label: '八大山人·达' },
];

// ============================================================================
// 2. V-A → word + descriptors (mirrors M2 + M6)
// ============================================================================

function vaToWord(v, a) {
  const r = Math.hypot(v, a);
  if (r < 0.15) return 'tender';
  const theta = Math.atan2(a, v);
  const sectors = [
    { lo: -Math.PI/8,        hi:  Math.PI/8,        word: 'calm' },
    { lo:  Math.PI/8,        hi:  3*Math.PI/8,      word: 'excited' },
    { lo:  3*Math.PI/8,      hi:  5*Math.PI/8,      word: 'joyful' },
    { lo:  5*Math.PI/8,      hi:  7*Math.PI/8,      word: 'tense' },
    { lo:  7*Math.PI/8,      hi:  Math.PI + 1e-3,   word: 'angry' },
    { lo: -Math.PI - 1e-3,   hi: -7*Math.PI/8,      word: 'angry' },
    { lo: -7*Math.PI/8,      hi: -5*Math.PI/8,      word: 'sad' },
    { lo: -5*Math.PI/8,      hi: -3*Math.PI/8,      word: 'melancholic' },
    { lo: -3*Math.PI/8,      hi: -Math.PI/8,        word: 'tender' },
  ];
  for (const s of sectors) if (theta >= s.lo && theta < s.hi) return s.word;
  return 'tender';
}

const INSTRUMENTS_BY_QUADRANT = {
  'pp': ['guzheng', 'dizi'],
  'pn': ['guqin', 'xiao'],
  'np': ['pipa', 'erhu'],
  'nn': ['xiao', 'guqin'],
};

function vaToDescriptors(v, a) {
  const tempo =
    a >  0.45 ? 'very fast' :
    a >  0.15 ? 'fast' :
    a > -0.15 ? 'moderate' :
    a > -0.45 ? 'slow' : 'very slow';
  const dynamics =
    a < -0.55 ? 'pp' :
    a < -0.25 ? 'p' :
    a <  0.05 ? 'mp' :
    a <  0.35 ? 'mf' :
    a <  0.65 ? 'f' : 'ff';
  const texture =
    a < -0.25 ? 'sparse' :
    a >  0.25 ? 'dense' : 'moderate';
  const articulation = a > 0.3 ? 'staccato' : 'legato';
  const register =
    a < -0.3 ? 'low' :
    a >  0.3 ? 'high' : 'mid';
  const meter = Math.abs(a) > 0.45 ? '4/4' : 'free';
  let mode;
  if (v < -0.25) mode = 'pentatonic_yu';
  else if (v > 0.25) mode = 'pentatonic_zhi';
  else mode = 'pentatonic_gong';
  const quad = (v >= 0 ? 'p' : 'n') + (a >= 0 ? 'p' : 'n');
  const instrumentation = INSTRUMENTS_BY_QUADRANT[quad];
  return { tempo, mode, meter, register, texture, dynamics, articulation, instrumentation };
}

// Nearest-audio in V-A space (used when user drags significantly)
// If a per-painting bank is provided, search it; else fall back to global AUDIO_BANK.
function nearestAudio(v, a, bank) {
  const pool = bank && bank.length ? bank : AUDIO_BANK;
  let best = pool[0], bestD = Infinity;
  for (const b of pool) {
    const d = (b.va[0] - v) ** 2 + (b.va[1] - a) ** 2;
    if (d < bestD) { bestD = d; best = b; }
  }
  return best;
}

// ============================================================================
// 3. DOM helpers
// ============================================================================

const $  = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));

// ============================================================================
// 4. Nav scroll state
// ============================================================================

const nav = $('#nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 60);
});

// ============================================================================
// 5. IntersectionObserver — fade-in + stagger + counter
// ============================================================================

const observer = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      if (e.target.dataset.count) animateCount(e.target, parseInt(e.target.dataset.count, 10));
      if (e.target.classList.contains('number-cell'))
        $$('[data-count]', e.target).forEach(el => animateCount(el, parseInt(el.dataset.count, 10)));
      observer.unobserve(e.target);
    }
  }
}, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

$$('.fade-in, .stagger, [data-count], .number-cell, .pipeline, .section-head').forEach(el => observer.observe(el));

function animateCount(el, target) {
  const dur = 1400;
  const start = performance.now();
  const sup = el.querySelector('sup');
  const supHtml = sup ? sup.outerHTML : '';
  function step(now) {
    const t = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = Math.round(target * eased);
    el.innerHTML = val.toLocaleString() + supHtml;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ============================================================================
// 6. Hero painting rotation + Ken Burns
// ============================================================================

let heroIndex = 0;
const heroImgs = $$('#hero-painting-stack img');
const heroCapTitle = $('#hero-caption-title');
const heroCapMeta = $('#hero-caption-meta');
const heroCaptions = {
  p1: { title: '云山图',          meta: 'Mi Youren · 南宋' },
  p3: { title: '群仙山图',        meta: 'Chen Ruyan · 元' },
  p6: { title: '溪山无尽图',      meta: 'Anonymous · 北宋-金' },
  p2: { title: '林逋月夜行吟',    meta: 'Du Jin · 明' },
};

function rotateHero() {
  heroImgs[heroIndex].classList.remove('active');
  heroIndex = (heroIndex + 1) % heroImgs.length;
  heroImgs[heroIndex].classList.add('active');
  const pid = heroImgs[heroIndex].dataset.pid;
  const cap = heroCaptions[pid];
  if (cap) {
    heroCapTitle.textContent = cap.title;
    heroCapMeta.textContent = cap.meta;
  }
}
setInterval(rotateHero, 7200);

// ============================================================================
// 7. Painting picker + thumbs + V-A dots on circumplex
// ============================================================================

let currentPainting = PAINTINGS[1]; // boot with Du Jin
let currentVA = [...currentPainting.va];
let userDraggedFar = false;

// Build thumbs
const thumbsEl = $('#painting-thumbs');
PAINTINGS.forEach((p, i) => {
  const t = document.createElement('div');
  t.className = 'thumb' + (i === 1 ? ' active' : '');
  t.dataset.id = p.id;
  t.innerHTML = `<img src="assets/paintings/${p.file}" alt="${p.titleEn}" loading="lazy" decoding="async">`;
  t.addEventListener('click', () => selectPainting(p.id));
  thumbsEl.appendChild(t);
});

// Build painting dots on circumplex (placed in <g id="va-dots">)
const vaDotsGroup = $('#va-dots');
const dotTip = $('#va-dot-tip');
function renderPaintingDots() {
  vaDotsGroup.innerHTML = '';
  PAINTINGS.forEach((p) => {
    const x = p.va[0] * 100;
    const y = -p.va[1] * 100;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('va-painting-dot');
    g.setAttribute('transform', `translate(${x},${y})`);
    g.dataset.id = p.id;
    g.innerHTML = `
      <circle class="halo" r="6" />
      <circle class="core" r="3.2" />
    `;
    g.addEventListener('mouseenter', (e) => {
      const rect = $('#va-circumplex').getBoundingClientRect();
      const svgRect = $('#va-svg').getBoundingClientRect();
      const scaleX = svgRect.width / 220;
      const scaleY = svgRect.height / 220;
      const cx = svgRect.left + (x + 110) * scaleX - rect.left;
      const cy = svgRect.top + (y + 110) * scaleY - rect.top;
      dotTip.style.left = cx + 'px';
      dotTip.style.top  = cy + 'px';
      dotTip.textContent = `${p.title} · ${p.dynKey}`;
      dotTip.classList.add('show');
    });
    g.addEventListener('mouseleave', () => dotTip.classList.remove('show'));
    g.addEventListener('click', () => selectPainting(p.id));
    vaDotsGroup.appendChild(g);
  });
  highlightActiveDot();
}
function highlightActiveDot() {
  $$('.va-painting-dot', vaDotsGroup).forEach(el => {
    el.classList.toggle('active', el.dataset.id === currentPainting.id);
  });
}

function selectPainting(id) {
  const p = PAINTINGS.find(x => x.id === id);
  if (!p) return;
  currentPainting = p;
  currentVA = [...p.va];
  userDraggedFar = false;

  // swap image with fade
  const frame = $('#painting-frame');
  const img = $('#painting-img');
  frame.classList.add('changing');
  setTimeout(() => {
    img.src = `assets/paintings/${p.file}`;
    img.alt = p.titleEn;
    frame.classList.remove('changing');
  }, 240);

  // meta
  $('#painting-title').textContent = p.title;
  $('#painting-sub').textContent = `${p.artist} · ${p.titleEn}`;
  const tagsEl = $('#painting-tags');
  tagsEl.innerHTML = `<span class="tag dyn">${p.dynasty}</span>` +
    p.tags.map(t => `<span class="tag">${t}</span>`).join('');

  // thumbs active
  $$('.thumb', thumbsEl).forEach(t => t.classList.toggle('active', t.dataset.id === p.id));

  // V-A pin + descriptors + word + dots
  setVA(p.va[0], p.va[1], true);
  highlightActiveDot();

  // RAG (re-render to retrigger CSS slide-in)
  renderRag(p.rag);

  // audio variants (per-painting bank if defined, else global)
  renderAudioVariants(p);

  // audio
  loadAudio('assets/audio/' + p.audio);
  $$('.audio-variants button').forEach(b => b.classList.toggle('active', b.dataset.audio === 'assets/audio/' + p.audio));

  // real-music note (prompt + full-length playback)
  updateRealAudioPanel(p);

  // update code panel
  refreshCodePanel();
}

// ============================================================================
// 7b. Per-painting audio variants UI (rebuilds button row + binds clicks)
// ============================================================================

function renderAudioVariants(p) {
  const bank = p.audioBank && p.audioBank.length ? p.audioBank : AUDIO_BANK;
  const container = $('.audio-variants');
  if (!container) return;
  container.innerHTML = bank.map(b => {
    const url = 'assets/audio/' + b.file;
    const active = b.file === p.audio ? ' class="active"' : '';
    return `<button data-audio="${url}"${active}>${b.label}</button>`;
  }).join('');
}

// Real-music panel: shows "this is real MusicGen output" + prompt expander
// + "完整聆听 X:XX" button. Hides cleanly when current painting has no isReal flag.
function updateRealAudioPanel(p) {
  const panel = $('#real-audio-note');
  if (!panel) return;
  if (!p.isReal) { panel.hidden = true; return; }
  panel.hidden = false;
  const promptHtml = (p.prompt || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');
  panel.innerHTML = `
    <div class="ran-head">
      <span class="ran-badge"><span class="ran-dot"></span>真音乐 · MusicGen-small + LoRA</span>
      <button class="ran-full" id="ran-full-btn" data-full="assets/audio/${p.audioFull}">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
        完整聆听 · ${p.audioFullLabel || ''}
      </button>
      <button class="ran-toggle" id="ran-toggle-btn" aria-expanded="false">▾ 看 prompt</button>
    </div>
    <pre class="ran-prompt" id="ran-prompt" hidden>${promptHtml}</pre>
  `;
  const fullBtn = $('#ran-full-btn');
  fullBtn.addEventListener('click', () => {
    loadAudio(fullBtn.dataset.full, true);
    $$('.audio-variants button').forEach(b => b.classList.remove('active'));
  });
  const toggleBtn = $('#ran-toggle-btn');
  const promptEl  = $('#ran-prompt');
  toggleBtn.addEventListener('click', () => {
    const open = promptEl.hidden;
    promptEl.hidden = !open;
    toggleBtn.textContent = open ? '▴ 收起 prompt' : '▾ 看 prompt';
    toggleBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
}

// ============================================================================
// 8. V-A circumplex — drag + live tone + audio swap
// ============================================================================

const svg = $('#va-svg');
const pin = $('#va-pin');
const wordEl = $('#va-word');
const coordEl = $('#va-coord');
let dragging = false;

function vaToPin(v, a) {
  return { x: v * 100, y: -a * 100 };
}

function setVA(v, a, animate = false) {
  v = Math.max(-1, Math.min(1, v));
  a = Math.max(-1, Math.min(1, a));
  currentVA = [v, a];
  const { x, y } = vaToPin(v, a);
  if (animate) {
    pin.style.transition = 'transform 700ms cubic-bezier(0.4,0,0.2,1)';
    setTimeout(() => pin.style.transition = '', 800);
  } else {
    pin.style.transition = '';
  }
  pin.setAttribute('transform', `translate(${x},${y})`);
  wordEl.textContent = vaToWord(v, a);
  coordEl.textContent = `v = ${v.toFixed(2)}  ·  a = ${a.toFixed(2)}`;
  const colorMap = {
    calm:'#b88f4e', excited:'#5e8466', joyful:'#5e8466',
    tense:'#b8302a', angry:'#b8302a', sad:'#2a6e96',
    melancholic:'#2a6e96', tender:'#b88f4e',
  };
  wordEl.style.color = colorMap[wordEl.textContent] || 'var(--ink-dark)';
  renderDescriptors(vaToDescriptors(v, a));
  refreshCodePanel();
}

function clientToVA(clientX, clientY) {
  const rect = svg.getBoundingClientRect();
  const xPct = (clientX - rect.left) / rect.width;
  const yPct = (clientY - rect.top) / rect.height;
  const v = (xPct * 2 - 1) * 1.1;
  const a = -((yPct * 2 - 1) * 1.1);
  return [
    Math.max(-1, Math.min(1, v)),
    Math.max(-1, Math.min(1, a)),
  ];
}

function startDrag(e) {
  dragging = true;
  svg.classList.add('dragging');
  markInteracted();
  startTone();
  moveDrag(e);
}
function moveDrag(e) {
  if (!dragging) return;
  e.preventDefault();
  const pt = e.touches ? e.touches[0] : e;
  const [v, a] = clientToVA(pt.clientX, pt.clientY);
  setVA(v, a);
  updateTone(v, a);
  // check if user has drifted far from painting's preset
  const dx = v - currentPainting.va[0];
  const dy = a - currentPainting.va[1];
  if (Math.hypot(dx, dy) > 0.30) userDraggedFar = true;
}
function endDrag() {
  if (!dragging) return;
  dragging = false;
  svg.classList.remove('dragging');
  stopTone(true);
  // If user dragged far, swap to nearest audio variant (use per-painting bank if any)
  if (userDraggedFar) {
    const nearest = nearestAudio(currentVA[0], currentVA[1], currentPainting && currentPainting.audioBank);
    const url = 'assets/audio/' + nearest.file;
    const activeBtn = $('.audio-variants button.active');
    const currentSrc = activeBtn ? activeBtn.dataset.audio : null;
    if (url !== currentSrc) {
      loadAudio(url, false);
      $$('.audio-variants button').forEach(b => b.classList.toggle('active', b.dataset.audio === url));
    }
  }
}

// V-A drag handlers — bind on document so dragging continues outside SVG
svg.addEventListener('mousedown', startDrag);
window.addEventListener('mousemove', moveDrag);
window.addEventListener('mouseup', endDrag);
svg.addEventListener('touchstart', startDrag, { passive: false });
window.addEventListener('touchmove', moveDrag, { passive: false });
window.addEventListener('touchend', endDrag);

// ============================================================================
// 9. Live audio preview (mirrors MockMusicGenerator)
// ============================================================================

let audioCtx = null;
let osc1 = null, osc2 = null, gainNode = null, lfo = null, lfoGain = null, vibrato = null, vibratoGain = null;
let toneActive = false;

function ensureCtx() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();
}

// V-A 拖动实时反馈：旧版用 Oscillator 合成 sine（被诟病为"杂音"），
// 已改为 no-op；拖动只更新 UI / 描述符，松手后切换真音乐 mp3 。
function startTone()         { /* no-op — 不合成 sine */ }
function updateTone(_v, _a)  { /* no-op */ }
function stopTone(_fade)     { /* no-op */ }

// 预览按钮：直接播放当前选中的真音乐变体（不再合成 sine）
$('#btn-preview').addEventListener('click', () => {
  const active = $('.audio-variants button.active');
  if (active) loadAudio(active.dataset.audio, true);
});

$('#btn-regen').addEventListener('click', () => {
  const btn = $('#btn-regen');
  const original = btn.textContent;
  btn.textContent = '生成中…';
  btn.disabled = true;
  // simulate latency + slot pulse + waveform shimmer
  $$('.slot').forEach(s => { s.classList.add('flash'); setTimeout(() => s.classList.remove('flash'), 800); });
  $('#waveform').classList.add('wf-loading');
  setTimeout(() => {
    btn.textContent = original;
    btn.disabled = false;
    $('#waveform').classList.remove('wf-loading');
    const active = $('.audio-variants button.active');
    if (active) loadAudio(active.dataset.audio, true);
  }, 1100);
});

// ============================================================================
// 10. Descriptors render
// ============================================================================

function renderDescriptors(d) {
  const grid = $('#slot-grid');
  $$('.slot', grid).forEach(slot => {
    const key = $('.slot-value', slot).dataset.slot;
    const val = d[key];
    const valEl = $('.slot-value', slot);
    if (key === 'instrumentation' && Array.isArray(val)) {
      valEl.textContent = val.join(' · ');
    } else {
      valEl.textContent = val;
    }
    const isNeutral = ['moderate', 'mp', 'legato', 'mid', '4/4', 'pentatonic_gong'].includes(val);
    slot.classList.toggle('highlight', !isNeutral && key !== 'instrumentation');
  });
}

// ============================================================================
// 11. Audio player — REAL waveform via Web Audio decode
// ============================================================================

const audioEl = $('#audio-el');
const playBtn = $('#play-btn');
const timeEl = $('#audio-time');
const wfEl = $('#waveform');
const NUM_BARS = 64;
let currentPeaks = new Array(NUM_BARS).fill(0.3);

function buildBars(peaks) {
  wfEl.innerHTML = '';
  for (let i = 0; i < NUM_BARS; i++) {
    const b = document.createElement('div');
    b.className = 'wf-bar';
    const h = Math.max(0.12, peaks[i] || 0.2);
    b.style.height = (h * 100) + '%';
    wfEl.appendChild(b);
  }
}
buildBars(currentPeaks);

async function decodeWaveform(url) {
  try {
    ensureCtx();
    const res = await fetch(url);
    const buf = await res.arrayBuffer();
    const audio = await audioCtx.decodeAudioData(buf);
    const data = audio.getChannelData(0);
    const block = Math.floor(data.length / NUM_BARS);
    const peaks = [];
    for (let i = 0; i < NUM_BARS; i++) {
      let sum = 0;
      let pk = 0;
      for (let j = 0; j < block; j++) {
        const s = data[i * block + j];
        sum += s * s;
        if (Math.abs(s) > pk) pk = Math.abs(s);
      }
      // mix RMS + peak for visual richness
      const rms = Math.sqrt(sum / block);
      peaks.push(0.4 * rms + 0.6 * pk);
    }
    const max = Math.max(...peaks);
    return peaks.map(p => p / (max || 1));
  } catch (err) {
    console.warn('waveform decode failed:', err);
    // fallback to deterministic sine
    return Array.from({ length: NUM_BARS }, (_, i) => {
      const t = i / NUM_BARS;
      return 0.4 + 0.45 * Math.abs(Math.sin(t * Math.PI * 3.7) * Math.sin(t * Math.PI * 1.3 + 0.4));
    });
  }
}

// 首次用户交互前，loadAudio() 只缓存 src，绝不写到 audioEl.src 也不 fetch
// —— Chrome 在某些情况下即使 preload=none 也会因 audio.src= 触发拉取，
//    所以彻底延迟到 markInteracted() 之后再设 src。
let hasUserInteracted = false;
let pendingSrc = null;
async function loadAudio(src, autoplay = false) {
  if (!hasUserInteracted && !autoplay) {
    // 仅暂存 src，等用户首次点 ▶ 或切音频按钮时再真加载
    pendingSrc = src;
    timeEl.textContent = '0:00 / 0:00';
    return;
  }
  audioEl.src = src;
  audioEl.load();
  if (autoplay) audioEl.play().catch(() => {});
  else { audioEl.pause(); }
  playBtn.classList.toggle('playing', autoplay);
  updateWaveform(0);
  timeEl.textContent = '0:00 / 0:00';
  wfEl.classList.add('wf-loading');
  currentPeaks = await decodeWaveform(src);
  wfEl.classList.remove('wf-loading');
  buildBars(currentPeaks);
}

// 首次用户交互后激活真加载
function markInteracted() {
  if (hasUserInteracted) return;
  hasUserInteracted = true;
  if (pendingSrc) loadAudio(pendingSrc, false);
}

function fmt(s) {
  if (!isFinite(s)) return '0:00';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60).toString().padStart(2, '0');
  return `${m}:${sec}`;
}

function updateWaveform(progress) {
  const bars = $$('.wf-bar', wfEl);
  const lit = Math.round(progress * bars.length);
  bars.forEach((b, i) => b.classList.toggle('played', i < lit));
}

audioEl.addEventListener('timeupdate', () => {
  if (audioEl.duration) {
    updateWaveform(audioEl.currentTime / audioEl.duration);
    timeEl.textContent = `${fmt(audioEl.currentTime)} / ${fmt(audioEl.duration)}`;
  }
});
audioEl.addEventListener('loadedmetadata', () => {
  timeEl.textContent = `0:00 / ${fmt(audioEl.duration)}`;
});
audioEl.addEventListener('ended', () => {
  playBtn.classList.remove('playing');
  updateWaveform(0);
});

playBtn.addEventListener('click', () => {
  ensureCtx();
  markInteracted();
  if (audioEl.paused) { audioEl.play().catch(() => {}); playBtn.classList.add('playing'); }
  else { audioEl.pause(); playBtn.classList.remove('playing'); }
});

wfEl.addEventListener('click', (e) => {
  markInteracted();
  if (!audioEl.duration) return;
  const rect = wfEl.getBoundingClientRect();
  audioEl.currentTime = ((e.clientX - rect.left) / rect.width) * audioEl.duration;
});

// Event delegation — buttons are rebuilt per painting in renderAudioVariants()
$('.audio-variants')?.addEventListener('click', (e) => {
  const b = e.target.closest('button[data-audio]');
  if (!b) return;
  markInteracted();
  $$('.audio-variants button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  loadAudio(b.dataset.audio, true);
});

// ============================================================================
// 12. RAG list (re-render with CSS slide-in)
// ============================================================================

function renderRag(items) {
  const list = $('#rag-list');
  list.innerHTML = '';
  // force reflow to retrigger animation
  void list.offsetWidth;
  list.innerHTML = items.map(r => `
    <div class="rag-item">
      <span class="rag-score">${r.score.toFixed(2)}</span>${r.text}
    </div>
  `).join('');
}

// ============================================================================
// 13. Module grid + figure hover-rotation + Lightbox
// ============================================================================

const moduleGrid = $('#module-grid');
MODULES.forEach(m => {
  const card = document.createElement('div');
  card.className = `module-card cat-${m.cat}`;
  // Use the headline figure as the small thumb
  const thumbFig = m.figs[0];
  const sigClass = m.sig.type === 'formula' ? 'formula' :
                   m.sig.type === 'svg'      ? 'svg-illust' : 'snippet';
  card.innerHTML = `
    <div class="mc-head">
      <div class="mc-thumb"><img src="assets/figures/${thumbFig}" alt=""></div>
      <div class="mc-head-text">
        <span class="mc-id">${m.id} · Module</span>
        <span class="mc-en">${m.en}</span>
      </div>
    </div>
    <h4>${m.cn}</h4>
    <div class="mc-sig ${sigClass}">${m.sig.html}</div>
    <p class="mc-desc">${m.desc}</p>
    <div class="mc-foot">
      <div class="mc-figs">
        ${m.figs.map((f, i) => `<span class="mini-fig" data-fig-idx="${i}" style="background-image:url('assets/figures/${f}')"></span>`).join('')}
      </div>
      <div class="mc-stat">
        <span class="key">${m.stat}</span>
        <span class="arrow">→</span>
      </div>
    </div>
  `;

  // mini-fig click opens lightbox jumping to that figure (still uses existing lightbox)
  $$('.mini-fig', card).forEach((mf, idx) => {
    mf.addEventListener('click', (e) => {
      e.stopPropagation();
      openLightbox(m, idx);
    });
  });

  card.addEventListener('click', () => openLightbox(m));
  moduleGrid.appendChild(card);
});

const lb = $('#lightbox');
const lbClose = $('#lightbox-close');
const lbTitle = $('#lb-title');
const lbDesc = $('#lb-desc');
const lbFigs = $('#lb-figs');

function openLightbox(m, focusIdx = -1) {
  lbTitle.textContent = `${m.id} · ${m.cn} · ${m.en}`;
  lbDesc.textContent = m.desc;
  lbFigs.innerHTML = m.figs.map((f, i) =>
    `<img src="assets/figures/${f}" alt="${f}" data-i="${i}" ${i === focusIdx ? 'style="outline:3px solid var(--seal); outline-offset:2px;"' : ''}>`).join('');
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
  if (focusIdx >= 0) {
    setTimeout(() => {
      const target = lbFigs.querySelector(`[data-i="${focusIdx}"]`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
  }
}
function closeLightbox() {
  lb.classList.remove('open');
  document.body.style.overflow = '';
}
lbClose.addEventListener('click', closeLightbox);
lb.addEventListener('click', (e) => { if (e.target === lb) closeLightbox(); });
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });

// ============================================================================
// 14. Pipeline step hover → highlight
// ============================================================================

$$('.pipe-step').forEach((s) => {
  s.addEventListener('mouseenter', () => {
    $$('.pipe-step').forEach(x => x.classList.remove('active'));
    s.classList.add('active');
  });
});

// ============================================================================
// 15. Code transparency panel — live JSON state
// ============================================================================

const codePanel = $('#code-panel');
const codeToggle = $('#code-panel-toggle');
const codePre = $('#code-panel-pre');
const codeCopy = $('#code-panel-copy');
let codeTab = 'painting';

codeToggle.addEventListener('click', () => {
  codePanel.classList.toggle('expanded');
});
$$('.code-panel-tab').forEach(t => {
  t.addEventListener('click', () => {
    codeTab = t.dataset.tab;
    $$('.code-panel-tab').forEach(x => x.classList.toggle('active', x === t));
    refreshCodePanel();
  });
});
codeCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(codePre.textContent).then(() => {
    codeCopy.textContent = 'copied!';
    setTimeout(() => codeCopy.textContent = 'copy', 1400);
  });
});

function colorizeJson(obj) {
  let s = JSON.stringify(obj, null, 2);
  s = s.replace(/"([^"]+)"(\s*:)/g, '<span class="key">"$1"</span>$2');
  s = s.replace(/:\s*"([^"]+)"/g, ': <span class="str">"$1"</span>');
  s = s.replace(/:\s*(-?\d+\.?\d*)/g, ': <span class="num">$1</span>');
  s = s.replace(/:\s*(true|false|null)/g, ': <span class="bool">$1</span>');
  return s;
}

function refreshCodePanel() {
  let data;
  if (codeTab === 'painting') {
    data = {
      id: currentPainting.id,
      title: currentPainting.title,
      title_en: currentPainting.titleEn,
      artist: currentPainting.artist,
      dynasty: currentPainting.dynasty,
      tags: currentPainting.tags,
      license: 'CC0 / public domain',
    };
  } else if (codeTab === 'va') {
    data = {
      valence: parseFloat(currentVA[0].toFixed(3)),
      arousal: parseFloat(currentVA[1].toFixed(3)),
      word: vaToWord(currentVA[0], currentVA[1]),
      source: 'M2 ▸ MLP(z) ▸ tanh',
      drift_from_preset: parseFloat(
        Math.hypot(currentVA[0] - currentPainting.va[0], currentVA[1] - currentPainting.va[1]).toFixed(3)
      ),
    };
  } else if (codeTab === 'descriptors') {
    data = vaToDescriptors(currentVA[0], currentVA[1]);
  } else {
    data = currentPainting.rag;
  }
  codePre.innerHTML = colorizeJson(data);
}

// ============================================================================
// 16. Concert mode — auto-tour all 8 paintings
// ============================================================================

const concertOverlay = $('#concert-overlay');
const concertBtn = $('#btn-concert');
const concertClose = $('#concert-close');
const concertFill = $('#concert-fill');
const concertIndex = $('#concert-index');
const concertTitle = $('#concert-title');
const concertSub = $('#concert-sub');
const concertVA = $('#concert-va');
const concertDesc = $('#concert-desc');
const concertPin = $('#concert-pin');
const concertAudio = $('#concert-audio');
const concertImgStack = $('#concert-img-stack');

// Build concert image stack — defer real src= to first Concert open so
// that 8 atlas paintings don't get fetched on initial page load.
PAINTINGS.forEach((p, i) => {
  const img = document.createElement('img');
  img.dataset.deferSrc = `assets/paintings/${p.file}`;
  img.alt = p.title;
  img.loading = 'lazy';
  img.decoding = 'async';
  img.style.position = 'absolute';
  img.style.inset = '0';
  img.style.width = '100%';
  img.style.height = '100%';
  img.style.objectFit = 'cover';
  img.style.opacity = '0';
  img.style.transition = 'opacity 1.2s ease';
  if (i === 0) img.classList.add('active');
  img.classList.add('concert-img');
  concertImgStack.appendChild(img);
});
function hydrateConcertImages() {
  $$('.concert-img').forEach(img => {
    if (img.dataset.deferSrc && !img.src) img.src = img.dataset.deferSrc;
  });
}

let concertTimer = null;
let concertStep = 0;
const STEP_MS = 11000;

function concertSetStep(idx) {
  concertStep = idx;
  const p = PAINTINGS[idx];
  // image swap
  $$('.concert-img', concertImgStack).forEach((img, i) => {
    img.classList.toggle('active', i === idx);
    img.style.opacity = i === idx ? '1' : '0';
  });
  // info
  concertIndex.textContent = `演 · ${idx + 1} / ${PAINTINGS.length}`;
  concertTitle.textContent = p.title;
  concertSub.textContent = `${p.artist}`;
  concertVA.innerHTML = `<span>v = ${p.va[0].toFixed(2)}</span><span>a = ${p.va[1].toFixed(2)}</span><span>→ ${vaToWord(p.va[0], p.va[1])}</span>`;
  concertDesc.textContent = p.rag[0].text;
  // pin
  const x = p.va[0] * 100;
  const y = -p.va[1] * 100;
  concertPin.setAttribute('transform', `translate(${x},${y})`);
  // audio
  concertAudio.src = `assets/audio/${p.audio}`;
  concertAudio.play().catch(() => {});
  // progress bar reset
  concertFill.style.transition = 'none';
  concertFill.style.width = '0%';
  void concertFill.offsetWidth;
  concertFill.style.transition = `width ${STEP_MS}ms linear`;
  concertFill.style.width = '100%';
}

function startConcert() {
  // pause main audio
  audioEl.pause(); playBtn.classList.remove('playing');
  concertOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';
  hydrateConcertImages();  // lazy-load 8 paintings on first open (not at page init)
  concertStep = 0;
  concertSetStep(0);
  concertTimer = setInterval(() => {
    const next = (concertStep + 1) % PAINTINGS.length;
    if (next === 0) {
      stopConcert();
    } else {
      concertSetStep(next);
    }
  }, STEP_MS);
}

function stopConcert() {
  clearInterval(concertTimer);
  concertTimer = null;
  concertOverlay.classList.remove('open');
  document.body.style.overflow = '';
  try { concertAudio.pause(); } catch {}
}

concertBtn.addEventListener('click', startConcert);
concertClose.addEventListener('click', stopConcert);
concertOverlay.addEventListener('click', (e) => {
  if (e.target === concertOverlay) stopConcert();
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && concertOverlay.classList.contains('open')) stopConcert();
});

// ============================================================================
// 17. Hero 3D parallax + ink-wash cursor trail
// ============================================================================

const heroEl = $('#hero');
const heroArt = $('.hero-art');
const scrollFrame = $('.hero-art .scroll-frame');
const heroTrail = $('#hero-trail');
const trailCtx = heroTrail.getContext('2d');

function fitHeroTrail() {
  const r = heroEl.getBoundingClientRect();
  heroTrail.width  = Math.max(2, Math.floor(r.width  * devicePixelRatio));
  heroTrail.height = Math.max(2, Math.floor(r.height * devicePixelRatio));
}
fitHeroTrail();
window.addEventListener('resize', fitHeroTrail);

// Tilt parallax on the scroll-frame (subtle 6deg max)
heroArt.addEventListener('mousemove', (e) => {
  const rect = heroArt.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width  - 0.5;
  const y = (e.clientY - rect.top)  / rect.height - 0.5;
  heroArt.classList.add('parallaxing');
  scrollFrame.style.transform =
    `perspective(1100px) rotateY(${x * 7}deg) rotateX(${-y * 7}deg) translateZ(8px)`;
});
heroArt.addEventListener('mouseleave', () => {
  heroArt.classList.remove('parallaxing');
  scrollFrame.style.transform = 'perspective(1100px) rotateY(0deg) rotateX(0deg)';
});

// Ink-wash cursor trail (only inside hero) — write a soft blot, fade entire canvas each frame
let lastBlot = { x: 0, y: 0, t: 0 };
heroEl.addEventListener('mousemove', (e) => {
  const rect = heroEl.getBoundingClientRect();
  const x = (e.clientX - rect.left) * devicePixelRatio;
  const y = (e.clientY - rect.top)  * devicePixelRatio;
  const dx = x - lastBlot.x, dy = y - lastBlot.y;
  const dist = Math.hypot(dx, dy);
  // Density limit: don't over-paint
  if (dist < 6) return;
  // Multiple soft blots along the segment for smooth trail
  const steps = Math.min(6, Math.max(1, Math.floor(dist / 14)));
  for (let i = 0; i < steps; i++) {
    const t = i / steps;
    const bx = lastBlot.x + dx * t;
    const by = lastBlot.y + dy * t;
    const r = 10 + Math.random() * 20;
    const grd = trailCtx.createRadialGradient(bx, by, 0, bx, by, r * devicePixelRatio);
    grd.addColorStop(0, 'rgba(20,17,15,0.06)');
    grd.addColorStop(1, 'rgba(20,17,15,0)');
    trailCtx.fillStyle = grd;
    trailCtx.beginPath();
    trailCtx.arc(bx, by, r * devicePixelRatio, 0, Math.PI * 2);
    trailCtx.fill();
  }
  lastBlot = { x, y, t: performance.now() };
});

// Continuous fade so the trail breathes
function fadeTrail() {
  trailCtx.fillStyle = 'rgba(245, 239, 226, 0.022)';
  trailCtx.fillRect(0, 0, heroTrail.width, heroTrail.height);
  requestAnimationFrame(fadeTrail);
}
fadeTrail();

// ============================================================================
// 18. Scroll progress
// ============================================================================

const scrollProg = $('#scroll-progress');
window.addEventListener('scroll', () => {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
  scrollProg.style.width = pct + '%';
});

// ============================================================================
// 19. Paintings Atlas — render grid + click → Painting Detail modal
// ============================================================================

const atlasGrid = $('#atlas-grid');
PAINTINGS.forEach((p) => {
  const card = document.createElement('div');
  card.className = 'atlas-card';
  card.dataset.id = p.id;
  const word = vaToWord(p.va[0], p.va[1]);
  card.innerHTML = `
    <div class="ac-frame">
      <div class="ac-mini-va">
        <svg viewBox="-110 -110 220 220" aria-hidden="true">
          <circle r="100" fill="none" stroke="#2a2521" stroke-width="2"/>
          <line x1="-100" y1="0" x2="100" y2="0" stroke="#a8a39e" stroke-width="0.8"/>
          <line x1="0" y1="-100" x2="0" y2="100" stroke="#a8a39e" stroke-width="0.8"/>
          <circle cx="${p.va[0] * 100}" cy="${-p.va[1] * 100}" r="14" fill="#b8302a"/>
        </svg>
      </div>
      <img src="assets/paintings/${p.file}" alt="${p.titleEn}">
      <div class="ac-seal"><span>回</span><span>声</span></div>
      <div class="ac-overlay">${p.rag[0].text}</div>
    </div>
    <div class="ac-body">
      <div class="ac-title">${p.title}</div>
      <div class="ac-artist">${p.artist}</div>
      <div class="ac-foot">
        <span class="word">${word}</span>
        <span>v=${p.va[0].toFixed(2)}</span>
        <span>a=${p.va[1].toFixed(2)}</span>
      </div>
    </div>
  `;
  card.addEventListener('click', () => openPaintingDetail(p));
  atlasGrid.appendChild(card);
});

// ============================================================================
// 20. Modal management — generic open/close
// ============================================================================

function openModal(id) {
  $('#' + id).classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal(id) {
  $('#' + id).classList.remove('open');
  document.body.style.overflow = '';
}
$$('[data-close]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    closeModal(btn.dataset.close);
  });
});
$$('.modal-overlay').forEach(m => {
  m.addEventListener('click', (e) => { if (e.target === m) closeModal(m.id); });
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') $$('.modal-overlay.open').forEach(m => closeModal(m.id));
});

// ============================================================================
// 21. About modal — open from nav
// ============================================================================

$('#open-about').addEventListener('click', (e) => {
  e.preventDefault();
  openModal('about-modal');
});

$('#cite-copy').addEventListener('click', () => {
  const txt = $('#bibtex-block').textContent;
  navigator.clipboard.writeText(txt).then(() => {
    $('#cite-copy').textContent = 'copied!';
    setTimeout(() => $('#cite-copy').textContent = 'copy', 1400);
  });
});

// ============================================================================
// 22. Painting Detail modal
// ============================================================================

let pdAudio = null;
function openPaintingDetail(p) {
  const d = vaToDescriptors(p.va[0], p.va[1]);
  const word = vaToWord(p.va[0], p.va[1]);
  const colorMap = {
    calm:'#b88f4e', excited:'#5e8466', joyful:'#5e8466',
    tense:'#b8302a', angry:'#b8302a', sad:'#2a6e96',
    melancholic:'#2a6e96', tender:'#b88f4e',
  };
  $('#pd-body').innerHTML = `
    <div class="pd-img-wrap" data-img="assets/paintings/${p.file}" data-cap="${p.title} · ${p.artist}">
      <img src="assets/paintings/${p.file}" alt="${p.titleEn}">
      <div class="pd-seal"><span>回</span><span>声</span></div>
    </div>
    <div class="pd-info">
      <h2>${p.title}</h2>
      <div class="pd-en">${p.artist} · ${p.titleEn}</div>
      <div class="pd-tags">
        <span class="tag dyn">${p.dynasty}</span>
        ${p.tags.map(t => `<span class="tag">${t}</span>`).join('')}
        <span class="tag">Cleveland · CC0</span>
      </div>
      <div class="pd-section">
        <h4>V-A Affective State</h4>
        <div class="pd-va-row">
          <svg viewBox="-110 -110 220 220">
            <circle r="100" fill="none" stroke="#524841" stroke-width="1"/>
            <line x1="-100" y1="0" x2="100" y2="0" stroke="#a8a39e" stroke-width="0.5"/>
            <line x1="0" y1="-100" x2="0" y2="100" stroke="#a8a39e" stroke-width="0.5"/>
            <path d="M0,0 L100,0 A100,100 0 0,1 0,100 Z" fill="#b88f4e" opacity="0.16" />
            <path d="M0,0 L0,100 A100,100 0 0,1 -100,0 Z" fill="#2a6e96" opacity="0.16" />
            <path d="M0,0 L-100,0 A100,100 0 0,1 0,-100 Z" fill="#b8302a" opacity="0.16" />
            <path d="M0,0 L0,-100 A100,100 0 0,1 100,0 Z" fill="#5e8466" opacity="0.16" />
            <circle cx="${p.va[0]*100}" cy="${-p.va[1]*100}" r="11" fill="${colorMap[word] || '#b8302a'}" opacity="0.3"/>
            <circle cx="${p.va[0]*100}" cy="${-p.va[1]*100}" r="6" fill="${colorMap[word] || '#b8302a'}"/>
          </svg>
          <div class="pd-va-info">
            <div class="pd-word" style="color: ${colorMap[word] || '#14110f'};">${word}</div>
            <div class="pd-coord">v = ${p.va[0].toFixed(2)}  ·  a = ${p.va[1].toFixed(2)}</div>
          </div>
        </div>
      </div>
      <div class="pd-section">
        <h4>Musical Descriptors · M6 ▸ 8-slot</h4>
        <div class="pd-slots">
          ${Object.entries(d).map(([k, v]) => `
            <div class="pd-slot">
              <div class="pd-slot-label">${k}</div>
              <div class="pd-slot-value">${Array.isArray(v) ? v.join(' · ') : v}</div>
            </div>
          `).join('')}
        </div>
      </div>
      <div class="pd-section">
        <h4>Retrieved Art-history Context · M3 ▸ top-3 of 1129</h4>
        <div class="pd-rag-list">
          ${p.rag.map((r, i) => `
            <div class="pd-rag-item" data-rag-idx="${i}">
              <span class="pd-rag-score">${r.score.toFixed(2)}</span>${r.text}
            </div>
          `).join('')}
        </div>
      </div>
      <div class="pd-section">
        <h4>Generated Soundtrack · M4 ▸ MusicGen mock</h4>
        <div class="pd-audio-row">
          <button class="pd-play-btn" id="pd-play">
            <svg class="pd-icon-play" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </button>
          <div class="pd-audio-info">${p.audio} · 32 kHz mono</div>
        </div>
        <audio id="pd-audio" src="assets/audio/${p.audio}" preload="auto"></audio>
      </div>
    </div>
  `;

  // Wire up RAG item clicks → RAG modal
  $$('.pd-rag-item', $('#pd-body')).forEach(item => {
    item.addEventListener('click', () => {
      const idx = parseInt(item.dataset.ragIdx, 10);
      openRagModal(p.rag[idx]);
    });
  });

  // Image zoom
  $('.pd-img-wrap', $('#pd-body')).addEventListener('click', (e) => {
    const wrap = e.currentTarget;
    openZoom(wrap.dataset.img, wrap.dataset.cap);
  });

  // Audio play
  pdAudio = $('#pd-audio');
  const pdPlay = $('#pd-play');
  pdPlay.addEventListener('click', () => {
    if (pdAudio.paused) { pdAudio.play(); pdPlay.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6zm8-14v14h4V5z"/></svg>'; }
    else { pdAudio.pause(); pdPlay.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'; }
  });
  pdAudio.addEventListener('ended', () => {
    pdPlay.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
  });

  openModal('painting-detail-modal');
}

// Stop pd audio when modal closes
$('#painting-detail-modal').addEventListener('click', (e) => {
  if (e.target.id === 'painting-detail-modal' || e.target.dataset.close === 'painting-detail-modal') {
    if (pdAudio) { try { pdAudio.pause(); } catch {} pdAudio = null; }
  }
});

// ============================================================================
// 23. Image zoom modal
// ============================================================================

const zoomImg = $('#zoom-img');
const zoomCap = $('#zoom-caption');
function openZoom(src, cap) {
  zoomImg.src = src;
  zoomImg.classList.remove('zoomed');
  zoomCap.textContent = cap || '点击切换 1× / 1.6×';
  openModal('zoom-modal');
}
zoomImg.addEventListener('click', () => zoomImg.classList.toggle('zoomed'));

// case-banner image → zoom modal
const caseImgWrap = $('#case-img-wrap');
if (caseImgWrap) {
  caseImgWrap.addEventListener('click', () => {
    const img = $('img', caseImgWrap);
    openZoom(img.src, '林逋月夜行吟 · Du Jin · 明');
  });
}

// ============================================================================
// 24. RAG modal
// ============================================================================

function openRagModal(r) {
  $('#rag-modal-score').textContent = r.score.toFixed(2);
  $('#rag-modal-src').textContent = `Met / Cleveland chunk · cosine ${r.score.toFixed(3)}`;
  $('#rag-modal-text').textContent = r.text;
  openModal('rag-modal');
}

// Wire up demo's RAG items: click → open modal
$('#rag-list').addEventListener('click', (e) => {
  const item = e.target.closest('.rag-item');
  if (!item) return;
  // Find index from siblings
  const items = $$('.rag-item', $('#rag-list'));
  const idx = items.indexOf(item);
  if (idx >= 0 && currentPainting.rag[idx]) {
    openRagModal(currentPainting.rag[idx]);
  }
});

// Make demo rag items look clickable
const ragListStyle = document.createElement('style');
ragListStyle.textContent = `.rag-item { cursor: pointer; transition: background 200ms; }
.rag-item:hover { background: rgba(42,110,150,0.08); }`;
document.head.appendChild(ragListStyle);

// ============================================================================
// 25. Dataflow diagram — hover highlights connected edges + neighbour nodes
// ============================================================================

const dfSvg = $('#df-svg');
if (dfSvg) {
  const dfNodes = $$('.df-node', dfSvg);
  const dfEdges = $$('.df-edge', dfSvg);
  const dfLabels = $$('.df-edge-label', dfSvg);

  function dfClear() {
    dfSvg.classList.remove('has-active');
    dfNodes.forEach(n => n.classList.remove('active'));
    dfEdges.forEach(e => e.classList.remove('active'));
    dfLabels.forEach(l => l.classList.remove('active'));
  }

  function dfHighlight(id) {
    dfSvg.classList.add('has-active');
    const neighbours = new Set([id]);
    dfEdges.forEach((edge, idx) => {
      const from = edge.dataset.from, to = edge.dataset.to;
      const isMe = from === id || to === id;
      edge.classList.toggle('active', isMe);
      // matching label is the next sibling text element in the SVG;
      // we just check label position; simpler: toggle all labels by index
      if (isMe) {
        neighbours.add(from === id ? to : from);
        // Find the closest label by index
        const lbl = edge.nextElementSibling;
        if (lbl && lbl.classList && lbl.classList.contains('df-edge-label')) {
          lbl.classList.add('active');
        }
      }
    });
    dfNodes.forEach(n => n.classList.toggle('active', neighbours.has(n.dataset.id)));
  }

  dfNodes.forEach(n => {
    n.addEventListener('mouseenter', () => dfHighlight(n.dataset.id));
    n.addEventListener('mouseleave', dfClear);
    n.addEventListener('focusin', () => dfHighlight(n.dataset.id));
    n.addEventListener('focusout', dfClear);
    // click → jump to corresponding module's lightbox if it's a real module
    n.addEventListener('click', () => {
      const id = n.dataset.id.toUpperCase();
      const mod = MODULES.find(m => m.id === id);
      if (mod) openLightbox(mod);
    });
    // a11y
    n.setAttribute('tabindex', '0');
    n.setAttribute('role', 'button');
  });

  // Observe to trigger the edge-drawing animation on scroll-in
  const dfObs = new IntersectionObserver((es) => {
    es.forEach(e => { if (e.isIntersecting) {
      e.target.classList.add('visible');
      dfObs.unobserve(e.target);
    }});
  }, { threshold: 0.25 });
  dfObs.observe($('.dataflow'));
}

// ============================================================================
// 26. Init
// ============================================================================

renderPaintingDots();
selectPainting('p2');
refreshCodePanel();

window.addEventListener('click', function once() {
  ensureCtx();
  window.removeEventListener('click', once);
}, { once: true });

})();
