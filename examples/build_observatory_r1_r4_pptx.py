#!/usr/bin/env python3
"""Build Fieldglass Observatory Expansion PowerPoint Deck (16 slides, 16:9).

Covers R1 (MS-DOS, Flight Sim, Medical Sim [Non-Clinical], Software),
R2 (Improvements Hub + dedicated slides for ChatGPT, Anthropic, Grok, SpaceX,
and Claire aka Grimes + KPI Synthesis),
R3 (Zoe Hospital Edition — Windows 7 SP1, Non-Clinical), and
R4/R5 (Observatory Integration, Media Hygiene & Verification).

Outputs byte-identical .pptx files to:
  - /home/cowboy/fieldglass/docs/Fieldglass_Observatory_Expansion.pptx
  - /home/cowboy/fieldglass/Fieldglass_Observatory_Expansion.pptx

Runs directly under bare /usr/bin/python3 via conditional sys.path fallback.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Conditional sys.path bootstrap so bare /usr/bin/python3 finds python-pptx
_SECTOOLS_SITE = pathlib.Path("/home/cowboy/security-tools/lib/python3.14/site-packages")
if importlib.util.find_spec("pptx") is None and _SECTOOLS_SITE.is_dir():
    sys.path.insert(0, str(_SECTOOLS_SITE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------------------
# Paths & Palette (Archival Botanical-Observatory Theme)
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
OUT_DOCS_PPTX = DOCS_ROOT / "Fieldglass_Observatory_Expansion.pptx"
OUT_ROOT_PPTX = REPO_ROOT / "Fieldglass_Observatory_Expansion.pptx"
MAX_FILE_BYTES = 50 * 1024 * 1024

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
TOTAL_SLIDES = 16

# Colors
C_PARCHMENT = RGBColor(0xF7, 0xF4, 0xEC)   # Warm archival paper
C_CARD      = RGBColor(0xFF, 0xFE, 0xFB)   # Bright paper card
C_CARD_TINT = RGBColor(0xEF, 0xEA, 0xDF)   # Warm stone tint
C_BORDER    = RGBColor(0xD8, 0xCF, 0xBF)   # Hairline archival border
C_SLATE_BG  = RGBColor(0x11, 0x18, 0x22)   # Deep observatory midnight
C_SLATE_CRD = RGBColor(0x1A, 0x24, 0x33)   # Dark card surface
C_SLATE_BDR = RGBColor(0x2D, 0x3C, 0x52)   # Dark card hairline

C_INK       = RGBColor(0x1B, 0x23, 0x2E)   # Primary dark ink
C_MUTED     = RGBColor(0x55, 0x62, 0x72)   # Secondary muted ink
C_LIGHT_INK = RGBColor(0xF3, 0xEF, 0xE6)   # Primary text on dark slides
C_LIGHT_MUT = RGBColor(0xA6, 0xB4, 0xC6)   # Secondary text on dark slides

C_INDIGO    = RGBColor(0x1E, 0x41, 0x7A)   # Prussian indigo
C_COPPER    = RGBColor(0xB8, 0x7A, 0x28)   # Archival copper / brass
C_GOLD      = RGBColor(0xDC, 0xA8, 0x54)   # Bright brass gold
C_RUBY      = RGBColor(0xB9, 0x34, 0x44)   # Telemetry / non-clinical ruby
C_RUBY_BG   = RGBColor(0x36, 0x12, 0x19)   # Deep ruby banner fill
C_SAGE      = RGBColor(0x2B, 0x6E, 0x5D)   # Botanical observatory sage
C_TEAL      = RGBColor(0x3E, 0x92, 0x8A)   # Bright teal for dark slides
C_CYAN      = RGBColor(0x5E, 0xDA, 0xF0)   # Telemetry cyan
C_VIOLET    = RGBColor(0x8E, 0x58, 0xD6)   # Creative violet (Claire/Grimes)

FONT_SERIF = "Liberation Serif"
FONT_SANS  = "Liberation Sans"
FONT_MONO  = "DejaVu Sans Mono"

R1_SLUGS = ("msdos", "flight-sim", "medical-sim", "software")
R2_SLUGS = ("chatgpt", "anthropic", "grok", "spacex", "claire-grimes")


# ---------------------------------------------------------------------------
# Data Loading & Contract Assertions
# ---------------------------------------------------------------------------
def _assert_base_contract(obj: Dict[str, Any], label: str) -> None:
    assert obj.get("executed") is False, f"{label}: executed must be False"
    assert obj.get("sentience_claimed") is False, f"{label}: sentience_claimed must be False"
    assert obj.get("tokens_used") == 0, f"{label}: tokens_used must be 0"


def _assert_non_clinical(obj: Dict[str, Any], label: str) -> None:
    assert obj.get("clinical_use") is False, f"{label}: clinical_use must be False"
    assert obj.get("educational_simulation_only") is True, f"{label}: educational_simulation_only must be True"
    assert obj.get("clinical_certification_claimed") is False, f"{label}: clinical_certification_claimed must be False"


def load_observatory_data() -> Dict[str, Any]:
    """Load and verify all M1-M3 JSON manifests, reports, and image paths."""
    r1: Dict[str, Any] = {}
    for domain in R1_SLUGS:
        ddir = DOCS_ROOT / domain
        summary = json.loads((ddir / "summary.json").read_text(encoding="utf-8"))
        chiasm = json.loads((ddir / "chiasm_report.json").read_text(encoding="utf-8"))
        _assert_base_contract(summary, f"R1/{domain}/summary.json")
        _assert_base_contract(chiasm, f"R1/{domain}/chiasm_report.json")
        if domain == "medical-sim":
            _assert_non_clinical(summary, "R1/medical-sim/summary.json")
            _assert_non_clinical(chiasm, "R1/medical-sim/chiasm_report.json")
        preview = ddir / summary["assets"]["preview_png"]
        braille_preview = ddir / summary["assets"]["braille_preview_png"]
        assert preview.is_file(), f"Missing {preview}"
        assert braille_preview.is_file(), f"Missing {braille_preview}"
        r1[domain] = {
            "summary": summary,
            "chiasm": chiasm,
            "preview": preview,
            "braille_preview": braille_preview,
        }

    imp_dir = DOCS_ROOT / "improvements"
    r2_hub = json.loads((imp_dir / "summary.json").read_text(encoding="utf-8"))
    _assert_base_contract(r2_hub, "R2/improvements/summary.json")
    assert r2_hub.get("clinical_use") is False
    assert (imp_dir / "preview.png").is_file()

    r2_subjects: Dict[str, Any] = {}
    for subj in r2_hub["subjects"]:
        slug = subj["slug"]
        assert slug in R2_SLUGS
        sdir = imp_dir / slug
        chiasm = json.loads((sdir / "chiasm_report.json").read_text(encoding="utf-8"))
        _assert_base_contract(subj, f"R2/{slug}/summary")
        _assert_base_contract(chiasm, f"R2/{slug}/chiasm_report.json")
        assert subj.get("clinical_use") is False
        preview = sdir / "preview.png"
        braille_preview = sdir / f"{slug}_braille_preview.png"
        assert preview.is_file(), f"Missing {preview}"
        assert braille_preview.is_file(), f"Missing {braille_preview}"
        r2_subjects[slug] = {
            "summary": subj,
            "chiasm": chiasm,
            "preview": preview,
            "braille_preview": braille_preview,
        }

    zh_dir = DOCS_ROOT / "zoe-hospital"
    zh_summary = json.loads((zh_dir / "summary.json").read_text(encoding="utf-8"))
    zh_manifest = json.loads((zh_dir / "manifest.json").read_text(encoding="utf-8"))
    zh_chiasm = json.loads((zh_dir / "chiasm_report.json").read_text(encoding="utf-8"))
    for name, obj in (("summary.json", zh_summary), ("manifest.json", zh_manifest), ("chiasm_report.json", zh_chiasm)):
        _assert_base_contract(obj, f"R3/zoe-hospital/{name}")
        _assert_non_clinical(obj, f"R3/zoe-hospital/{name}")
    assert (zh_dir / "preview.png").is_file()
    assert (zh_dir / zh_manifest["bundle_zip"]).is_file()

    # Unified 10-module telemetry rows for Chart A
    rows: List[Dict[str, Any]] = []
    m1_labels = {
        "msdos": "R1 MS-DOS",
        "flight-sim": "R1 Flight",
        "medical-sim": "R1 Med-Sim",
        "software": "R1 Software",
    }
    for domain in R1_SLUGS:
        m = r1[domain]["summary"]["metrics"]
        rows.append({
            "slug": domain,
            "label": m1_labels[domain],
            "group": "R1",
            "episodes": int(m["episode_count"]),
            "past_a010": int(m["past_a_010"]),
            "future_a010": int(m["future_a_010"]),
            "ei_bits": float(m["effective_information_bits"]),
            "h1_mean_bits": float(m["h1_mean_bits"]),
        })

    r2_labels = {
        "chatgpt": "R2 ChatGPT",
        "anthropic": "R2 Anthropic",
        "grok": "R2 Grok",
        "spacex": "R2 SpaceX",
        "claire-grimes": "R2 Grimes",
    }
    for slug in R2_SLUGS:
        m = r2_subjects[slug]["summary"]["metrics"]
        ch = r2_subjects[slug]["chiasm"]
        rows.append({
            "slug": slug,
            "label": r2_labels[slug],
            "group": "R2",
            "episodes": int(m["episodes"]),
            "past_a010": int(m["past_a_tau"]),
            "future_a010": int(m["future_a_tau"]),
            "ei_bits": float(m["effective_information_bits"]),
            "h1_mean_bits": float(ch["h1_mean_bits"]),
        })

    zm = zh_summary["metrics"]
    rows.append({
        "slug": "zoe-hospital",
        "label": "R3 Zoe Hosp",
        "group": "R3",
        "episodes": int(zm["episode_count"]),
        "past_a010": int(zm["past_accessible_volume"]),
        "future_a010": int(zm["future_accessible_volume"]),
        "ei_bits": float(zm["effective_information_bits"]),
        "h1_mean_bits": float(zm["mean_h1_bits"]),
    })

    return {
        "r1": r1,
        "r2_hub": r2_hub,
        "r2_hub_preview": imp_dir / "preview.png",
        "r2_subjects": r2_subjects,
        "r3": {
            "summary": zh_summary,
            "manifest": zh_manifest,
            "chiasm": zh_chiasm,
            "preview": zh_dir / "preview.png",
            "bundle_zip": zh_dir / zh_manifest["bundle_zip"],
        },
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Metadata-Clean Image Helper
# ---------------------------------------------------------------------------
def sanitize_png(src: pathlib.Path, tmp_dir: pathlib.Path, tag: str = "") -> pathlib.Path:
    """Re-encode image as clean PNG in tmp_dir with zero EXIF / text metadata."""
    prefix = f"{tag}_" if tag else ""
    dst = tmp_dir / f"clean_{prefix}{src.stem}.png"
    if not dst.exists():
        with Image.open(src) as im:
            clean = ImageOps.exif_transpose(im)
            if clean.mode not in ("RGB", "RGBA"):
                clean = clean.convert("RGB")
            clean.save(dst, format="PNG", pnginfo=PngInfo(), optimize=True)
    return dst


# ---------------------------------------------------------------------------
# High-DPI Matplotlib Charts (300 DPI, metadata={})
# ---------------------------------------------------------------------------
def build_chart_a_telemetry(rows: List[Dict[str, Any]], tmp_dir: pathlib.Path) -> pathlib.Path:
    """Chart A: Past vs Future A_0.10 + EI (bits) & H1 mean across all 10 modules."""
    out_png = tmp_dir / "chart_a_telemetry.png"
    labels = [r["label"] for r in rows]
    past_v = [r["past_a010"] for r in rows]
    fut_v = [r["future_a010"] for r in rows]
    ei_v = [r["ei_bits"] for r in rows]
    h1_v = [r["h1_mean_bits"] for r in rows]
    x = np.arange(len(rows))

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.2, 3.85), dpi=300,
        gridspec_kw={"width_ratios": [1.02, 1.08], "wspace": 0.29},
    )
    fig.patch.set_facecolor("#FFFEFB")

    # Left panel: Past vs Future A_0.10
    ax1.set_facecolor("#FFFEFB")
    w = 0.36
    b1 = ax1.bar(x - w / 2, past_v, width=w, color="#1E417A", label="Past A_0.10", zorder=3)
    b2 = ax1.bar(x + w / 2, fut_v, width=w, color="#2B6E5D", label="Future A_0.10", zorder=3)
    ax1.grid(axis="y", linestyle="--", linewidth=0.6, color="#DDD5C7", zorder=0)
    for sp in ("top", "right"):
        ax1.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax1.spines[sp].set_color("#B8AF9F")

    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0, h + 0.14, f"{int(h)}",
            ha="center", va="bottom", fontsize=6.9, fontweight="bold", color="#1B232E",
        )
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=32, ha="right", fontsize=7.4, color="#1B232E")
    ax1.set_ylabel("Accessible States (tau = 0.10)", fontsize=8.4, fontweight="bold", color="#1B232E")
    ax1.set_ylim(0, 8.8)
    ax1.set_title("Chiasm Accessible Volume: Past vs. Future A_0.10", fontsize=9.8, fontweight="bold", color="#1B232E", loc="left", pad=8)
    ax1.legend(loc="upper right", frameon=True, facecolor="#F7F4EC", edgecolor="#D8CFBF", fontsize=7.2, ncol=2)

    # Right panel: Effective Info (bits) + Mean H1
    ax2.set_facecolor("#FFFEFB")
    ax2.grid(axis="y", linestyle="--", linewidth=0.6, color="#DDD5C7", zorder=0)
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_color("#B87A28")
    ax2.spines["bottom"].set_color("#B8AF9F")

    bar_cols = ["#2B6E5D" if r["group"] == "R1" else ("#1E417A" if r["group"] == "R2" else "#B93444") for r in rows]
    bars_ei = ax2.bar(x, ei_v, width=0.56, color=bar_cols, alpha=0.88, label="Effective Info EI (bits)", zorder=3)
    for b, val in zip(bars_ei, ei_v):
        ax2.text(
            b.get_x() + b.get_width() / 2.0, val + 0.012, f"{val:.3f}",
            ha="center", va="bottom", fontsize=6.4, fontweight="bold", color="#1B232E",
        )

    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=32, ha="right", fontsize=7.4, color="#1B232E")
    ax2.set_ylabel("Effective Information EI (bits)", fontsize=8.4, fontweight="bold", color="#1E417A")
    ax2.set_ylim(0, 0.58)
    ax2.set_title("Effective Information (EI) & Mean Shannon Entropy H1", fontsize=9.8, fontweight="bold", color="#1B232E", loc="left", pad=8)

    ax2b = ax2.twinx()
    ax2b.spines["top"].set_visible(False)
    ax2b.spines["right"].set_color("#B93444")
    ax2b.plot(x, h1_v, color="#B93444", marker="o", markersize=4.5, linewidth=1.7, label="Mean H1 (bits)", zorder=5)
    ax2b.set_ylabel("Mean H1 Entropy (bits)", fontsize=8.4, fontweight="bold", color="#B93444")
    ax2b.set_ylim(2.4, 3.15)
    ax2b.tick_params(axis="y", colors="#B93444", labelsize=7.6)
    ax2.tick_params(axis="y", colors="#1E417A", labelsize=7.6)

    h1_handles, h1_labels = ax2.get_legend_handles_labels()
    h2_handles, h2_labels = ax2b.get_legend_handles_labels()
    ax2.legend(h1_handles + h2_handles, h1_labels + h2_labels, loc="upper right", frameon=True, facecolor="#F7F4EC", edgecolor="#D8CFBF", fontsize=7.0, ncol=2)

    fig.subplots_adjust(left=0.055, right=0.935, top=0.88, bottom=0.23)
    fig.savefig(out_png, dpi=300, facecolor=fig.get_facecolor(), metadata={})
    plt.close(fig)
    return out_png


def build_chart_b_r2_uplift(tmp_dir: pathlib.Path) -> pathlib.Path:
    """Chart B: Headline Baseline -> Target KPI uplift across all 5 R2 subjects."""
    out_png = tmp_dir / "chart_b_r2_uplift.png"

    # Two clean panels: Error/Risk Reduction (lower is better) & Capability/Recall Gain (higher is better)
    risk_metrics = [
        ("ChatGPT · Schema Retry (%)", 11.4, 0.8, "#1E417A"),
        ("ChatGPT · Sycophancy Rev. (%)", 18.5, 2.0, "#1E417A"),
        ("Anthropic · OOS MCP Writes (%)", 4.2, 0.0, "#B87A28"),
        ("Grok · Rumor Conflation (%)", 19.2, 3.8, "#B93444"),
        ("Grok · Truncated Chart Misread (%)", 27.0, 4.5, "#B93444"),
        ("SpaceX · LEO Handover Loss (%)", 2.40, 0.05, "#2B6E5D"),
        ("Grimes · Live Dead-Air Risk (%)", 8.5, 0.3, "#7B46B8"),
    ]
    gain_metrics = [
        ("Anthropic · Anomaly Recall (%)", 34.0, 86.0, "#B87A28"),
        ("Anthropic · Post-Compact Recall (%)", 71.0, 96.0, "#B87A28"),
        ("Grok · Precision@10 Bot-Echo (%)", 54.0, 76.0, "#B93444"),
        ("Grok · Auditability & ARIA (%)", 52.0, 91.0, "#B93444"),
        ("SpaceX · SHA-256 Frame Verif. (%)", 18.0, 100.0, "#2B6E5D"),
        ("SpaceX · Braille Flight Comp. (%)", 5.0, 92.0, "#2B6E5D"),
        ("Grimes · Stem Attribution (%)", 31.0, 95.0, "#7B46B8"),
    ]

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.2, 3.65), dpi=300,
        gridspec_kw={"width_ratios": [1.0, 1.0], "wspace": 0.64},
    )
    fig.patch.set_facecolor("#FFFEFB")

    def _dumbbell(ax, items, title, xlim, is_reduction: bool):
        ax.set_facecolor("#FFFEFB")
        y = np.arange(len(items))[::-1]
        for yi, (lbl, base, targ, col) in zip(y, items):
            ax.plot([base, targ], [yi, yi], color="#8E9BAE", linewidth=2.2, zorder=2)
            ax.scatter([base], [yi], color="#9AA5B4", s=44, zorder=3, edgecolors="#1B232E", linewidths=0.6)
            ax.scatter([targ], [yi], color=col, s=56, zorder=4, edgecolors="#1B232E", linewidths=0.7)
            if is_reduction:
                ax.text(base + xlim * 0.022, yi, f"{base:g}% -> {targ:g}%", va="center", ha="left", fontsize=7.0, fontweight="bold", color="#1B232E")
            else:
                ax.text(min(targ + xlim * 0.022, xlim * 0.99), yi, f"{base:g}% -> {targ:g}%", va="center", ha="left", fontsize=7.0, fontweight="bold", color="#1B232E")
        ax.set_yticks(y)
        ax.set_yticklabels([it[0] for it in items], fontsize=7.4, color="#1B232E")
        ax.set_xlim(-xlim * 0.04, xlim)
        ax.grid(axis="x", linestyle="--", linewidth=0.6, color="#DDD5C7", zorder=0)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color("#B8AF9F")
        ax.set_xlabel("Percentage (%)", fontsize=8.0, fontweight="bold", color="#1B232E")
        ax.set_title(title, fontsize=9.2, fontweight="bold", color="#1B232E", loc="left", pad=8)

    _dumbbell(ax1, risk_metrics, "Failure / Error Rate Reduction (Baseline -> Target)", 43.0, True)
    _dumbbell(ax2, gain_metrics, "Verification, Recall & Accessibility Uplift", 136.0, False)

    fig.subplots_adjust(left=0.205, right=0.975, top=0.88, bottom=0.16)
    fig.savefig(out_png, dpi=300, facecolor=fig.get_facecolor(), metadata={})
    plt.close(fig)
    return out_png


# ---------------------------------------------------------------------------
# Slide Helper Primitives
# ---------------------------------------------------------------------------
def set_slide_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(
    slide, x: float, y: float, w: float, h: float,
    fill: Optional[RGBColor] = None,
    line: Optional[RGBColor] = None,
    line_pt: float = 0.75,
    rounded: bool = False,
    radius: float = 0.04,
):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if rounded and hasattr(shp, "adjustments") and len(shp.adjustments) > 0:
        shp.adjustments[0] = radius
    if fill is not None:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if line is not None:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_pt)
    else:
        shp.line.fill.background()
    return shp


def add_textbox(
    slide, x: float, y: float, w: float, h: float,
    text: str = "",
    font_name: str = FONT_SANS,
    font_size: float = 11.0,
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = C_INK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    line_spacing: float = 1.15,
    margin: Tuple[float, float, float, float] = (0.03, 0.03, 0.02, 0.02),
    hyperlink: Optional[str] = None,
):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(margin[0])
    tf.margin_right = Inches(margin[1])
    tf.margin_top = Inches(margin[2])
    tf.margin_bottom = Inches(margin[3])

    for idx, line_str in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line_str
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
    if hyperlink:
        tb.click_action.hyperlink.address = hyperlink
    return tb


def add_bullets(
    slide, x: float, y: float, w: float, h: float,
    items: Sequence[Tuple[str, str]],
    font_size: float = 9.8,
    lead_color: RGBColor = C_INDIGO,
    body_color: RGBColor = C_INK,
    bullet_char: str = "▪  ",
    space_after_pt: float = 4.0,
    line_spacing: float = 1.15,
):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    for idx, (lead, body) in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after_pt)

        r0 = p.add_run()
        r0.text = bullet_char
        r0.font.name = FONT_SANS
        r0.font.size = Pt(font_size)
        r0.font.bold = True
        r0.font.color.rgb = lead_color

        if lead:
            r1 = p.add_run()
            r1.text = lead + " "
            r1.font.name = FONT_SANS
            r1.font.size = Pt(font_size)
            r1.font.bold = True
            r1.font.color.rgb = lead_color

        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_SANS
        r2.font.size = Pt(font_size)
        r2.font.color.rgb = body_color
    return tb


def add_badge(
    slide, x: float, y: float, w: float, h: float,
    text: str, bg: RGBColor, fg: RGBColor = C_LIGHT_INK, font_size: float = 8.0,
    border: Optional[RGBColor] = None,
):
    add_rect(slide, x, y, w, h, fill=bg, line=border, line_pt=0.75 if border else 0.0, rounded=True, radius=0.35)
    add_textbox(
        slide, x, y, w, h, text=text,
        font_name=FONT_MONO, font_size=font_size, bold=True, color=fg,
        align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=(0.03, 0.03, 0.0, 0.0),
    )


def add_picture_contain(
    slide, img_path: pathlib.Path,
    x: float, y: float, w: float, h: float,
    frame_fill: Optional[RGBColor] = None,
    frame_line: Optional[RGBColor] = None,
    pad: float = 0.05,
    rounded: bool = True,
):
    if frame_fill is not None or frame_line is not None:
        add_rect(slide, x, y, w, h, fill=frame_fill, line=frame_line, line_pt=0.75, rounded=rounded, radius=0.03)
    with Image.open(img_path) as im:
        iw, ih = im.size
    box_w = max(0.1, w - 2 * pad)
    box_h = max(0.1, h - 2 * pad)
    scale = min(box_w / iw, box_h / ih)
    pw = iw * scale
    ph = ih * scale
    px = x + (w - pw) / 2.0
    py = y + (h - ph) / 2.0
    return slide.shapes.add_picture(str(img_path), Inches(px), Inches(py), width=Inches(pw), height=Inches(ph))


def add_header_footer(
    slide, slide_num: int, eyebrow: str, title: str, subtitle: str = "",
    dark: bool = False, accent: RGBColor = C_INDIGO,
    footer_note: str = "Fieldglass Observatory Expansion  ·  R1–R5  ·  Zero Cloud Tokens ($0.00)",
):
    ink = C_LIGHT_INK if dark else C_INK
    mut = C_LIGHT_MUT if dark else C_MUTED
    rule = C_SLATE_BDR if dark else C_BORDER

    add_rect(slide, 0, 0, 13.333, 0.06, fill=accent, line=None)
    add_textbox(
        slide, 0.55, 0.20, 10.5, 0.22,
        text=eyebrow.upper(),
        font_name=FONT_MONO, font_size=8.0, bold=True, color=accent,
        margin=(0, 0, 0, 0),
    )
    add_textbox(
        slide, 0.55, 0.41, 12.23, 0.45,
        text=title,
        font_name=FONT_SERIF, font_size=22.0, bold=True, color=ink,
        margin=(0, 0, 0, 0),
    )
    if subtitle:
        add_textbox(
            slide, 0.55, 0.87, 12.23, 0.28,
            text=subtitle,
            font_name=FONT_SANS, font_size=10.2, color=mut,
            margin=(0, 0, 0, 0),
        )
        rule_y = 1.18
    else:
        rule_y = 0.92

    add_rect(slide, 0.55, rule_y, 12.23, 0.015, fill=rule, line=None)
    add_rect(slide, 0.55, 7.08, 12.23, 0.012, fill=rule, line=None)
    add_textbox(
        slide, 0.55, 7.13, 10.0, 0.24,
        text=footer_note,
        font_name=FONT_MONO, font_size=7.6, color=mut, margin=(0, 0, 0, 0),
    )
    add_textbox(
        slide, 11.4, 7.13, 1.38, 0.24,
        text=f"{slide_num:02d} / {TOTAL_SLIDES:02d}",
        font_name=FONT_MONO, font_size=8.2, bold=True, color=accent,
        align=PP_ALIGN.RIGHT, margin=(0, 0, 0, 0),
    )


def add_non_clinical_banner(slide, x: float, y: float, w: float, text: str, dark: bool = True) -> None:
    bg = C_RUBY_BG if dark else RGBColor(0xFD, 0xEC, 0xEE)
    fg = RGBColor(0xFF, 0xD6, 0xDC) if dark else C_RUBY
    add_rect(slide, x, y, w, 0.34, fill=bg, line=C_RUBY, line_pt=1.0, rounded=True, radius=0.18)
    add_textbox(
        slide, x + 0.12, y, w - 0.24, 0.34,
        text=text,
        font_name=FONT_MONO, font_size=8.2, bold=True, color=fg,
        align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=(0, 0, 0, 0),
    )


# ---------------------------------------------------------------------------
# Individual Slides (01–16)
# ---------------------------------------------------------------------------
def build_slide_01_cover(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_SLATE_BG)

    add_rect(slide, 0, 0, 13.333, 0.09, fill=C_GOLD, line=None)
    add_rect(slide, 0.42, 0.34, 12.49, 6.82, fill=None, line=C_SLATE_BDR, line_pt=1.0)
    add_rect(slide, 0.55, 0.52, 0.07, 6.42, fill=C_GOLD, line=None)

    add_badge(slide, 0.82, 0.64, 4.35, 0.30, "OBSERVATORY EXPANSION  ·  R1–R4  ·  NOV 2026", C_SLATE_CRD, C_GOLD, 8.0, border=C_GOLD)

    add_textbox(
        slide, 0.82, 1.06, 6.45, 1.38,
        text="Fieldglass\nObservatory",
        font_name=FONT_SERIF, font_size=42, bold=True, color=C_LIGHT_INK,
        line_spacing=1.02, margin=(0, 0, 0, 0),
    )
    add_textbox(
        slide, 0.82, 2.52, 6.45, 1.15,
        text="R1 Simulators (MS-DOS, 6-DOF Flight, Medical Sandbox, Software)  ·  "
             "R2 Engineering Dossiers (ChatGPT, Anthropic, Grok, SpaceX, Claire / Grimes)  ·  "
             "R3 Zoe Hospital Edition (Windows 7 SP1, Non-Clinical)  ·  "
             "Kloster A_τ(p) & SHA-256 Causal Chiasms.",
        font_name=FONT_SANS, font_size=11.4, color=C_LIGHT_MUT, line_spacing=1.28, margin=(0, 0, 0, 0),
    )

    add_rect(slide, 0.82, 3.74, 6.20, 0.02, fill=C_GOLD, line=None)

    stats = [
        ("10", "New Modules"),
        ("25", "R2 Proposals"),
        ("Win7 SP1", "Hospital Era"),
        ("0", "Clinical Claims"),
    ]
    for i, (val, lbl) in enumerate(stats):
        cx = 0.82 + i * 1.58
        add_rect(slide, cx, 3.92, 1.46, 0.94, fill=C_SLATE_CRD, line=C_SLATE_BDR, line_pt=0.8, rounded=True, radius=0.08)
        add_textbox(slide, cx, 4.02, 1.46, 0.42, val, FONT_SERIF, 18.5 if len(val) > 4 else 21, True, color=C_GOLD, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))
        add_textbox(slide, cx, 4.48, 1.46, 0.30, lbl, FONT_SANS, 8.6, False, color=C_LIGHT_MUT, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))

    add_non_clinical_banner(
        slide, 0.82, 5.04, 6.22,
        "SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL USE (clinical_use=False)",
        dark=True,
    )

    add_textbox(
        slide, 0.82, 5.50, 6.25, 1.38,
        text="Equation: A_τ(p) = |{ x ∈ X : p(x) > τ }|\n"
             "Contract: fieldglass-causal-chiasm/v1  ·  executed=False  ·  sentience_claimed=False\n"
             "Zero Cloud Tokens: tokens_used=0  ·  GPS Metadata Stripped (-map_metadata -1)\n"
             "Live Archive: https://nicholas-michael-kloster.github.io/fieldglass/",
        font_name=FONT_MONO, font_size=8.1, color=C_LIGHT_MUT, line_spacing=1.35, margin=(0, 0, 0, 0),
    )

    # Right 2x2 preview grid
    previews = [
        ("R1.1 · MS-DOS 6.22 & 8086", data["r1"]["msdos"]["preview"], C_GOLD, 7.36, 0.62),
        ("R1.2 · 6-DOF Flight HUD", data["r1"]["flight-sim"]["preview"], C_SLATE_BDR, 10.10, 0.62),
        ("R2 · 5 Improvement Dossiers", data["r2_hub_preview"], C_SLATE_BDR, 7.36, 3.88),
        ("R3 · Zoe Hospital (Win7 SP1)", data["r3"]["preview"], C_RUBY, 10.10, 3.88),
    ]
    for cap, img_p, bdr, px, py in previews:
        clean_p = sanitize_png(img_p, tmp_dir, tag=f"cov_{px:.0f}_{py:.0f}")
        add_picture_contain(slide, clean_p, px, py, 2.58, 2.74, frame_fill=C_SLATE_CRD, frame_line=bdr, pad=0.06, rounded=True)
        add_textbox(slide, px, py + 2.78, 2.58, 0.24, cap, FONT_MONO, 7.4, True, color=C_LIGHT_INK if bdr == C_SLATE_BDR else bdr, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))


def build_slide_02_telemetry_overview(prs: Presentation, data: Dict[str, Any], chart_a: pathlib.Path) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_PARCHMENT)
    add_header_footer(
        slide, 2,
        "01 · Cross-Module Telemetry & Epistemic Contract",
        "Kloster A_τ(p) & Causal Chiasm Synthesis Across All 10 New Modules",
        "Every R1, R2, and R3 deliverable seals past/future repertoire volumes under fieldglass-causal-chiasm/v1 with tokens_used=0.",
        dark=False, accent=C_INDIGO,
    )

    kpis = [
        ("4 Modules", "R1 Simulators", "MS-DOS, Flight, Med, Software", C_SAGE),
        ("5 / 25", "R2 Dossiers & KPIs", "ChatGPT, Anthropic, Grok, SpaceX, Grimes", C_INDIGO),
        ("Win7 SP1", "R3 Zoe Hospital", "ES5/HTA + Py3.7/3.8 Stdlib", C_RUBY),
        ("192", "Sealed Episodes", "56 R1 + 120 R2 + 16 R3", C_COPPER),
        ("0.475 bits", "Peak EI (Software)", "Grok R2 Peak: 0.468 bits", C_INDIGO),
        ("^_^", "Reversible Future", "future_boxed_in=False on all 10", C_SAGE),
    ]
    cw = 1.93
    gap = 0.13
    for i, (val, lbl, sub, acc) in enumerate(kpis):
        x = 0.55 + i * (cw + gap)
        add_rect(slide, x, 1.30, cw, 1.04, fill=C_CARD, line=C_BORDER, line_pt=0.75, rounded=True, radius=0.06)
        add_rect(slide, x, 1.30, cw, 0.06, fill=acc, line=None)
        add_textbox(slide, x + 0.06, 1.39, cw - 0.12, 0.36, val, FONT_SERIF, 18.0, True, color=acc, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))
        add_textbox(slide, x + 0.06, 1.77, cw - 0.12, 0.22, lbl, FONT_SANS, 9.0, True, color=C_INK, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))
        add_textbox(slide, x + 0.05, 2.00, cw - 0.10, 0.28, sub, FONT_SANS, 7.1, False, color=C_MUTED, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))

    add_picture_contain(slide, chart_a, 0.55, 2.44, 12.23, 3.84, frame_fill=C_CARD, frame_line=C_BORDER, pad=0.05, rounded=True)

    add_rect(slide, 0.55, 6.38, 12.23, 0.58, fill=C_SLATE_BG, line=C_GOLD, line_pt=0.8, rounded=True, radius=0.05)
    add_textbox(
        slide, 0.72, 6.44, 11.90, 0.46,
        text="INVARIANTS VERIFIED AT BUILD TIME: executed=False · sentience_claimed=False · tokens_used=0 · "
             "medical-sim & zoe-hospital carry clinical_use=False, educational_simulation_only=True, clinical_certification_claimed=False.",
        font_name=FONT_MONO, font_size=8.0, bold=False, color=C_LIGHT_INK, valign=MSO_ANCHOR.MIDDLE, margin=(0, 0, 0, 0),
    )


def _build_r1_standard_slide(
    prs: Presentation,
    slide_num: int,
    eyebrow: str,
    title: str,
    subtitle: str,
    accent: RGBColor,
    dark: bool,
    domain_data: Dict[str, Any],
    bullets: Sequence[Tuple[str, str]],
    non_clinical_banner: Optional[str],
    tmp_dir: pathlib.Path,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_SLATE_BG if dark else C_PARCHMENT)
    add_header_footer(slide, slide_num, eyebrow, title, subtitle, dark=dark, accent=accent)

    card_bg = C_SLATE_CRD if dark else C_CARD
    card_bdr = C_SLATE_BDR if dark else C_BORDER
    ink = C_LIGHT_INK if dark else C_INK
    mut = C_LIGHT_MUT if dark else C_MUTED

    y_top = 1.30
    if non_clinical_banner:
        add_non_clinical_banner(slide, 0.55, y_top, 12.23, non_clinical_banner, dark=dark)
        y_top += 0.44

    content_h = 6.96 - y_top
    preview_p = sanitize_png(domain_data["preview"], tmp_dir, tag=f"r1_{slide_num}")
    braille_p = sanitize_png(domain_data["braille_preview"], tmp_dir, tag=f"r1b_{slide_num}")

    # Left: Preview image (7.15" wide) + Braille strip bottom-left
    img_h = content_h * 0.68
    add_picture_contain(slide, preview_p, 0.55, y_top, 7.15, img_h, frame_fill=card_bg, frame_line=accent if dark else card_bdr, pad=0.06, rounded=True)

    braille_y = y_top + img_h + 0.12
    braille_h = 6.96 - braille_y
    add_rect(slide, 0.55, braille_y, 7.15, braille_h, fill=card_bg, line=card_bdr, line_pt=0.75, rounded=True, radius=0.04)
    add_picture_contain(slide, braille_p, 0.65, braille_y + 0.06, 2.35, braille_h - 0.12, frame_fill=C_CARD, frame_line=card_bdr, pad=0.03, rounded=False)

    s = domain_data["summary"]
    m = s["metrics"]
    add_textbox(
        slide, 3.14, braille_y + 0.08, 4.44, 0.24,
        f"2×4 BRAILLE + CAUSAL CHIASM SEAL ({s['domain']})",
        FONT_MONO, 7.8, True, color=accent, margin=(0, 0, 0, 0),
    )
    add_textbox(
        slide, 3.14, braille_y + 0.34, 4.44, braille_h - 0.42,
        f"Episodes: {m['episode_count']}  ·  Past→Future A_0.10: {m['past_a_010']} → {m['future_a_010']} ({m['presence_glyph']})\n"
        f"EI = {m['effective_information_bits']:.6f} bits  ·  H1 = {m['h1_mean_bits']:.4f}  ·  H2 = {m['h2_mean_bits']:.4f}  ·  M4 = {m['m4_mean_purity']:.4f}\n"
        f"Route: docs/{s['route']}  ·  SHA-256 Sealed",
        FONT_MONO, 7.5, False, color=ink, line_spacing=1.28, margin=(0, 0, 0, 0),
    )

    # Right: Technical Architecture & Highlights Card
    rx = 7.90
    rw = 4.88
    add_rect(slide, rx, y_top, rw, content_h, fill=card_bg, line=card_bdr, line_pt=0.85, rounded=True, radius=0.05)
    add_rect(slide, rx, y_top, rw, 0.07, fill=accent, line=None)
    add_textbox(slide, rx + 0.18, y_top + 0.18, rw - 0.36, 0.28, "SIMULATOR ARCHITECTURE & VERIFIED HIGHLIGHTS", FONT_MONO, 8.2, True, color=accent, margin=(0, 0, 0, 0))
    add_bullets(
        slide, rx + 0.18, y_top + 0.50, rw - 0.36, content_h - 1.32,
        bullets, font_size=9.4, lead_color=accent, body_color=ink, space_after_pt=5.5, line_spacing=1.18,
    )
    add_rect(slide, rx + 0.18, 6.24, rw - 0.36, 0.58, fill=C_SLATE_BG if not dark else C_BG_BOX(dark), line=card_bdr, line_pt=0.65, rounded=True, radius=0.05)
    add_textbox(
        slide, rx + 0.28, 6.30, rw - 0.56, 0.46,
        f"Contract: {s['contract']}  ·  executed={s['executed']}  ·  tokens_used={s['tokens_used']}",
        FONT_MONO, 7.4, False, color=C_GOLD if not dark else mut, valign=MSO_ANCHOR.MIDDLE, margin=(0, 0, 0, 0),
    )


def C_BG_BOX(dark: bool) -> RGBColor:
    return RGBColor(0x0D, 0x13, 0x1D) if dark else C_PARCHMENT


def build_slide_03_r1_msdos(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    d = data["r1"]["msdos"]
    bullets = [
        ("16-Bit 8086 Real-Mode CPU:", "Interactive CS:IP, DS, SS, SP, FLAGS registers and A20 physical address calculator (seg << 4 + offset)."),
        ("1 MB Memory Map:", "640 KB Conventional RAM + 384 KB Upper Memory Area (UMA) + 64 KB High Memory Area (HMA) visualization."),
        ("1.44 MB FAT12 & COMMAND.COM:", "2,880 sectors × 512 B disk geometry with deterministic DIR, TYPE, MEM, VER, and CHKDSK educational shell."),
        ("Telemetry Integration:", "12 sealed episodes track boot-to-shell state expansion (Past A_0.10 = 4 → Future A_0.10 = 6, EI = 0.2447 bits)."),
    ]
    _build_r1_standard_slide(
        prs, 3,
        "02 · R1 Domain 1 · Legacy Computing",
        "MS-DOS 6.22 & 8086 Real-Mode Educational Simulator",
        "Deterministic 16-bit memory segmentation, FAT12 geometry, and COMMAND.COM shell coupled to Kloster A_τ(p).",
        C_SAGE, False, d, bullets, None, tmp_dir,
    )


def build_slide_04_r1_flight(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    d = data["r1"]["flight-sim"]
    bullets = [
        ("ISA Atmosphere & 6-DOF:", "Computes ISA air density ρ(h), lift/drag polar, stall-bounded AoA margin, and semi-implicit aerodynamic integration."),
        ("Six-Pack Telemetry HUD:", "Interactive Canvas artificial horizon, airspeed, altitude, VSI, turn coordinator, and heading indicator."),
        ("Sortie Phase Progression:", "16-episode flight profile from ground roll through climb, cruise, and flare (A_0.10: 5 → 7, EI = 0.1661 bits)."),
        ("Vector & Braille Plates:", "Exports flight_sim_plate.svg, flight_sim_chiasm.svg, and 2×4 Unicode Braille instrument strip."),
    ]
    _build_r1_standard_slide(
        prs, 4,
        "03 · R1 Domain 2 · Aerodynamics",
        "6-DOF Flight Dynamics & Telemetry HUD Simulator",
        "ISA atmospheric physics, bank-to-turn attitude dynamics, and six-pack cockpit telemetry under fieldglass-r1-summary/v1.",
        C_INDIGO, False, d, bullets, None, tmp_dir,
    )


def build_slide_05_r1_medical(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    d = data["r1"]["medical-sim"]
    bullets = [
        ("Synthetic Biomedical Signals:", "Educational Gaussian PQRST ECG trace, 660/940 nm Beer-Lambert SpO₂ curve, capnography plateau, and P-V compliance loop."),
        ("Dimensional Infusion Math:", "Classroom-only mL/hr rate and dose-unit sanity checker — zero patient data, zero hardware drivers."),
        ("Hard Non-Clinical Contract:", "JSON explicitly enforces clinical_use=False, educational_simulation_only=True, clinical_certification_claimed=False."),
        ("Steady-State Sandbox:", "16 simulated episodes maintain Past A_0.10 = 7 → Future A_0.10 = 7 (EI = 0.00224 bits, H1 = 2.9675 bits)."),
    ]
    _build_r1_standard_slide(
        prs, 5,
        "04 · R1 Domain 3 · Strictly Non-Clinical",
        "Simulated Medical Equipment Sandbox (Educational Only)",
        "Synthetic biomedical waveform and optics sandbox — strictly simulated/educational, making zero clinical or diagnostic claims.",
        C_RUBY, True, d, bullets,
        "STRICTLY SIMULATED / EDUCATIONAL SANDBOX ONLY — NOT FOR CLINICAL, DIAGNOSTIC, OR PATIENT-CARE USE",
        tmp_dir,
    )


def build_slide_06_r1_software(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    d = data["r1"]["software"]
    bullets = [
        ("6-Stage Observatory Pipeline:", "Maps frame_ingest -> deskew_geom -> bg_clean -> kloster_atp -> svg_braille -> chiasm_seal directly to src/fieldglass/."),
        ("Strict Superlevel-Set Calculator:", "Live interactive p(x) > τ explorer verifying Kloster A_τ(p) threshold behavior without approximation."),
        ("Pure-JS SHA-256 Verifier:", "Browser-side digest inspection matching chiasm_report.json cryptographic seals with zero network calls."),
        ("Peak M1 Effective Information:", "Highest M1 EI at 0.4748 bits across 12 episodes (A_0.10: 5 → 5, H1 = 2.8109), plus 6-layer Win7/ES5 matrix."),
    ]
    _build_r1_standard_slide(
        prs, 6,
        "05 · R1 Domain 4 · Systems Engineering",
        "Software Systems & Fieldglass Observatory Workbench",
        "Self-documenting software observatory detailing Fieldglass internals, strict A_τ(p), and Windows 7-to-modern compatibility.",
        C_COPPER, False, d, bullets, None, tmp_dir,
    )


def build_slide_07_r2_hub(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_PARCHMENT)
    add_header_footer(
        slide, 7,
        "06 · R2 Architecture Hub · Five Engineering Dossiers",
        "Structured Improvements Across Five AI, Aerospace & Creative Subjects",
        "25 concrete proposals (5 per subject) in docs/improvements/, each grounded with 24-episode Chiasms, SVGs, and 2×4 Braille.",
        dark=False, accent=C_INDIGO,
    )

    # Top-left: Hub preview image
    hub_p = sanitize_png(data["r2_hub_preview"], tmp_dir, tag="r2_hub")
    add_picture_contain(slide, hub_p, 0.55, 1.32, 6.20, 3.82, frame_fill=C_CARD, frame_line=C_BORDER, pad=0.06, rounded=True)
    add_textbox(slide, 0.55, 5.18, 6.20, 0.24, "docs/improvements/preview.png  ·  Zero-CDN Static Observatory Hub", FONT_MONO, 7.6, True, color=C_INDIGO, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0))

    # Bottom-left: Hub summary & invariants card
    add_rect(slide, 0.55, 5.48, 6.20, 1.46, fill=C_SLATE_BG, line=C_GOLD, line_pt=0.85, rounded=True, radius=0.05)
    add_textbox(slide, 0.74, 5.58, 5.82, 0.24, "R2 DOSSIER ARCHITECTURE & SCHEMA (fieldglass-r2-improvements/v1)", FONT_MONO, 7.8, True, color=C_GOLD, margin=(0, 0, 0, 0))
    add_bullets(
        slide, 0.74, 5.86, 5.82, 1.00,
        [
            ("10 Artifacts Per Subject:", "index.html, preview.png, braille_preview.png, architecture.svg, chiasm.svg, braille.txt/.json, data/summary/chiasm JSONs."),
            ("Dedicated Deep-Dives Next:", "Slides 08–12 inspect each of ChatGPT, Anthropic, Grok, SpaceX, and Claire (aka Grimes) individually."),
        ],
        font_size=8.8, lead_color=C_GOLD, body_color=C_LIGHT_MUT, space_after_pt=3.5,
    )

    # Right: 5-subject structured table/cards
    rx = 6.95
    rw = 5.83
    subjects = [data["r2_subjects"][slug] for slug in R2_SLUGS]
    accents = [C_INDIGO, C_COPPER, C_RUBY, C_SAGE, C_VIOLET]
    card_h = 1.04
    gap = 0.115
    for idx, (sdata, acc) in enumerate(zip(subjects, accents)):
        y = 1.32 + idx * (card_h + gap)
        s = sdata["summary"]
        m = s["metrics"]
        ch = sdata["chiasm"]
        add_rect(slide, rx, y, rw, card_h, fill=C_CARD, line=C_BORDER, line_pt=0.8, rounded=True, radius=0.05)
        add_rect(slide, rx, y, 0.08, card_h, fill=acc, line=None)
        add_badge(slide, rx + 0.18, y + 0.12, 1.50, 0.24, s["display_name"].upper(), acc, C_LIGHT_INK, 7.5)
        add_textbox(
            slide, rx + 1.78, y + 0.11, rw - 1.92, 0.25,
            f"{s['category']}  ·  Slide {8 + idx:02d}",
            FONT_MONO, 7.6, True, color=acc, align=PP_ALIGN.RIGHT, margin=(0, 0, 0, 0),
        )
        add_textbox(
            slide, rx + 0.18, y + 0.41, rw - 0.34, 0.28,
            s["tagline"],
            FONT_SANS, 9.0, True, color=C_INK, margin=(0, 0, 0, 0),
        )
        add_textbox(
            slide, rx + 0.18, y + 0.72, rw - 0.34, 0.24,
            f"5 proposals  ·  24 ep  ·  A_0.10: {m['past_a_tau']}→{m['future_a_tau']}  ·  "
            f"EI={m['effective_information_bits']:.4f} bits  ·  H1={ch['h1_mean_bits']:.4f}  ·  {m['presence_glyph']}",
            FONT_MONO, 7.3, False, color=C_MUTED, margin=(0, 0, 0, 0),
        )


def _build_r2_subject_slide(
    prs: Presentation,
    slide_num: int,
    eyebrow: str,
    sdata: Dict[str, Any],
    accent: RGBColor,
    dark: bool,
    tmp_dir: pathlib.Path,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_SLATE_BG if dark else C_PARCHMENT)

    s = sdata["summary"]
    m = s["metrics"]
    ch = sdata["chiasm"]
    slug = s["slug"]

    add_header_footer(
        slide, slide_num,
        eyebrow,
        f"{s['display_name']} — Structured Improvement Dossier ({s['category']})",
        s["tagline"],
        dark=dark, accent=accent,
    )

    card_bg = C_SLATE_CRD if dark else C_CARD
    card_bdr = C_SLATE_BDR if dark else C_BORDER
    ink = C_LIGHT_INK if dark else C_INK
    mut = C_LIGHT_MUT if dark else C_MUTED

    # Left column: preview.png + braille preview + telemetry strip
    preview_p = sanitize_png(sdata["preview"], tmp_dir, tag=f"r2_{slug}")
    braille_p = sanitize_png(sdata["braille_preview"], tmp_dir, tag=f"r2b_{slug}")

    add_picture_contain(slide, preview_p, 0.55, 1.30, 5.48, 3.74, frame_fill=card_bg, frame_line=accent if dark else card_bdr, pad=0.05, rounded=True)

    add_rect(slide, 0.55, 5.14, 5.48, 1.82, fill=card_bg, line=card_bdr, line_pt=0.8, rounded=True, radius=0.04)
    add_picture_contain(slide, braille_p, 0.65, 5.22, 2.08, 1.66, frame_fill=C_CARD, frame_line=card_bdr, pad=0.03, rounded=False)

    add_textbox(slide, 2.84, 5.24, 3.08, 0.24, "2×4 BRAILLE & CHIASM SEAL", FONT_MONO, 7.8, True, color=accent, margin=(0, 0, 0, 0))
    add_textbox(
        slide, 2.84, 5.52, 3.08, 1.34,
        f"Episodes: {m['episodes']} (nexus @ {ch['nexus_sec']}s)\n"
        f"Past→Future A_0.10: {m['past_a_tau']} → {m['future_a_tau']} ({m['presence_glyph']})\n"
        f"EI = {m['effective_information_bits']:.6f} bits\n"
        f"H1 = {ch['h1_mean_bits']:.4f}  ·  M4 = {ch['m4_purity_mean']:.4f}\n"
        f"Invariants: {', '.join(m['structural_invariants'])}\n"
        f"docs/improvements/{slug}/",
        FONT_MONO, 7.3, False, color=ink, line_spacing=1.26, margin=(0, 0, 0, 0),
    )

    # Right column: 5 structured proposal cards with exact IDs & KPIs
    rx = 6.22
    rw = 6.56
    item_h = 1.04
    gap = 0.115
    for idx, (imp, kpi) in enumerate(zip(s["top_improvements"], s["kpis"])):
        y = 1.30 + idx * (item_h + gap)
        add_rect(slide, rx, y, rw, item_h, fill=card_bg, line=card_bdr, line_pt=0.8, rounded=True, radius=0.04)
        add_rect(slide, rx, y, 0.08, item_h, fill=accent, line=None)
        add_badge(slide, rx + 0.18, y + 0.10, 1.18, 0.23, imp["id"], accent, C_SLATE_BG if dark and accent in (C_CYAN, C_GOLD) else C_LIGHT_INK, 7.5)
        add_textbox(
            slide, rx + 1.44, y + 0.07, rw - 1.58, 0.36,
            imp["title"],
            FONT_SANS, 8.7, True, color=ink, line_spacing=1.08, margin=(0, 0, 0, 0),
        )
        add_textbox(
            slide, rx + 0.18, y + 0.48, rw - 0.34, 0.23,
            f"KPI Metric: {kpi['metric']}",
            FONT_SANS, 8.4, False, color=mut, margin=(0, 0, 0, 0),
        )
        add_textbox(
            slide, rx + 0.18, y + 0.73, rw - 0.34, 0.24,
            f"Baseline: {kpi['baseline']}   →   Target: {kpi['target']}",
            FONT_MONO, 7.9, True, color=accent, margin=(0, 0, 0, 0),
        )


def build_slide_08_r2_chatgpt(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    _build_r2_subject_slide(prs, 8, "07 · R2 Subject 1 · Frontier AI", data["r2_subjects"]["chatgpt"], C_CYAN, True, tmp_dir)


def build_slide_09_r2_anthropic(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    _build_r2_subject_slide(prs, 9, "08 · R2 Subject 2 · Constitutional & Coding AI", data["r2_subjects"]["anthropic"], C_COPPER, False, tmp_dir)


def build_slide_10_r2_grok(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    _build_r2_subject_slide(prs, 10, "09 · R2 Subject 3 · Real-Time & Social", data["r2_subjects"]["grok"], C_RUBY, True, tmp_dir)


def build_slide_11_r2_spacex(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    _build_r2_subject_slide(prs, 11, "10 · R2 Subject 4 · Aerospace & Telemetry", data["r2_subjects"]["spacex"], C_INDIGO, False, tmp_dir)


def build_slide_12_r2_grimes(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    _build_r2_subject_slide(prs, 12, "11 · R2 Subject 5 · Creative & Audio", data["r2_subjects"]["claire-grimes"], C_VIOLET, True, tmp_dir)


def build_slide_13_r2_synthesis(prs: Presentation, chart_b: pathlib.Path) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_PARCHMENT)
    add_header_footer(
        slide, 13,
        "12 · R2 Impact Synthesis",
        "Measurable Baseline-to-Target Uplift Across All 25 R2 Proposals",
        "Every subject dossier couples quantitative target reductions/gains with zero-token cryptographic provenance and 2×4 Braille.",
        dark=False, accent=C_SAGE,
    )

    add_picture_contain(slide, chart_b, 0.55, 1.30, 12.23, 3.82, frame_fill=C_CARD, frame_line=C_BORDER, pad=0.05, rounded=True)

    pillars = [
        ("CRYPTOGRAPHIC PROVENANCE", C_INDIGO,
         "CanvasProof-v1 Merkle DAGs (ChatGPT), Span-Hash anchoring (Anthropic), ClaimLedger (Grok), SHA-256 HIL frames (SpaceX), and Elf.Tech 50/50 voice stems (Claire/Grimes)."),
        ("DETERMINISTIC GUARDRAILS", C_RUBY,
         "Kloster A_τ(p) stem routing (-38% wasted tokens), capability-scoped MCP dry-run gates (0% OOS writes), dual-cone rumor suppression, and bar-quantized stage failover (<0.3%)."),
        ("TACTILE 2×4 BRAILLE ACCESS", C_SAGE,
         "Every R1 simulator and R2 dossier exports 72-column 2×4 Unicode Braille transcripts, trajectory plates, and cymatic scores (up to 93% offline accessibility)."),
    ]
    pw = 3.92
    pg = 0.235
    for i, (hdr, acc, body) in enumerate(pillars):
        x = 0.55 + i * (pw + pg)
        add_rect(slide, x, 5.26, pw, 1.70, fill=C_CARD, line=C_BORDER, line_pt=0.8, rounded=True, radius=0.05)
        add_rect(slide, x, 5.26, pw, 0.07, fill=acc, line=None)
        add_textbox(slide, x + 0.16, 5.42, pw - 0.32, 0.26, hdr, FONT_MONO, 8.2, True, color=acc, margin=(0, 0, 0, 0))
        add_textbox(slide, x + 0.16, 5.72, pw - 0.32, 1.14, body, FONT_SANS, 9.1, False, color=C_INK, line_spacing=1.22, margin=(0, 0, 0, 0))


def build_slide_14_r3_win7_arch(prs: Presentation, data: Dict[str, Any], tmp_dir: pathlib.Path) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_SLATE_BG)
    add_header_footer(
        slide, 14,
        "13 · R3 Zoe Hospital Edition · Windows 7 SP1 Architecture",
        "Zoe Hospital Edition: Windows 7-Era Compatibility & Non-Clinical Contract",
        "Air-gapped ES5/HTA kiosk & Python 3.7/3.8+ stdlib loopback server engineered for Windows 7 SP1 (NT 6.1) legacy workstations.",
        dark=True, accent=C_RUBY,
    )

    add_non_clinical_banner(
        slide, 0.55, 1.30, 12.23,
        "STRICTLY SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL, DIAGNOSTIC, OR PATIENT-CARE USE — NO CLINICAL CERTIFICATION CLAIMED",
        dark=True,
    )

    r3_prev = sanitize_png(data["r3"]["preview"], tmp_dir, tag="r3_prev")
    add_picture_contain(slide, r3_prev, 0.55, 1.76, 6.25, 3.82, frame_fill=C_SLATE_CRD, frame_line=C_GOLD, pad=0.05, rounded=True)
    add_textbox(
        slide, 0.55, 5.64, 6.25, 0.24,
        "docs/zoe-hospital/preview.png (1280×720) · IE8–IE11 / mshta.exe Safe Layout",
        FONT_MONO, 7.6, True, color=C_GOLD, align=PP_ALIGN.CENTER, margin=(0, 0, 0, 0),
    )

    # Bottom-left contract box
    zm = data["r3"]["summary"]
    add_rect(slide, 0.55, 5.94, 6.25, 1.02, fill=C_SLATE_CRD, line=C_RUBY, line_pt=0.85, rounded=True, radius=0.04)
    add_textbox(
        slide, 0.72, 6.02, 5.90, 0.86,
        f"Min OS: {zm['min_windows_version']}  ·  Package: zoe-hospital-win7-edition v1.0.0\n"
        f"clinical_use={zm['clinical_use']}  ·  educational_simulation_only={zm['educational_simulation_only']}  ·  "
        f"clinical_certification_claimed={zm['clinical_certification_claimed']}\n"
        f"executed={zm['executed']}  ·  sentience_claimed={zm['sentience_claimed']}  ·  tokens_used={zm['tokens_used']}",
        FONT_MONO, 7.4, False, color=C_LIGHT_INK, line_spacing=1.28, margin=(0, 0, 0, 0),
    )

    # Right: 4-tier Win7 compatibility stack
    layers = [
        ("01", "zoe_hospital_kiosk.html & .hta (mshta.exe)", C_GOLD,
         "Strict ES5-only JavaScript (var / function(), zero let/const/arrow/fetch/promises), explicit hex colors & IE8-safe layout, zero external CDNs."),
        ("02", "zoe_hospital_win7.py (Python 3.7 / 3.8+ Stdlib)", C_CYAN,
         "Zero third-party imports, Python 3.7+ AST compatible, binds 127.0.0.1 loopback HTTP/1.1 only, zero raw ANSI escapes for clean Win7 cmd.exe."),
        ("03", "launch_win7.bat & README_WIN7.txt", C_TEAL,
         "One-click Windows 7 SP1 batch launcher probing python/py -3 or falling back cleanly to mshta.exe zoe_hospital_kiosk.hta."),
        ("04", "zoe_hospital_win7_bundle.zip (134.8 KB)", C_RUBY,
         f"Portable air-gapped archive packing all {len(data['r3']['manifest']['files'])} SHA-256 verified files with manifest.json & chiasm_report.json."),
    ]
    rx = 7.00
    rw = 5.78
    lh = 1.21
    lg = 0.12
    for i, (num, hdr, acc, desc) in enumerate(layers):
        y = 1.76 + i * (lh + lg)
        add_rect(slide, rx, y, rw, lh, fill=C_SLATE_CRD, line=C_SLATE_BDR, line_pt=0.8, rounded=True, radius=0.05)
        add_rect(slide, rx, y, 0.08, lh, fill=acc, line=None)
        add_badge(slide, rx + 0.18, y + 0.14, 0.44, 0.24, num, acc, C_SLATE_BG, 8.0)
        add_textbox(slide, rx + 0.70, y + 0.12, rw - 0.86, 0.28, hdr, FONT_SERIF, 12.0, True, color=C_LIGHT_INK, margin=(0, 0, 0, 0))
        add_textbox(slide, rx + 0.18, y + 0.46, rw - 0.34, 0.66, desc, FONT_SANS, 8.8, False, color=C_LIGHT_MUT, line_spacing=1.22, margin=(0, 0, 0, 0))


def build_slide_15_r3_features_seal(prs: Presentation, data: Dict[str, Any]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_PARCHMENT)
    add_header_footer(
        slide, 15,
        "14 · R3 Zoe Hospital Edition · Offline Sandbox & Telemetry",
        "Offline Hospital Sandbox Modules & SHA-256 Causal Chiasm Seal",
        "Four self-contained educational modules running offline on Windows 7 SP1 without cloud APIs or clinical claims.",
        dark=False, accent=C_SAGE,
    )

    zs = data["r3"]["summary"]
    zm = zs["metrics"]
    man = data["r3"]["manifest"]

    cards = [
        ("MODULE 01 · COMMUNICATION", "Simulated Hospital Communication Board", C_INDIGO, [
            ("Low-Stress Prompts:", "Pre-built non-clinical comfort, lighting, hydration, and orientation phrases for classroom & demo walkthroughs."),
            ("Zero Network State:", "Runs purely in ES5 DOM state inside IE8–IE11, mshta.exe, or local loopback HTTP/1.1."),
        ]),
        ("MODULE 02 · ACCESSIBILITY", "2×4 Unicode Braille Converter", C_COPPER, [
            ("Deterministic Packing:", "Converts any educational phrase or ward orientation cue into crisp 2×4 Unicode Braille cells locally."),
            ("Legacy Font Safe:", "Renders clean monospace patterns without requiring modern browser APIs or external font CDNs."),
        ]),
        ("MODULE 03 · TELEMETRY", "Kloster A_τ(p) Ward-Calm Simulator", C_SAGE, [
            ("16-Episode Chiasm:", f"Past A_0.10 = {zm['past_accessible_volume']} → Future A_0.10 = {zm['future_accessible_volume']} (shift {zm['chiasm_shift']}, glyph {zm['presence_glyph']})."),
            ("Entropy & Purity:", f"EI = {zm['effective_information_bits']:.6f} bits · H1 = {zm['mean_h1_bits']:.4f} · M4 = {zm['mean_m4_purity']:.5f} · Invariants: {', '.join(zm['structural_invariants'])}."),
        ]),
        ("MODULE 04 · INTEGRITY", "Training Checklist & SHA-256 Manifest", C_RUBY, [
            ("10-File Sealed Manifest:", f"manifest.json records exact byte counts and SHA-256 digests for all {len(man['files'])} runtime artifacts."),
            ("Non-Clinical Gate:", "Every training checklist item reinforces educational-only boundaries (clinical_certification_claimed=False)."),
        ]),
    ]

    cw = 5.98
    ch = 2.26
    gx = 0.27
    gy = 0.16
    for idx, (tag, title, acc, bullets) in enumerate(cards):
        r, c = divmod(idx, 2)
        x = 0.55 + c * (cw + gx)
        y = 1.32 + r * (ch + gy)
        add_rect(slide, x, y, cw, ch, fill=C_CARD, line=C_BORDER, line_pt=0.85, rounded=True, radius=0.05)
        add_rect(slide, x, y, cw, 0.07, fill=acc, line=None)
        add_textbox(slide, x + 0.18, y + 0.15, cw - 0.36, 0.22, tag, FONT_MONO, 8.0, True, color=acc, margin=(0, 0, 0, 0))
        add_textbox(slide, x + 0.18, y + 0.38, cw - 0.36, 0.30, title, FONT_SERIF, 13.5, True, color=C_INK, margin=(0, 0, 0, 0))
        add_rect(slide, x + 0.18, y + 0.72, cw - 0.36, 0.012, fill=C_BORDER, line=None)
        add_bullets(slide, x + 0.18, y + 0.82, cw - 0.36, ch - 0.90, bullets, font_size=9.1, lead_color=acc, body_color=C_INK, space_after_pt=4.5)

    add_rect(slide, 0.55, 6.22, 12.23, 0.68, fill=C_SLATE_BG, line=C_GOLD, line_pt=0.85, rounded=True, radius=0.05)
    add_textbox(
        slide, 0.74, 6.28, 11.85, 0.56,
        f"Zoe Hospital Chiasm Report SHA-256: {zs['report_sha256']}  ·  "
        f"Disclaimer: {zs['disclaimer']}",
        FONT_MONO, 7.8, False, color=C_LIGHT_INK, valign=MSO_ANCHOR.MIDDLE, margin=(0, 0, 0, 0),
    )


def build_slide_16_r4_r5_summary(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_SLATE_BG)
    add_rect(slide, 0, 0, 13.333, 0.08, fill=C_GOLD, line=None)
    add_rect(slide, 0.42, 0.34, 12.49, 6.82, fill=None, line=C_SLATE_BDR, line_pt=1.0)

    add_badge(slide, 0.78, 0.60, 4.75, 0.30, "15 · R4/R5 INTEGRATION, HYGIENE & VERIFICATION", C_SLATE_CRD, C_GOLD, 8.0, border=C_GOLD)
    add_textbox(
        slide, 0.78, 1.02, 11.77, 0.54,
        "Observatory R1–R4 Complete · Verified Within All R5 Constraints",
        FONT_SERIF, 25.0, True, color=C_LIGHT_INK, margin=(0, 0, 0, 0),
    )
    add_textbox(
        slide, 0.78, 1.56, 11.77, 0.36,
        "Dual byte-identical 16:9 .pptx deliverables, docs/index.html pure HTML/CSS wiring, README.md documentation, and automated pytest verification.",
        FONT_SANS, 11.0, False, color=C_LIGHT_MUT, margin=(0, 0, 0, 0),
    )

    cols = [
        ("DELIVERABLE OUTPUTS (R4)", C_GOLD, [
            ("Dual .pptx Decks:", "docs/Fieldglass_Observatory_Expansion.pptx and /home/cowboy/fieldglass/Fieldglass_Observatory_Expansion.pptx (byte-identical SHA-256)."),
            ("Observatory Wiring:", "docs/index.html preserves all 29 specimens (#specimen-1..#specimen-29) and wires R1–R4 cards with zero <script> tags."),
            ("Documentation:", "README.md documents R1–R4, Win7 Zoe Hospital non-clinical edition, /usr/bin/python3 commands, and R5 gates."),
        ]),
        ("MEDIA & RUNTIME GATES (R5)", C_CYAN, [
            ("Runtime Discipline:", "Standalone /usr/bin/python3 execution via conditional sys.path fallback and TemporaryDirectory() (no /tmp cache)."),
            ("Zero GPS Metadata:", "All embedded ppt/media/* and docs/ media assets sanitized (-map_metadata -1 / empty PngInfo) with 0 GPS tags."),
            ("Strict < 50 MB Budget:", "Every file in docs/ including the .pptx deck remains strictly under 50 MB (52,428,800 bytes)."),
        ]),
        ("REPOSITORY BOUNDARIES (R5)", C_RUBY, [
            ("Clean Git Discipline:", "Never run git add -A; pre-existing untracked artifacts remain untouched and isolated."),
            ("Hard Monorepo Boundary:", "External local zoe-monorepo checkout is never touched or modified."),
            ("Remote Policy:", "Any update to Nicholas-Michael-Kloster/Zoe README.md uses only the GitHub Git Data API."),
        ]),
    ]
    cw = 3.76
    cg = 0.245
    for i, (hdr, acc, bullets) in enumerate(cols):
        x = 0.78 + i * (cw + cg)
        add_rect(slide, x, 2.10, cw, 3.64, fill=C_SLATE_CRD, line=C_SLATE_BDR, line_pt=0.85, rounded=True, radius=0.05)
        add_rect(slide, x, 2.10, cw, 0.07, fill=acc, line=None)
        add_textbox(slide, x + 0.16, 2.26, cw - 0.32, 0.26, hdr, FONT_MONO, 8.2, True, color=acc, margin=(0, 0, 0, 0))
        add_rect(slide, x + 0.16, 2.56, cw - 0.32, 0.012, fill=C_SLATE_BDR, line=None)
        add_bullets(slide, x + 0.16, 2.68, cw - 0.32, 2.94, bullets, font_size=9.0, lead_color=acc, body_color=C_LIGHT_INK, space_after_pt=6.0)

    add_non_clinical_banner(
        slide, 0.78, 5.94, 11.77,
        "SIMULATED / EDUCATIONAL ONLY — medical-sim & zoe-hospital claim ZERO clinical, diagnostic, or patient-care certification.",
        dark=True,
    )

    add_textbox(
        slide, 0.78, 6.46, 10.2, 0.36,
        "Fieldglass Observatory  ·  Nicholas Michael Kloster  ·  executed=False  ·  sentience_claimed=False  ·  tokens_used=0",
        FONT_MONO, 8.1, False, color=C_LIGHT_MUT, valign=MSO_ANCHOR.MIDDLE, margin=(0, 0, 0, 0),
    )
    add_textbox(
        slide, 11.2, 6.46, 1.35, 0.36,
        f"{TOTAL_SLIDES:02d} / {TOTAL_SLIDES:02d}",
        FONT_MONO, 8.6, True, color=C_GOLD, align=PP_ALIGN.RIGHT, valign=MSO_ANCHOR.MIDDLE, margin=(0, 0, 0, 0),
    )


def build_deck() -> Tuple[pathlib.Path, pathlib.Path, str, int]:
    data = load_observatory_data()

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = pathlib.Path(tmp_str)
        chart_a = build_chart_a_telemetry(data["rows"], tmp_dir)
        chart_b = build_chart_b_r2_uplift(tmp_dir)

        build_slide_01_cover(prs, data, tmp_dir)
        build_slide_02_telemetry_overview(prs, data, chart_a)
        build_slide_03_r1_msdos(prs, data, tmp_dir)
        build_slide_04_r1_flight(prs, data, tmp_dir)
        build_slide_05_r1_medical(prs, data, tmp_dir)
        build_slide_06_r1_software(prs, data, tmp_dir)
        build_slide_07_r2_hub(prs, data, tmp_dir)
        build_slide_08_r2_chatgpt(prs, data, tmp_dir)
        build_slide_09_r2_anthropic(prs, data, tmp_dir)
        build_slide_10_r2_grok(prs, data, tmp_dir)
        build_slide_11_r2_spacex(prs, data, tmp_dir)
        build_slide_12_r2_grimes(prs, data, tmp_dir)
        build_slide_13_r2_synthesis(prs, chart_b)
        build_slide_14_r3_win7_arch(prs, data, tmp_dir)
        build_slide_15_r3_features_seal(prs, data)
        build_slide_16_r4_r5_summary(prs)

        assert len(prs.slides) == TOTAL_SLIDES, f"Expected {TOTAL_SLIDES} slides, got {len(prs.slides)}"

        OUT_DOCS_PPTX.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(OUT_DOCS_PPTX))

    size_bytes = OUT_DOCS_PPTX.stat().st_size
    assert 0 < size_bytes < MAX_FILE_BYTES, f"PPTX size {size_bytes} violates < 50 MB limit"
    shutil.copyfile(OUT_DOCS_PPTX, OUT_ROOT_PPTX)

    sha_docs = hashlib.sha256(OUT_DOCS_PPTX.read_bytes()).hexdigest()
    sha_root = hashlib.sha256(OUT_ROOT_PPTX.read_bytes()).hexdigest()
    assert sha_docs == sha_root, "Dual .pptx SHA-256 mismatch"
    return OUT_DOCS_PPTX, OUT_ROOT_PPTX, sha_docs, size_bytes


def main() -> None:
    docs_p, root_p, digest, size_bytes = build_deck()
    print(f"Built {TOTAL_SLIDES} slides -> {docs_p} & {root_p} ({size_bytes:,} bytes, sha256={digest})")


if __name__ == "__main__":
    main()
