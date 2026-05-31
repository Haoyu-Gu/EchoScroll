"""Visualizations for M6 Prompt Translator.

Generates three PNG figures into ./figures/:
    1. fig_prompt_table.png  -- 8 example inputs -> 8-slot outputs as a table,
                                with cells highlighted when they differ from
                                the neutral default state.
    2. fig_slot_heatmap.png  -- categorical heatmap (8 inputs x 8 slots),
                                each value mapped to a distinct color, with
                                the actual value string annotated in each cell.
    3. fig_pipeline.png      -- boxes-and-arrows schematic of the translator
                                pipeline: user prompt -> [LLM | rule] auto-select
                                -> 8-slot structured output -> MusicGen.

Run:
    python viz.py
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from translator import DEFAULT_STATE, SLOTS, RuleBasedTranslator


# ---------------------------------------------------------------------------
# CJK-safe font setup: half the demo inputs are Chinese, so the figures need
# a font with CJK glyphs or the labels render as tofu boxes.
# ---------------------------------------------------------------------------

def _pick_cjk_font_family() -> list[str]:
    candidates = [
        "PingFang SC", "PingFang TC", "Heiti SC", "Heiti TC", "STHeiti",
        "Songti SC", "Hiragino Sans GB", "Arial Unicode MS",
        "Noto Sans CJK SC", "Source Han Sans SC",
        "Microsoft YaHei", "SimHei",
        "DejaVu Sans",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    return [c for c in candidates if c in available] or ["DejaVu Sans"]


matplotlib.rcParams["font.family"] = _pick_cjk_font_family()
matplotlib.rcParams["axes.unicode_minus"] = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEMO_INPUTS = [
    "再空一点",
    "更激烈",
    "make it gentler",
    "古风一点，加点琴",
    "slow piano",
    "joyful and energetic",
    "黑暗压抑",
    "明朗活泼",
]

# Per spec: input | tempo | mode | register | texture | dynamics | articulation | instruments
TABLE_SLOTS = ["tempo", "mode", "register", "texture",
               "dynamics", "articulation", "instrumentation"]
TABLE_HEADERS = ["input"] + ["tempo", "mode", "register", "texture",
                             "dynamics", "articulation", "instruments"]

# Heatmap: all 8 slots in canonical order.
HEATMAP_SLOTS = list(SLOTS)


FIG_DIR = Path(__file__).parent / "figures"


# ---------------------------------------------------------------------------
# Translate the demo inputs once and share the rows.
# ---------------------------------------------------------------------------

def _translate_all() -> list[dict]:
    rule = RuleBasedTranslator()
    base = dict(DEFAULT_STATE)
    rows = []
    for p in DEMO_INPUTS:
        out = rule.translate(p, current_state=base)
        rows.append(out)
    return rows


def _slot_value_str(state: dict, slot: str) -> str:
    v = state[slot]
    if isinstance(v, list):
        return ", ".join(v)
    return str(v)


def _default_value_str(slot: str) -> str:
    v = DEFAULT_STATE[slot]
    if isinstance(v, list):
        return ", ".join(v)
    return str(v)


# ---------------------------------------------------------------------------
# Figure 1: rendered table
# ---------------------------------------------------------------------------

def make_prompt_table(rows: list[dict], outfile: Path) -> None:
    data = []
    diff_mask = []  # True where cell differs from DEFAULT_STATE
    for prompt, state in zip(DEMO_INPUTS, rows):
        row = [prompt]
        mask = [False]  # input column never highlighted
        for slot in TABLE_SLOTS:
            cell = _slot_value_str(state, slot)
            row.append(cell)
            mask.append(cell != _default_value_str(slot))
        data.append(row)
        diff_mask.append(mask)

    n_rows = len(data)
    n_cols = len(TABLE_HEADERS)

    fig, ax = plt.subplots(figsize=(n_cols * 1.55 + 1.5, n_rows * 0.55 + 1.2))
    ax.set_axis_off()
    ax.set_title("M6 Prompt Translator -- example inputs to 8-slot outputs\n"
                 "(highlighted cells differ from neutral default)",
                 fontsize=12, pad=14)

    tbl = ax.table(
        cellText=data,
        colLabels=TABLE_HEADERS,
        loc="center",
        cellLoc="center",
        colLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.55)

    # Style header row.
    for c in range(n_cols):
        h = tbl[(0, c)]
        h.set_facecolor("#2C3E50")
        h.set_text_props(color="white", weight="bold")

    # Style body cells.
    for r in range(n_rows):
        for c in range(n_cols):
            cell = tbl[(r + 1, c)]
            if c == 0:
                # input column
                cell.set_facecolor("#ECF0F1")
                cell.set_text_props(weight="bold")
            elif diff_mask[r][c]:
                # changed slot vs default
                cell.set_facecolor("#FFE9A8")
                cell.set_text_props(weight="bold", color="#7F4A00")
            else:
                cell.set_facecolor("#FAFAFA")
                cell.set_text_props(color="#7F8C8D")

    # Slightly widen the instruments column since strings are longer.
    try:
        for r in range(n_rows + 1):
            tbl[(r, n_cols - 1)].set_width(tbl[(r, n_cols - 1)].get_width() * 1.45)
    except KeyError:
        pass

    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: categorical heatmap
# ---------------------------------------------------------------------------

def make_slot_heatmap(rows: list[dict], outfile: Path) -> None:
    # Build a string DataFrame (rows x slots) of the actual values.
    str_grid = []
    for state in rows:
        str_grid.append([_slot_value_str(state, s) for s in HEATMAP_SLOTS])
    df_str = pd.DataFrame(str_grid, index=DEMO_INPUTS, columns=HEATMAP_SLOTS)

    # Map each unique value to a distinct integer code; build a numeric grid
    # so heatmap can color by category.
    unique_values = sorted({v for row in str_grid for v in row})
    code_of = {v: i for i, v in enumerate(unique_values)}
    num_grid = np.array([[code_of[v] for v in row] for row in str_grid])

    n_vals = len(unique_values)
    # Use a qualitative palette that scales to however many distinct values appear.
    palette = sns.color_palette("tab20", n_colors=max(n_vals, 3))[:n_vals]
    cmap = matplotlib.colors.ListedColormap(palette)

    fig_w = max(10, len(HEATMAP_SLOTS) * 1.6)
    fig_h = max(5, len(DEMO_INPUTS) * 0.65 + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    sns.heatmap(
        num_grid,
        ax=ax,
        cmap=cmap,
        cbar=False,
        annot=df_str.values,
        fmt="",
        linewidths=0.6,
        linecolor="white",
        xticklabels=HEATMAP_SLOTS,
        yticklabels=DEMO_INPUTS,
        annot_kws={"fontsize": 8, "color": "black"},
    )
    ax.set_title("M6 Prompt Translator -- 8-slot categorical heatmap\n"
                 "(color encodes which value; rows = prompts, cols = slots)",
                 fontsize=12, pad=12)
    ax.set_xlabel("slot", fontsize=10)
    ax.set_ylabel("user prompt", fontsize=10)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)

    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: pipeline schematic
# ---------------------------------------------------------------------------

def _box(ax, x, y, w, h, text, facecolor, edgecolor="#2C3E50",
         text_color="black", fontsize=11, weight="normal"):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.6,
        facecolor=facecolor,
        edgecolor=edgecolor,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center",
            fontsize=fontsize, color=text_color, weight=weight,
            wrap=True)


def _arrow(ax, x1, y1, x2, y2, color="#34495E", style="-|>"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        mutation_scale=18,
        linewidth=1.8,
        color=color,
    ))


def make_pipeline(outfile: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 6.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.2)
    ax.set_axis_off()
    ax.set_title("M6 Prompt Translator -- pipeline",
                 fontsize=13, weight="bold", pad=10)

    # Stage 1: user prompt
    _box(ax, 0.2, 2.7, 2.0, 1.2,
         'user prompt\n(zh / en)\ne.g. "再空一点"',
         facecolor="#ECF0F1",
         fontsize=10, weight="bold")

    # Stage 2: auto-select router
    _box(ax, 2.9, 2.7, 2.0, 1.2,
         "auto-select\nbackend router\n(API key / deps)",
         facecolor="#D6EAF8",
         fontsize=10, weight="bold")

    # Stage 3: two parallel paths
    _box(ax, 5.6, 4.1, 2.4, 1.1,
         "LLM path\nAnthropic / OpenAI /\nlocal Qwen",
         facecolor="#FCF3CF",
         fontsize=10, weight="bold")
    _box(ax, 5.6, 1.4, 2.4, 1.1,
         "Rule path\nregex dictionary\n(always available)",
         facecolor="#FADBD8",
         fontsize=10, weight="bold")

    # Stage 4: structured 8-slot output
    slot_lines = ("tempo  |  mode  |  meter\nregister  |  texture  |  dynamics\n"
                  "articulation  |  instrumentation")
    _box(ax, 8.7, 2.45, 3.5, 1.65,
         "8-slot structured output\n(JSON)\n\n" + slot_lines,
         facecolor="#D5F5E3",
         fontsize=8.5, weight="bold")

    # Stage 5: MusicGen consumer (sits to the far right, below)
    _box(ax, 9.8, 0.35, 2.4, 1.0,
         "MusicGen\ncondition prompt",
         facecolor="#E8DAEF",
         fontsize=10, weight="bold")

    # Arrows
    _arrow(ax, 2.2, 3.3, 2.9, 3.3)            # prompt -> router
    _arrow(ax, 4.9, 3.5, 5.6, 4.55)           # router -> LLM
    _arrow(ax, 4.9, 3.1, 5.6, 1.95)           # router -> Rule
    _arrow(ax, 8.0, 4.55, 8.7, 3.65)          # LLM   -> output
    _arrow(ax, 8.0, 1.95, 8.7, 2.85)          # Rule  -> output
    # output -> MusicGen
    _arrow(ax, 11.0, 2.45, 11.0, 1.35)

    # Fallback dashed arrow LLM -> Rule
    ax.add_patch(FancyArrowPatch(
        (6.8, 4.1), (6.8, 2.5),
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.3,
        linestyle=(0, (4, 3)),
        color="#7F8C8D",
    ))
    ax.text(6.95, 3.3, "fallback on\nfailure / non-JSON",
            fontsize=8, color="#7F8C8D",
            ha="left", va="center", style="italic")

    # Legend
    legend_handles = [
        mpatches.Patch(facecolor="#FCF3CF", edgecolor="#2C3E50", label="LLM path"),
        mpatches.Patch(facecolor="#FADBD8", edgecolor="#2C3E50", label="Rule path"),
        mpatches.Patch(facecolor="#D5F5E3", edgecolor="#2C3E50", label="Structured output"),
        mpatches.Patch(facecolor="#E8DAEF", edgecolor="#2C3E50", label="Downstream consumer"),
    ]
    ax.legend(handles=legend_handles, loc="lower left",
              bbox_to_anchor=(0.0, -0.02), ncol=4, frameon=False, fontsize=9)

    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = _translate_all()

    out1 = FIG_DIR / "fig_prompt_table.png"
    out2 = FIG_DIR / "fig_slot_heatmap.png"
    out3 = FIG_DIR / "fig_pipeline.png"

    make_prompt_table(rows, out1)
    make_slot_heatmap(rows, out2)
    make_pipeline(out3)

    for p in (out1, out2, out3):
        assert p.exists(), f"missing {p}"
        print(f"wrote {p}  ({p.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
