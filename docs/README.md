# EchoScroll · Showcase Demo

> 中国画 → V-A 情感 → MusicGen 配乐 端到端系统的精致网页演示。
> 单页静态网站，**零 build · 零依赖 · 零后端**，本地起一个 http server 就能看。

---

## 启动 · 一句话

```bash
unzip echoscroll_demo.zip
cd echoscroll_demo
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

> ⚠️ **不能**直接双击 `index.html`。浏览器在 `file://` 协议下会拒绝音频/canvas 的跨源访问，导致波形和 Web Audio 实时合成失效。**必须**起本地 server。

### 换端口

```bash
python3 -m http.server 9000        # 端口 9000
```

### 停掉

```bash
pkill -f "http.server"
# 或者按住 Ctrl+C
```

### 用 Node 起（如果不喜欢 Python）

```bash
npx serve -p 8080
# 或
npx http-server -p 8080
```

---

## 浏览器要求

- **推荐**：Chrome / Edge / Safari **2024 年后** 的版本
- **完整体验需要**：
  - `animation-timeline: view()` —— 滚动驱动动画（Chrome 115+ / Safari 26+ / Firefox 137+）
  - `@property` —— CSS 自定义属性插值（Chrome 85+ / Safari 16.4+）
  - Web Audio API —— V-A 拖动实时合成（所有现代浏览器都支持）
- **老浏览器**会自动 fallback 到 IntersectionObserver 一次性 fade-in，内容完整但少了 Apple-style 的滚动跟随感

---

## 11 个 section 一览

| # | section | 内容 |
|---|---|---|
| 1 | **Hero** | 笔锋题字 · 4 画 Ken Burns 轮播 · 朱印 · 鼠标 3D parallax + 墨迹光标轨迹 |
| 2 | **引语** | "画者，画此情；听者，听此意" 大引号水印 |
| 3 | **Vision** | 项目愿景文字陈述 |
| 4 | **Pipeline · 五步而成** | 5 步骤卡片 + 4 个手绘 SVG 毛笔箭头（滚动入视时绘出）|
| 5 | **Live Demo · 展卷而听** | ⭐ 核心交互区：8 画作选择 + 可拖动 V-A 圆环 + 实时合成预览 + 8-slot 描述符 + 音频播放器（6 变体）+ RAG top-3 检索 |
| 6 | **Case Study · 案例研究** | 1 幅画的完整 pipeline 4 步 trace（INPUT → ENCODER → V-A → OUTPUT）|
| 7 | **Atlas · 画作图谱** | 8 画作 grid，每张含 mini V-A 圆环 + RAG 上下文遮罩 |
| 8 | **Module Showcase · 模块陈列** | 9 卡片，每卡 = 小图标 + 公式/SVG/代码片段 + 描述 + 3 张图缩略 + 关键数字 |
| 9 | **Dataflow · 模块连接图** | 1280×680 SVG 网络图，hover 高亮进出边 + label |
| 10 | **Research Context · 研究语境** | 三栏对照：现状 / 差距 / 我们的方法 |
| 11 | **Timeline · 项目时间线** | 4 个里程碑（P1→P4）|
| 12 | **Numbers · 硬数字** | 8 个滚动入视时缓动计数 |
| 13 | **Tech Stack** | 22 个技术 pill 按视觉/音频/语言/框架/数据分色 |
| 14 | **Footer** | 团队 + 导师 + SHA-256 |

外加 **6 个弹窗**：Lightbox（模块图）· About（关于）· Painting Detail（画作详情）· Image Zoom（图片放大）· RAG Chunk（检索片段）· Concert Mode（演奏厅自动巡演 8 画 ~96s）

---

## 关键交互

| 操作 | 触发 |
|---|---|
| 拖动 V-A 圆环上的红点 | **Web Audio 实时合成预览音**（sine + 颤音 + 模幅 LFO，跟随 V-A 即时变化）；松手后离当前画作太远会自动切到最接近的音频变体 |
| 点选 8 张古画缩略图 | 主图 fade 切换、V-A 跳到该画预设、配乐切换、RAG 列表刷新 |
| 点选 V-A 圆环上 8 个淡墨小点 | 同上（圆环上散布着 8 张画作的预设坐标）|
| 点击 atlas / 缩略图 | 打开 **Painting Detail** 弹窗（全字段 + 可放大图）|
| 点击模块卡 | 打开 **Lightbox** 看该模块完整 3 张图 |
| 点击模块卡底部小缩略图 | 打开 lightbox 并 outline 高亮指定那张 |
| 点击 RAG chunk | 打开 **RAG Chunk** 弹窗看全文 + meta |
| 点击 case-study 大图 | 全屏 zoom，再点切换 1× ⇄ 1.6× |
| **顶栏 演奏厅 按钮** | 全屏自动巡演 8 画作 ~96s，可 ESC 退出 |
| **顶栏 关于** | About 弹窗（项目介绍 + BibTeX 引用）|
| **右下 ⌘ 按钮** | 代码透明面板，4 标签（painting/va/descriptors/rag）实时 JSON 状态 + copy |
| 滚动到 Dataflow 后 hover 节点 | 进出边变朱砂 + 发光，其它节点淡出 |
| 模块卡 hover | 底部 3 张图缩略图 spring 弹大 |

---

## 文件清单

```
echoscroll_demo/
├── README.md            ← 本文件
├── index.html           1,208 行  HTML 骨架 + 内容
├── styles.css           3,589 行  样式（含 Apple-style scroll-driven 动画 + 14 处连续呼吸 + 微交互）
├── app.js               1,505 行  交互（拖动 / Web Audio / 计数器 / 弹窗 / Concert）
└── assets/              12 MB
    ├── paintings/       8 张古画（南宋→清，CC0/Cleveland & Met）3.8 MB
    ├── figures/         27 张模块可视化 + 1 张 GALLERY 总览  3.6 MB
    ├── audio/           7 段 demo 音频（M4 mock + M5 变速/段位）4.7 MB
    └── data/            5 个 smoke test JSON（painting_metadata / va / descriptors / retrieved_chunks / metrics）
```

**代码总计**：6,302 行（HTML + CSS + JS）  
**资源总计**：51 个文件 / 12 MB

---

## 8 张古画 · 朝代分布

| 编号 | 画 | 作者 | 朝代 | V-A 预设 | 词 |
|---|---|---|---|---:|---|
| p1 | 云山图 | Mi Youren · 米友仁 (1072–1151) | 南宋 | (-0.22, -0.55) | calm |
| p2 | 林逋月夜行吟 (smoke test) | Du Jin · 杜堇 (1446–c. 1519) | 明 | (-0.03, +0.11) | tender |
| p3 | 群仙山图 | Chen Ruyan · 陈汝言 (c. 1331–1371) | 元 | (+0.35, -0.05) | tender |
| p4 | 溪山兰若图 | Juran · 巨然 (active 960–985) | 北宋 | (-0.36, -0.34) | melancholic |
| p5 | 仿郭忠恕山水 | Bada Shanren · 八大山人 (1626–1705) | 清 | (-0.42, +0.18) | tense |
| p6 | 溪山无尽图 | 佚名 | 北宋-金 | (-0.05, +0.45) | joyful |
| p7 | 寒梅图 | Ni Jing · 倪静 | 元-明 | (-0.30, -0.42) | sad |
| p8 | 雪梅图 | Liu Shiru · 刘世儒 | 明 | (+0.12, -0.50) | calm |

所有图像 **CC0 / 公有领域**，来自 Cleveland Museum of Art 与 The Metropolitan Museum of Art 开放数据。

---

## 设计语言（中国画美学）

**配色**
```
宣纸  #f5efe2     墨色   #2a2521     朱砂   #b8302a
石青  #2a6e96     石绿   #5e8466     描金   #b88f4e
```

**字体**
- 中文 serif：Noto Serif SC（标题）+ Ma Shan Zheng（毛笔印章）
- 拉丁 serif：Cormorant Garamond（斜体）
- 无衬线：Inter（小字）+ JetBrains Mono（mono）

**动画哲学**
- 所有 scroll-driven 入场用 `animation-timeline: view()`
- 全站 easing 统一：`ease-out` / `ease-smooth` / `ease-spring` / `ease-io`
- 焦点元素带连续"呼吸"（朱印 6.5s · 墨溅 18-26s · V-A halo 2.6s · 画 Ken Burns 22s）

---

## 不需要

- ❌ Node / npm / Vite / 任何 build 工具
- ❌ 任何 API key
- ❌ 后端 / 数据库
- ❌ Python 包（只用标准库 `http.server`）
- ❌ 网络（Google Fonts 第一次会下，之后浏览器 cache；离线只是字体退化，功能完整）

---

## License

代码 · MIT；中国画图片 · CC0 (Met / Cleveland)；音频 · 项目研究产物。
