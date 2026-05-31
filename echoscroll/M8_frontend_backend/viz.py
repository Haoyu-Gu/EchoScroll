"""
Architectural visualisations for M8 (frontend + backend skeleton).

We cannot render the React UI without a browser, so these matplotlib figures
serve as stand-ins for screenshots:

    fig_system_arch.png    -- three-layer system architecture diagram
    fig_endpoint_flow.png  -- sequence-diagram of a typical user flow
    fig_va_panel_mockup.png -- mockup of the V-A circumplex panel

Run:
    python viz.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Circle


HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ---------- shared style helpers ------------------------------------------

LAYER_COLORS = {
    "browser": "#dbe9ff",
    "browser_edge": "#2b5fb0",
    "backend": "#fde2c4",
    "backend_edge": "#b86c1c",
    "modules": "#d8ecd6",
    "modules_edge": "#3a7a3a",
    "ws": "#efd9f7",
    "ws_edge": "#7a3aaa",
}


def _rounded_box(ax, x, y, w, h, label, face, edge, fontsize=10, weight="normal"):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4,
        facecolor=face,
        edgecolor=edge,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        color="#1a1a1a",
    )
    return box


def _arrow(ax, xy_from, xy_to, color="#444", lw=1.3, style="-|>", mut=12, ls="-"):
    arr = FancyArrowPatch(
        xy_from,
        xy_to,
        arrowstyle=style,
        mutation_scale=mut,
        color=color,
        linewidth=lw,
        linestyle=ls,
    )
    ax.add_patch(arr)


# ---------- fig 1: system architecture ------------------------------------


def fig_system_arch(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title(
        "EchoScroll · M8 System Architecture",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )

    # ---- Layer banner labels on left ----
    for ly, txt in [(7.4, "Browser\n(React)"), (4.4, "FastAPI\nbackend"), (1.4, "M1–M9\n(stubbed)")]:
        ax.text(
            0.35,
            ly,
            txt,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#333",
            rotation=90,
        )

    # ============ TOP LAYER: Browser ============
    top_y = 6.7
    top_h = 1.6
    # outer browser frame
    _rounded_box(
        ax,
        0.9,
        top_y,
        11.4,
        top_h,
        "",
        LAYER_COLORS["browser"],
        LAYER_COLORS["browser_edge"],
    )
    ax.text(
        1.15,
        top_y + top_h - 0.22,
        "Browser  ·  React + Vite + WaveSurfer",
        fontsize=10,
        fontweight="bold",
        color=LAYER_COLORS["browser_edge"],
    )

    components = [
        ("UploadPanel",     1.25),
        ("VAPanel",         3.45),
        ("WaveformView",    5.65),
        ("PromptBox",       7.85),
        ("HummingRecorder", 10.05),
    ]
    cw, ch = 2.05, 0.7
    cy = top_y + 0.25
    for name, cx in components:
        _rounded_box(
            ax,
            cx,
            cy,
            cw,
            ch,
            name,
            "#ffffff",
            LAYER_COLORS["browser_edge"],
            fontsize=9,
        )

    # flow arrows between components (UploadPanel -> VAPanel -> ...)
    for i in range(len(components) - 1):
        x_from = components[i][1] + cw
        x_to = components[i + 1][1]
        _arrow(
            ax,
            (x_from + 0.02, cy + ch / 2),
            (x_to - 0.02, cy + ch / 2),
            color=LAYER_COLORS["browser_edge"],
            lw=1.0,
        )

    # ============ MIDDLE LAYER: FastAPI ============
    mid_y = 3.7
    mid_h = 1.6
    _rounded_box(
        ax,
        0.9,
        mid_y,
        11.4,
        mid_h,
        "",
        LAYER_COLORS["backend"],
        LAYER_COLORS["backend_edge"],
    )
    ax.text(
        1.15,
        mid_y + mid_h - 0.22,
        "FastAPI backend  ·  backend/main.py  (uvicorn :8000)",
        fontsize=10,
        fontweight="bold",
        color=LAYER_COLORS["backend_edge"],
    )

    endpoints = [
        ("POST /upload",          1.05, "#ffffff"),
        ("POST /generate",        2.78, "#ffffff"),
        ("POST /edit/va",         4.51, "#ffffff"),
        ("POST /edit/prompt",     6.24, "#ffffff"),
        ("POST /edit/humming",    7.97, "#ffffff"),
        ("GET /audio/{id}",       9.70, "#ffffff"),
        ("WS /ws/preview",       11.43, LAYER_COLORS["ws"]),
    ]
    ew, eh = 1.65, 0.72
    ey = mid_y + 0.23
    for name, ex, face in endpoints:
        edge = (
            LAYER_COLORS["ws_edge"]
            if name.startswith("WS")
            else LAYER_COLORS["backend_edge"]
        )
        _rounded_box(ax, ex - 0.83, ey, ew, eh, name, face, edge, fontsize=8.2)

    # ============ BOTTOM LAYER: M1–M9 modules ============
    bot_y = 0.5
    bot_h = 1.95
    _rounded_box(
        ax,
        0.9,
        bot_y,
        11.4,
        bot_h,
        "",
        LAYER_COLORS["modules"],
        LAYER_COLORS["modules_edge"],
    )
    ax.text(
        1.15,
        bot_y + bot_h - 0.22,
        "M1–M9 modules  ·  stubbed (replace `# TODO: wire to M*`)",
        fontsize=10,
        fontweight="bold",
        color=LAYER_COLORS["modules_edge"],
    )

    modules = [
        ("M1\nImage\nEncoder",        1.05),
        ("M2\nV-A\nProjector",        2.30),
        ("M3\nArt-Hist\nRAG",         3.55),
        ("M4\nMusic\nGenerator",      4.80),
        ("M5\nEditing\nLayer",        6.05),
        ("M6\nPrompt\nTranslator",    7.30),
        ("M7\nHumming\nInteract",     8.55),
        ("M8\nFE/BE\n(this)",         9.80),
        ("M9\nEval &\nLogs",         11.05),
    ]
    mw, mh = 1.15, 1.35
    my = bot_y + 0.13
    for name, mx in modules:
        face = "#ffffff" if "M8" not in name else "#f7f7d0"
        _rounded_box(
            ax,
            mx,
            my,
            mw,
            mh,
            name,
            face,
            LAYER_COLORS["modules_edge"],
            fontsize=7.8,
        )

    # ---- inter-layer arrows (browser -> backend) ----
    # UploadPanel -> /upload
    _arrow(
        ax,
        (components[0][1] + cw / 2, cy),
        (endpoints[0][1] - 0.83 + ew / 2, ey + eh),
        color=LAYER_COLORS["backend_edge"],
        lw=1.2,
    )
    # VAPanel -> /edit/va    (also goes through /generate)
    _arrow(
        ax,
        (components[1][1] + cw / 2, cy),
        (endpoints[2][1] - 0.83 + ew / 2, ey + eh),
        color=LAYER_COLORS["backend_edge"],
        lw=1.2,
    )
    # WaveformView <- /audio
    _arrow(
        ax,
        (endpoints[5][1] - 0.83 + ew / 2, ey + eh),
        (components[2][1] + cw / 2, cy),
        color=LAYER_COLORS["backend_edge"],
        lw=1.2,
        ls="--",
    )
    # PromptBox -> /edit/prompt
    _arrow(
        ax,
        (components[3][1] + cw / 2, cy),
        (endpoints[3][1] - 0.83 + ew / 2, ey + eh),
        color=LAYER_COLORS["backend_edge"],
        lw=1.2,
    )
    # HummingRecorder -> /edit/humming
    _arrow(
        ax,
        (components[4][1] + cw / 2, cy),
        (endpoints[4][1] - 0.83 + ew / 2, ey + eh),
        color=LAYER_COLORS["backend_edge"],
        lw=1.2,
    )
    # WS /ws/preview <-> any component (drawn from frame)
    _arrow(
        ax,
        (endpoints[6][1] - 0.83 + ew / 2, ey + eh),
        (components[2][1] + cw, cy + ch / 2),
        color=LAYER_COLORS["ws_edge"],
        lw=1.2,
        ls=":",
    )

    # ---- backend -> modules ----
    endpoint_to_modules = {
        0: [0],            # upload -> M1 (just routes asset for downstream)
        1: [0, 1, 2, 3],   # generate -> M1, M2, M3, M4
        2: [4],            # edit/va -> M5
        3: [5],            # edit/prompt -> M6
        4: [6],            # edit/humming -> M7
        5: [3],            # /audio/{id} -> M4 (renders cached output)
        6: [3, 8],         # ws/preview -> M4 (progress) and M9 (logs)
    }
    for ei, mods in endpoint_to_modules.items():
        ex = endpoints[ei][1]
        for mi in mods:
            mx = modules[mi][1] + mw / 2
            color = (
                LAYER_COLORS["ws_edge"]
                if ei == 6
                else LAYER_COLORS["modules_edge"]
            )
            _arrow(
                ax,
                (ex, ey),
                (mx, my + mh),
                color=color,
                lw=0.9,
                ls=("--" if ei == 6 else "-"),
                mut=9,
            )

    # legend
    leg_x = 9.3
    leg_y = 8.55
    ax.text(leg_x, leg_y, "Legend:", fontsize=8.5, fontweight="bold")
    ax.add_patch(
        Rectangle((leg_x, leg_y - 0.32), 0.25, 0.18,
                  facecolor=LAYER_COLORS["browser"],
                  edgecolor=LAYER_COLORS["browser_edge"])
    )
    ax.text(leg_x + 0.32, leg_y - 0.23, "React UI", fontsize=7.5)
    ax.add_patch(
        Rectangle((leg_x + 1.4, leg_y - 0.32), 0.25, 0.18,
                  facecolor=LAYER_COLORS["backend"],
                  edgecolor=LAYER_COLORS["backend_edge"])
    )
    ax.text(leg_x + 1.72, leg_y - 0.23, "FastAPI", fontsize=7.5)
    ax.add_patch(
        Rectangle((leg_x, leg_y - 0.58), 0.25, 0.18,
                  facecolor=LAYER_COLORS["modules"],
                  edgecolor=LAYER_COLORS["modules_edge"])
    )
    ax.text(leg_x + 0.32, leg_y - 0.49, "M1-M9 stubs", fontsize=7.5)
    ax.add_patch(
        Rectangle((leg_x + 1.4, leg_y - 0.58), 0.25, 0.18,
                  facecolor=LAYER_COLORS["ws"],
                  edgecolor=LAYER_COLORS["ws_edge"])
    )
    ax.text(leg_x + 1.72, leg_y - 0.49, "WebSocket", fontsize=7.5)

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------- fig 2: endpoint sequence flow ---------------------------------


def fig_endpoint_flow(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.axis("off")
    ax.set_title(
        "EchoScroll · Typical User Flow (sequence diagram)",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )

    # 3 actors / lifelines
    lanes = [
        ("Browser\n(React UI)",   2.0, LAYER_COLORS["browser"],   LAYER_COLORS["browser_edge"]),
        ("FastAPI\nbackend/main.py", 6.0, LAYER_COLORS["backend"],   LAYER_COLORS["backend_edge"]),
        ("M-modules\n(M1-M7)",      10.0, LAYER_COLORS["modules"],   LAYER_COLORS["modules_edge"]),
    ]
    top_y = 10.0
    bot_y = 0.5
    for label, x, face, edge in lanes:
        _rounded_box(ax, x - 1.1, top_y - 0.05, 2.2, 0.7, label, face, edge,
                     fontsize=10, weight="bold")
        # dashed lifeline
        ax.plot([x, x], [top_y - 0.05, bot_y], linestyle=(0, (4, 3)),
                color="#888", linewidth=1)

    # Helper for message rows
    def msg(y, x_from, x_to, label, color="#222", style="-|>", note=None, ls="-"):
        _arrow(ax, (x_from, y), (x_to, y), color=color, style=style, lw=1.6, ls=ls)
        # label centered above arrow
        mid = (x_from + x_to) / 2
        ax.text(mid, y + 0.13, label, ha="center", va="bottom",
                fontsize=9, color=color)
        if note:
            ax.text(mid, y - 0.18, note, ha="center", va="top",
                    fontsize=7.5, style="italic", color="#555")

    def activation(x, y_top, y_bot, color):
        ax.add_patch(Rectangle((x - 0.10, y_bot), 0.20,
                               y_top - y_bot, facecolor=color,
                               edgecolor=color, alpha=0.45))

    Xb, Xs, Xm = 2.0, 6.0, 10.0
    BR_C = LAYER_COLORS["browser_edge"]
    BE_C = LAYER_COLORS["backend_edge"]
    MO_C = LAYER_COLORS["modules_edge"]

    # User action banner
    ax.text(Xb, 9.35, "user drops painting", ha="center", fontsize=8.5,
            color="#444", style="italic")
    # 1) /upload
    msg(9.0, Xb, Xs, "POST /upload  (multipart: image + metadata)", color=BR_C,
        note="UploadPanel.tsx -> backend.upload()")
    activation(Xs, 9.0, 8.55, LAYER_COLORS["backend"])
    msg(8.6, Xs, Xb, "200 UploadResponse  {painting_id, preview_url}", color=BE_C,
        style="-|>", ls="--")

    # 2) /generate
    msg(7.9, Xb, Xs, "POST /generate  {painting_id, duration_s}", color=BR_C,
        note="App.generate()")
    activation(Xs, 7.9, 6.6, LAYER_COLORS["backend"])
    msg(7.55, Xs, Xm, "call M1 image encoder -> M2 V-A -> M3 RAG -> M4 audio",
        color=BE_C, style="-|>")
    activation(Xm, 7.55, 6.95, LAYER_COLORS["modules"])
    msg(6.95, Xm, Xs, "audio bytes + V-A + descriptors + retrieved docs",
        color=MO_C, style="-|>", ls="--")
    msg(6.6, Xs, Xb,
        "200 GenerateResponse  {audio_url, va, descriptors, retrieved_context}",
        color=BE_C, style="-|>", ls="--")

    # 3) audio fetch
    msg(5.85, Xb, Xs, "GET /audio/{painting_id}", color=BR_C,
        note="WaveformView mounts <audio>")
    activation(Xs, 5.85, 5.45, LAYER_COLORS["backend"])
    msg(5.45, Xs, Xb, "audio/wav  (stub.wav)", color=BE_C, style="-|>", ls="--")

    # 4) display
    ax.text(Xb, 5.05, "display waveform + descriptors",
            ha="center", fontsize=8.5, color="#444", style="italic")

    # 5) user drags V-A
    ax.text(Xb, 4.45, "user drags V-A point", ha="center", fontsize=8.5,
            color="#444", style="italic")
    msg(4.05, Xb, Xs, "POST /edit/va  {painting_id, va_target:[v,a]}",
        color=BR_C, note="VAPanel.commitVA()")
    activation(Xs, 4.05, 2.9, LAYER_COLORS["backend"])
    msg(3.7, Xs, Xm, "call M5 editing layer (preserve identity, retarget V-A)",
        color=BE_C)
    activation(Xm, 3.7, 3.25, LAYER_COLORS["modules"])
    msg(3.25, Xm, Xs, "retargeted audio bytes", color=MO_C, style="-|>", ls="--")
    msg(2.9, Xs, Xb, "200 EditVAResponse  {audio_url, va}",
        color=BE_C, style="-|>", ls="--")

    # 6) reload audio
    msg(2.15, Xb, Xs, "GET /audio/{painting_id}?v=&a=&t=...  (cache-bust)",
        color=BR_C, note="setAudioUrl triggers WaveSurfer reload")
    activation(Xs, 2.15, 1.75, LAYER_COLORS["backend"])
    msg(1.75, Xs, Xb, "audio/wav  (updated)", color=BE_C, style="-|>", ls="--")

    # 7) loop
    ax.text(Xb, 1.25, "loop: user keeps dragging or types prompt / hums",
            ha="center", fontsize=8.5, color="#444", style="italic")

    # ---- legend ----
    lx, ly = 0.2, 0.55
    ax.text(lx, ly + 0.30, "Legend:", fontsize=8, fontweight="bold")
    _arrow(ax, (lx + 0.05, ly), (lx + 0.8, ly), color="#444", style="-|>", lw=1.4)
    ax.text(lx + 0.9, ly - 0.04, "request", fontsize=7.5)
    _arrow(ax, (lx + 2.0, ly), (lx + 2.75, ly), color="#444", style="-|>",
           lw=1.4, ls="--")
    ax.text(lx + 2.85, ly - 0.04, "response", fontsize=7.5)
    ax.add_patch(Rectangle((lx + 4.0, ly - 0.05), 0.20, 0.18,
                           facecolor=LAYER_COLORS["backend"], alpha=0.45,
                           edgecolor=LAYER_COLORS["backend_edge"]))
    ax.text(lx + 4.28, ly - 0.04, "activation bar", fontsize=7.5)

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------- fig 3: V-A panel mockup ---------------------------------------


def fig_va_panel_mockup(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # ---- outer "browser/window" frame ----
    _rounded_box(ax, 0.2, 0.2, 9.6, 9.6, "", "#f7f8fa", "#999")
    # title bar
    ax.add_patch(Rectangle((0.2, 9.0), 9.6, 0.8,
                           facecolor="#e7eaef", edgecolor="#999"))
    # traffic lights
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        ax.add_patch(Circle((0.6 + i * 0.3, 9.4), 0.10,
                            facecolor=c, edgecolor="#666", linewidth=0.5))
    ax.text(5.0, 9.4, "EchoScroll · V-A Panel",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color="#333")

    # ---- panel header ----
    ax.text(0.6, 8.55, "2 · VALENCE × AROUSAL",
            fontsize=10.5, fontweight="bold", color="#1a1a1a")
    ax.text(0.6, 8.25,
            "drag the point to retarget the mood (auto-commits on release)",
            fontsize=8.5, color="#666", style="italic")

    # ---- plot area for the circumplex ----
    # use an inset-style sub-axes coordinates within our parent ax
    px0, py0 = 1.4, 1.4
    pw, ph = 7.2, 6.4
    # plot background card
    _rounded_box(ax, px0 - 0.25, py0 - 0.25, pw + 0.5, ph + 0.5, "",
                 "#ffffff", "#bbb")

    # quadrant tints (in user coords [-1,1])
    # axes mapping:  x in [-1,1] -> [px0, px0+pw];  y -> [py0, py0+ph]
    def to_x(v):
        return px0 + (v + 1) / 2 * pw

    def to_y(a):
        return py0 + (a + 1) / 2 * ph

    # quadrant rectangles (with the requested colour mapping)
    # Q1 (+v,+a) warm yellow  (happy / excited)
    ax.add_patch(Rectangle((to_x(0), to_y(0)), to_x(1) - to_x(0),
                           to_y(1) - to_y(0),
                           facecolor="#fff1b8", edgecolor="none", alpha=0.85))
    # Q2 (-v,+a) red (tense / angry)
    ax.add_patch(Rectangle((to_x(-1), to_y(0)), to_x(0) - to_x(-1),
                           to_y(1) - to_y(0),
                           facecolor="#f7c2bf", edgecolor="none", alpha=0.85))
    # Q3 (-v,-a) blue (sad / melancholic)
    ax.add_patch(Rectangle((to_x(-1), to_y(-1)), to_x(0) - to_x(-1),
                           to_y(0) - to_y(-1),
                           facecolor="#c4d8f4", edgecolor="none", alpha=0.85))
    # Q4 (+v,-a) green (calm / serene)
    ax.add_patch(Rectangle((to_x(0), to_y(-1)), to_x(1) - to_x(0),
                           to_y(0) - to_y(-1),
                           facecolor="#cfe7c8", edgecolor="none", alpha=0.85))

    # axes
    ax.plot([to_x(-1), to_x(1)], [to_y(0), to_y(0)], color="#333", lw=1.0)
    ax.plot([to_x(0), to_x(0)], [to_y(-1), to_y(1)], color="#333", lw=1.0)

    # tick marks
    for v in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        ax.plot([to_x(v), to_x(v)], [to_y(0) - 0.05, to_y(0) + 0.05],
                color="#444", lw=0.8)
        if v != 0:
            ax.text(to_x(v), to_y(0) - 0.20, f"{v:+.1f}", ha="center",
                    va="top", fontsize=7, color="#666")
    for a in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        ax.plot([to_x(0) - 0.05, to_x(0) + 0.05], [to_y(a), to_y(a)],
                color="#444", lw=0.8)
        if a != 0:
            ax.text(to_x(0) - 0.10, to_y(a), f"{a:+.1f}", ha="right",
                    va="center", fontsize=7, color="#666")

    # cardinal labels (around perimeter)
    # north / arousal+ : "EXCITED"
    ax.text((to_x(-1) + to_x(1)) / 2, to_y(1) + 0.18, "AROUSAL  ↑  excited",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
            color="#333")
    # south / arousal- : "CALM"
    ax.text((to_x(-1) + to_x(1)) / 2, to_y(-1) - 0.18, "↓  calm",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#333")
    # east / valence+ : "PLEASANT"
    ax.text(to_x(1) + 0.18, (to_y(-1) + to_y(1)) / 2,
            "pleasant  →  VALENCE",
            ha="left", va="center", fontsize=9, fontweight="bold",
            color="#333", rotation=90)
    # west / valence- : "UNPLEASANT"
    ax.text(to_x(-1) - 0.18, (to_y(-1) + to_y(1)) / 2,
            "unpleasant  ←",
            ha="right", va="center", fontsize=9, fontweight="bold",
            color="#333", rotation=90)

    # quadrant label hints
    ax.text(to_x(0.5), to_y(0.5), "excited /\nhappy",
            ha="center", va="center", fontsize=8.5, color="#7a6500",
            alpha=0.75)
    ax.text(to_x(-0.5), to_y(0.5), "tense /\nangry",
            ha="center", va="center", fontsize=8.5, color="#9a3a35",
            alpha=0.75)
    ax.text(to_x(-0.5), to_y(-0.5), "sad /\nmelancholic",
            ha="center", va="center", fontsize=8.5, color="#2c4a86",
            alpha=0.75)
    ax.text(to_x(0.5), to_y(-0.5), "calm /\nserene",
            ha="center", va="center", fontsize=8.5, color="#2e5a25",
            alpha=0.75)

    # ---- draggable point at (-0.3, -0.5) ----
    pt_v, pt_a = -0.3, -0.5
    px, py = to_x(pt_v), to_y(pt_a)

    # halo (suggests it's interactive)
    ax.add_patch(Circle((px, py), 0.32, facecolor="#3a7a3a",
                        edgecolor="none", alpha=0.20))
    ax.add_patch(Circle((px, py), 0.18, facecolor="#3a7a3a",
                        edgecolor="none", alpha=0.35))
    ax.add_patch(Circle((px, py), 0.11, facecolor="#ffffff",
                        edgecolor="#1f4d1f", linewidth=1.8, zorder=5))

    # tooltip box pointing to the point
    tip_w, tip_h = 1.85, 0.85
    tip_x = px + 0.35
    tip_y = py + 0.30
    _rounded_box(ax, tip_x, tip_y, tip_w, tip_h, "",
                 "#ffffff", "#222")
    ax.text(tip_x + tip_w / 2, tip_y + tip_h - 0.22,
            "calm / serene",
            ha="center", va="center", fontsize=9.5, fontweight="bold",
            color="#222")
    ax.text(tip_x + tip_w / 2, tip_y + 0.20,
            f"V={pt_v:+.2f}   A={pt_a:+.2f}",
            ha="center", va="center", fontsize=8.5, color="#444",
            family="monospace")
    # tooltip arrow (leader line) from box to point
    ax.plot([tip_x, px + 0.10], [tip_y + 0.1, py + 0.07],
            color="#222", lw=1.0)

    # ---- footer hint ----
    ax.text(5.0, 0.55,
            "(rendered by matplotlib as a screenshot stand-in; "
            "actual UI is React + canvas)",
            ha="center", va="center", fontsize=7.5, color="#888",
            style="italic")

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------- main ----------------------------------------------------------


def main() -> None:
    outputs = [
        ("fig_system_arch.png",      fig_system_arch),
        ("fig_endpoint_flow.png",    fig_endpoint_flow),
        ("fig_va_panel_mockup.png",  fig_va_panel_mockup),
    ]
    for name, fn in outputs:
        out_path = FIG_DIR / name
        fn(out_path)
        print(f"wrote {out_path}")

    # sanity check
    missing = [n for n, _ in outputs if not (FIG_DIR / n).exists()]
    if missing:
        raise SystemExit(f"missing outputs: {missing}")
    print("all 3 figures produced.")


if __name__ == "__main__":
    main()
