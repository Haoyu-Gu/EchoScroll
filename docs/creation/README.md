# EchoScroll · Creation Preview

> Live: **https://haoyu-gu.github.io/EchoScroll/creation/**

A second, design-school-aligned version of the EchoScroll demo. Same framework as the presentation demo (no layout changes), but with three visual tracks updated to match the design team's creation-oriented mockups:

| Track | Change |
|---|---|
| **A · Palette → 偏石青 (stone-teal)** | `--stone-blue` 从 `#2a6e96` 拉深到 `#1f5d72` 对齐设计学院。朱印红从所有 UI 强调位下岗（按钮、链接、徽章），改用石青统一。朱印仅保留装饰性印章用途。 |
| **B · 卷轴展开动画 (scroll-reveal)** | 凡是画卷出现的位置（hero painting-stack、case-study banner），加入「绢面卷布从中央向两侧拉开 + 双轴心滑动」入场动画，IntersectionObserver 进入视口时触发，1.4s `cubic-bezier(0.16, 1, 0.3, 1)` 平滑曲线。 |
| **C · Logo 替换** | 旧版「回声」朱印章 → 新版「展开的小卷轴 SVG + Caveat 手写花体 EchoScroll」。 |

## 故宫风同心圆 reticle 标记点（附赠）

在 case study 的画作上，叠加了 2 个同心圆 reticle 标记点（白外环 + 石青中心 + 呼吸光圈），点击后画面左上角浮出深色半透明注释面板（V-A 坐标 + 文字描述）。这是为了暗示**创作版的核心交互方向：在画上直接打点编辑**——参考故宫博物院《清明上河图》的画作热点交互。

实际的"画上编辑"完整交互（拖动 reticle / 标签 picker / 横向手卷拖滚）会在独立的 creation-oriented demo 里实现。

## 与 Presentation 版的差异

| | Presentation 版 (`/`) | Creation Preview (`/creation/`) |
|---|---|---|
| 主强调色 | 朱印红 `#b8302a` + 石青 `#2a6e96` 双主 | **唯一石青** `#1f5d72` |
| 画卷进入 | fade-in + opacity transition | **卷轴展开** (curtain + axis 滑出) |
| Logo | 「回声」朱印章 | 展开卷轴 SVG + Caveat 手写体 |
| 画上交互 | V-A 圆环（独立面板） | V-A 圆环 + **画上 reticle 标记点** |
| Framework / sections | 14 节 + Concert Mode | **完全一致**（框架不动） |
| 假设受众 | 答辩 / 评委 / 投资人 | **设计学院 + 创作者** |

## 实现细节（给改的人看）

3 个文件就这些改动：

| 文件 | Δ | 关键 token |
|---|---|---|
| `creation/index.html` | +28 行 | nav-brand 换成 `.scroll-logo`，hero/case-study 加 `class="scroll-reveal" data-reveal` + `<span class="reveal-axis left/right">`，case-study 加 2 个 `<button class="reticle">` + `<div class="reticle-panel">`，assets 路径全部改为 `../assets/...` |
| `creation/styles.css` | +260 行 (v8 块) | `.scroll-reveal`、`.reticle`、`.reticle-panel`、`.nav-brand .scroll-logo` 全新；token 改 `--stone-blue` 为 `#1f5d72`、新增 `--silk-warm/--silk-deep/--stone-blue-d`；audience-card.hi / real-audio-note 强调色从 seal 改 stone-blue |
| `creation/app.js` | +60 行 | 末尾两个新 IIFE：`initScrollReveal` (IO 触发 .revealed)、`initReticles` (点击切换面板) |

Assets (画作 + 音频 + figures) **不复制**，直接通过 `../assets/...` 引用 presentation 版的 assets 目录，节省 40 MB。

## 本地预览

```bash
cd docs
python3 -m http.server 8080
# 打开 http://localhost:8080/creation/
```
