#!/usr/bin/env python3
"""Fieldglass Specimen #2 — Field Notebook, Birds on a Wire & Blanche Ames's Fig. 57 Stelis leucopogon.

Processes `/home/cowboy/Screencasts/Screencast From 2026-11-25 12-59-30.mp4` (13.09 min):
  1. Extracts 6 sharpest clean camera-viewport frames (zero UI chrome overlap on hero art)
  2. Builds archival ink prints, framed two-tone vector SVGs, and 2x4 Unicode Braille specimens
     for BOTH Fig. 57 Stelis leucopogon (Blanche Ames) AND Nick's original "Birds on a Wire" sketch
  3. Runs full 13-minute (196-episode) GEM Causal Chiasm & Persistent Filtration Tomography
  4. Renders a smooth 48-second 1280x720 Kloster A_tau(p_t) telemetry highlight reel
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_GUIAI = Path("/media/cowboy/research/zoe-monorepo/guiai-lab")
if str(REPO_GUIAI) not in sys.path:
    sys.path.insert(0, str(REPO_GUIAI))

from fieldglass.plate import clean_illumination, ink_to_braille_lines, render_braille_preview_png, save_braille_bundle
from guiai.gem.chiasm import (
    CONTRACT as CHIASM_CONTRACT,
    _line,
    _polyline,
    _rectangle,
    _text,
    causal_chiasm,
    hud_stamp_objects,
    persistent_filtration_tomography,
)
from guiai.gem.model import Scene
from guiai.gem.qualia import BACKGROUND, CYAN, GOLD, MUTED, PANEL, RED, TEXT
from guiai.gem.render import write_svg
from guiai.gem.visual_language import woven_diamond

SRC = Path("/home/cowboy/Screencasts/Screencast From 2026-11-25 12-59-30.mp4")
OUT = Path("/home/cowboy/fieldglass_specimen2")
PLATES_DIR = OUT / "plates"
ASSETS_DIR = OUT / "assets"
CHIASM_DIR = OUT / "chiasm"
VIDEO_DIR = OUT / "video"

# Exact Pixel 7 camera viewport inside 1920x1080 scrcpy (x: 743..1177 = 434px wide)
# Clean upper canvas y=185..655 (470px tall) sits completely ABOVE the .7/1x/2 zoom pill & red stop button!
VP_X, VP_W = 743, 434
CLEAN_Y, CLEAN_H = 185, 470  # completely UI-free band!

TONAL_STATES = (
    "deep_shadow",
    "ink_linework",
    "dark_midtone",
    "botanical_mid",
    "warm_sepia",
    "aged_paper",
    "bright_cream",
    "paper_highlight",
)


def _load_font(size: int, bold: bool = False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    return ImageFont.truetype(p, size) if Path(p).is_file() else ImageFont.load_default()


def a_tau(p: np.ndarray, tau: float) -> int:
    return int(np.sum(p > tau))


def shannon_h1(p: np.ndarray) -> float:
    nz = p[p > 0]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def renyi_h2(p: np.ndarray) -> float:
    return float(-math.log2(max(float(np.sum(p * p)), 1e-12)))


def quartic_m4(p: np.ndarray) -> float:
    return float(np.sum(p ** 4) ** 0.25)


def normalize_dist(d: dict[str, float]) -> dict[str, float]:
    clean = {k: max(float(v), 1e-9) for k, v in d.items()}
    total = sum(clean.values())
    norm = {k: v / total for k, v in clean.items()}
    max_k = max(norm, key=lambda k: norm[k])
    norm[max_k] = 1.0 - sum(v for k, v in norm.items() if k != max_k)
    return norm


def lum_to_8state(p256: np.ndarray) -> dict[str, float]:
    return normalize_dist({
        name: float(p256[i * 32 : (i + 1) * 32].sum())
        for i, name in enumerate(TONAL_STATES)
    })


def sharp_score(im: Image.Image) -> float:
    return float(ndimage.laplace(np.asarray(im.convert("L"), dtype=np.float32)).var())


def extract_clean_plates() -> dict[str, Path]:
    PLATES_DIR.mkdir(parents=True, exist_ok=True)
    # Windows chosen from storyboard; cropped cleanly to UI-free upper viewfinder band (434x470)
    # except where full viewport (y=170..655) is ideal!
    windows = [
        ("01_birds_on_a_wire", "Nick · Birds on a Wire Sketch", 204.0, 6.0, (758, 225, 1145, 645)),
        ("02_bridal_wreath_woodcut", "Vintage Woodcut · Bridal Wreath Falls", 292.0, 5.0, (748, 200, 1168, 650)),
        ("03_orchid_multistem", "Ames & Correll · Multi-Stem Orchid", 358.0, 5.0, (748, 195, 1170, 655)),
        ("04_fig57_stelis_leucopogon", "Fig. 57 · Stelis leucopogon (Blanche Ames, p. 177)", 496.5, 4.0, (748, 195, 1172, 652)),
        ("05_fig54_stelis_guatemalensis", "Fig. 54 · Stelis guatemalensis (Blanche Ames)", 558.5, 5.0, (748, 198, 1170, 650)),
        ("06_live_pen_smiles", "Nick · Live Pen-and-Ink Smiles", 658.0, 5.0, (755, 220, 1165, 650)),
    ]
    out_map: dict[str, Path] = {}
    thumbs: list[tuple[str, float, Path]] = []

    with tempfile.TemporaryDirectory() as tmp:
        for slug, label, start, dur, (cx0, cy0, cx1, cy1) in windows:
            cw, ch = cx1 - cx0, cy1 - cy0
            cdir = Path(tmp) / slug
            cdir.mkdir()
            subprocess.run([
                "ffmpeg", "-v", "error", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
                "-i", str(SRC), "-vf", f"fps=4,crop={cw}:{ch}:{cx0}:{cy0}", "-q:v", "2",
                str(cdir / "f_%03d.jpg"),
            ], check=True)
            cands = sorted(cdir.glob("f_*.jpg"))
            best = max(cands, key=lambda p: sharp_score(Image.open(p)))
            best_ts = start + cands.index(best) / 4.0
            out_png = PLATES_DIR / f"{slug}.png"
            subprocess.run([
                "ffmpeg", "-v", "error", "-ss", f"{best_ts:.2f}", "-i", str(SRC),
                "-frames:v", "1", "-vf", f"crop={cw}:{ch}:{cx0}:{cy0}", "-y", str(out_png),
            ], check=True)
            out_map[slug] = out_png
            thumbs.append((label, best_ts, out_png))
            print(f"OK {slug}: t={best_ts:.2f}s size={Image.open(out_png).size}")

    # Build clean 3x2 contact sheet (zero UI chrome!)
    tw, th = 440, 490
    sheet = Image.new("RGB", (3 * tw, 2 * th), (12, 15, 22))
    sd = ImageDraw.Draw(sheet)
    f_lbl = _load_font(12, bold=True)
    for idx, (label, ts, pp) in enumerate(thumbs):
        im = Image.open(pp).convert("RGB")
        im.thumbnail((tw - 16, th - 36))
        r, c = divmod(idx, 3)
        ox = c * tw + (tw - im.width) // 2
        oy = r * th + 28 + (th - 36 - im.height) // 2
        sheet.paste(im, (ox, oy))
        mm, ss = divmod(int(ts), 60)
        sd.text((c * tw + 10, r * th + 8), f"{mm:02d}:{ss:02d} · {label[:38]}", fill=(242, 196, 92), font=f_lbl)
    sheet.save(PLATES_DIR / "contact_sheet_specimen2.jpg", quality=92)
    return out_map


def make_hero_specimen_assets(
    src_png: Path,
    stem: str,
    *,
    title: str,
    subtitle: str,
    art_box_frac: tuple[float, float, float, float],
    paper_cutoff: float = 0.915,
    ink_floor: float = 0.38,
    gamma: float = 1.25,
    svg_levels: tuple[float, float, float] = (0.10, 0.26, 1.2),
    braille_cols: int = 68,
) -> dict[str, str]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    im = Image.open(src_png).convert("RGB")
    # Upscale 3x with bicubic before illumination division so contours & stippling trace silky smooth!
    up = im.resize((im.width * 3, im.height * 3), Image.Resampling.BICUBIC)
    ink, archival, bw = clean_illumination(up, sigma=48.0, paper_cutoff=paper_cutoff, ink_floor=ink_floor, gamma=gamma)

    arch_path = ASSETS_DIR / f"{stem}_archival_print.png"
    bw_path = ASSETS_DIR / f"{stem}_ink_bw.png"
    archival.save(arch_path)
    bw.save(bw_path)

    # Isolate pure artwork region for SVG & Braille
    ph, pw = ink.shape
    fx0, fy0, fx1, fy1 = art_box_frac
    art_ink = ink[int(ph * fy0):int(ph * fy1), int(pw * fx0):int(pw * fx1)].copy()
    mask = art_ink > 0.14
    labeled, n_comp = ndimage.label(mask)
    if n_comp > 0:
        sizes = ndimage.sum(mask, labeled, range(1, n_comp + 1))
        cleaned = np.where((sizes >= 6)[labeled - 1] & mask, art_ink, 0.0)
    else:
        cleaned = art_ink

    # Trace framed two-tone archival SVG
    ah, aw = cleaned.shape
    vec_w = 640
    vec_h = max(32, int(round(ah * (vec_w / max(1, aw)))))
    small = np.asarray(
        Image.fromarray((cleaned * 255.0).clip(0, 255).astype(np.uint8)).resize((vec_w, vec_h), Image.Resampling.BOX),
        dtype=np.float32,
    ) / 255.0
    smooth = ndimage.gaussian_filter(small, sigma=0.6)

    svg_path = ASSETS_DIR / f"{stem}.svg"
    fig_h = max(7.5, min(11.0, 8.0 * (vec_h / vec_w) + 1.4))
    fig = plt.figure(figsize=(8.0, fig_h), dpi=100, facecolor="#f6f1e4")
    ax = fig.add_axes([0.06, 0.13, 0.88, 0.81], facecolor="#f6f1e4")
    ax.contourf(smooth, levels=list(svg_levels), colors=["#786f5f", "#1b1916"])
    ax.set_xlim(0, vec_w - 1)
    ax.set_ylim(vec_h - 1, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patches.append(plt.Rectangle((0.028, 0.024), 0.944, 0.952, fill=False, edgecolor="#8c7f68", linewidth=1.2, transform=fig.transFigure))
    fig.patches.append(plt.Rectangle((0.036, 0.032), 0.928, 0.936, fill=False, edgecolor="#c4b89f", linewidth=0.6, transform=fig.transFigure))
    fig.text(0.5, 0.074, title, ha="center", va="center", fontsize=11.5, fontweight="bold", family="serif", color="#1b1916")
    fig.text(0.5, 0.046, subtitle, ha="center", va="center", fontsize=8.2, style="italic", family="serif", color="#524a3d")
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)

    svg_prev = ASSETS_DIR / f"{stem}_svg_preview.png"
    subprocess.run(["rsvg-convert", "-w", "1000", "-o", str(svg_prev), str(svg_path)], check=True)

    # 2x4 Unicode Braille bundle
    lines = ink_to_braille_lines(cleaned, cols=braille_cols)
    br = save_braille_bundle(lines, ASSETS_DIR, stem, title=title, subtitle=subtitle)
    print(f"OK hero assets [{stem}]: SVG={svg_path.stat().st_size/1024:.1f}KB Braille={braille_cols}x{len(lines)}")
    return {
        "archival": str(arch_path),
        "ink_bw": str(bw_path),
        "svg": str(svg_path),
        "svg_preview": str(svg_prev),
        **br,
    }


def chapter_for_sec(sec: float) -> tuple[str, tuple[int, int, int]]:
    if sec < 228:
        return "CH.1 · FIELD NOTEBOOK & POEMS", (242, 196, 92)
    if sec < 350:
        return "CH.2 · VINTAGE ILLUSTRATED FOLIO", (168, 226, 142)
    if 490 <= sec <= 515:
        return "CH.3 · FIG. 57 STELIS LEUCOPOGON", (255, 105, 130)
    if sec < 612:
        return "CH.3 · AMES & CORRELL ORCHIDS", (94, 218, 238)
    if sec < 700:
        return "CH.4 · ROSE TATTOO & LIVE PEN ART", (244, 138, 178)
    return "CH.5 · ZOE MOBILE APP STUDIO", (195, 162, 255)


def run_chiasm_and_timelapse() -> dict[str, Any]:
    CHIASM_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    # Sample the full 13.09 min (785.5s) screencast at 1.5 fps (~1178 frames -> 49s @ 24fps smooth 16x timelapse!)
    # Cropped cleanly to Pixel 7 camera viewport (x=743..1177, y=155..875 -> 434x720!)
    sample_fps = 1.5
    out_fps = 24
    vid_w, vid_h = 434, 720
    out_w, out_h = 1280, 720

    print("Decoding full 13-min screencast at 1.5 fps (16x smooth timelapse, 434x720 clean phone viewport)...")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(SRC),
        "-vf", f"fps={sample_fps},crop={vid_w}:{vid_h}:{VP_X}:155",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    fbytes = vid_w * vid_h * 3
    n_frames = len(raw) // fbytes
    frames = np.frombuffer(raw[: n_frames * fbytes], dtype=np.uint8).reshape(n_frames, vid_h, vid_w, 3)
    print(f"Decoded {n_frames} timelapse frames covering {n_frames / sample_fps:.1f}s -> {n_frames / out_fps:.1f}s @ {out_fps}fps.")

    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    # Collect ~196 evenly spaced episode distributions (every 6th frame = every 4s of real recording)
    episodes_8: list[dict[str, float]] = []
    ep_a004: list[int] = []
    ep_a010: list[int] = []
    ep_secs: list[float] = []

    for i in range(n_frames):
        # Measure luminance strictly on the UI-free botanical/notebook area (rows 30..500 inside 720p crop)
        sub = frames[i, 30:500:2, ::2, :]
        lum = (0.299 * sub[..., 0] + 0.587 * sub[..., 1] + 0.114 * sub[..., 2]).astype(np.uint8)
        counts = np.bincount(lum.ravel(), minlength=256).astype(np.float64)
        p = counts / counts.sum()
        hists[i] = p
        a004[i] = a_tau(p, 0.004)
        a010[i] = a_tau(p, 0.010)
        a020[i] = a_tau(p, 0.020)
        h1_arr[i] = shannon_h1(p)
        h2_arr[i] = renyi_h2(p)
        m4_arr[i] = quartic_m4(p)
        if i % 6 == 0 and len(episodes_8) < 220:
            episodes_8.append(lum_to_8state(p))
            ep_a004.append(int(a004[i]))
            ep_a010.append(int(a010[i]))
            ep_secs.append(i / sample_fps)

    # Nexus at Fig. 57 Stelis leucopogon (t = 498s = 08:18)
    nexus_ep = min(range(len(ep_secs)), key=lambda k: abs(ep_secs[k] - 498.0))
    past_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes_8[:nexus_ep]])) for s in TONAL_STATES})
    fut_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes_8[nexus_ep:]])) for s in TONAL_STATES})
    chiasm_res = causal_chiasm(past_avg, fut_avg, tau=0.10, horizon=12)
    tomo_res = persistent_filtration_tomography(
        episodes_8,
        thresholds=(0.04, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50),
        invariant_tau=0.14,
    )

    # Build GEM Scene SVG for Specimen #2
    w_svg, h_svg = 1400, 1000
    objs: list[dict[str, Any]] = [
        _rectangle("bg", [0, 0, w_svg, h_svg], BACKGROUND, BACKGROUND, 0),
        _rectangle("p1", [28, 96, 686, 520], RED, PANEL, 2),
        _rectangle("p2", [714, 96, 1372, 520], "#294058", PANEL, 1),
        _rectangle("p3", [28, 544, 1372, 926], "#294058", PANEL, 1),
        _text("title", [28, 44], "FIELDGLASS SPECIMEN #2 · 13-MIN CAUSAL CHIASM & TOMOGRAPHY", 24, RED),
        _text("sub", [28, 74], "Notebook Poems & Birds on a Wire -> Vintage Woodcuts -> Fig. 57 Stelis leucopogon (08:18) -> Live Pen Art", 14, GOLD),
    ]
    cx, cy = 357, 308
    objs.extend([
        _text("p1-t", [48, 128], "01 / CAUSAL CHIASM AT FIG. 57 NEXUS (08:18 / 498s)", 16, CYAN),
        _text("p1-pl", [52, 164], f"PAST (00:00-08:18) A_0.10 = {chiasm_res['past_accessible_volume']}", 13, CYAN),
        _text("p1-fl", [418, 164], f"FUTURE (08:18-13:05) A_0.10 = {chiasm_res['future_accessible_volume']}", 13, GOLD),
    ])
    for idx, (dy, cl, cr) in enumerate([(-92, CYAN, GOLD), (-44, CYAN, RED), (44, GOLD, CYAN), (92, RED, GOLD)]):
        objs.append(_polyline(f"cl-{idx}", [[88, cy + dy], [cx - 48, cy + dy * 0.35], [cx, cy]], cl, 2))
        objs.append(_polyline(f"cr-{idx}", [[cx, cy], [cx + 48, cy - dy * 0.35], [626, cy - dy]], cr, 2))
    objs.extend(woven_diamond("s2-gem", [cx, cy], 32, RED))
    ei = chiasm_res["effective_information_bits"]
    objs.extend([
        _text("p1-nx", [cx - 108, cy + 56], "FIG. 57 STELIS LEUCOPOGON", 13, GOLD),
        _text("p1-c1", [48, 478], f"Nexus EI = {ei:.4f} bits · shift = {chiasm_res['chiasm_shift']:+d} · glyph = {chiasm_res['presence_glyph']} · boxed_in = {chiasm_res['future_boxed_in']}", 13, TEXT),
        _text("p1-c2", [48, 502], f"Full 13.09-minute capture ({len(episodes_8)} episodes sampled every 4s)", 12, MUTED),
    ])

    objs.append(_text("p2-t", [734, 128], f"02 / PERSISTENT FILTRATION TOMOGRAPHY ({len(episodes_8)} EPISODES)", 16, CYAN))
    objs.append(_text("p2-s", [734, 154], "Mean survival threshold P(x) across 13 min of notebook + botanicals + app", 12, MUTED))
    for idx, (state, score) in enumerate(sorted(tomo_res["persistence_scores"].items(), key=lambda kv: -kv[1])):
        by = 188 + idx * 36
        bw = max(8, int(min(1.0, score / 0.55) * 340))
        is_inv = state in tomo_res["structural_invariants"]
        col = RED if is_inv else CYAN
        objs.extend([
            _text(f"p2-st-{idx}", [738, by + 16], state, 12, TEXT),
            _rectangle(f"p2-b-{idx}", [885, by + 2, 885 + bw, by + 22], col, col, 1),
            _text(f"p2-v-{idx}", [895 + bw, by + 17], f"P={score:.3f} {'INV' if is_inv else ''}", 12, GOLD if is_inv else MUTED),
        ])
    objs.append(_text("p2-cap", [734, 498], f"Invariants (tau>=0.14): {', '.join(tomo_res['structural_invariants']) or 'none'}", 12, GOLD))

    gx0, gy0, gx1, gy1 = 92, 628, 1330, 868
    objs.extend([
        _text("p3-t", [48, 578], "03 / 13-MINUTE KLOSTER ACCESSIBLE VOLUME TRAJECTORY  A_tau(p_t)", 16, CYAN),
        _text("p3-s", [48, 604], "Cyan: A_0.004(p_t) [0..160]  ·  Gold: A_0.010(p_t) [0..50]  ·  Ruby marker: Fig. 57 Stelis leucopogon (08:18)", 12, MUTED),
        _rectangle("p3-grid", [gx0, gy0, gx1, gy1], "#294058", "#0c1420", 1),
    ])
    n_ep = max(1, len(ep_a010) - 1)
    # Shaded Ames & Correll orchids chapter (350s..612s)
    ox0 = gx0 + (350.0 / 785.5) * (gx1 - gx0)
    ox1 = gx0 + (612.0 / 785.5) * (gx1 - gx0)
    objs.append(_rectangle("p3-orch", [ox0, gy0 + 1, ox1, gy1 - 1], "#243a4d", "#112233", 1))
    fx = gx0 + (498.0 / 785.5) * (gx1 - gx0)
    objs.append(_line("p3-nx", [fx, gy0], [fx, gy1], RED, 2))
    objs.append(_text("p3-nxl", [fx + 6, gy0 + 20], "FIG. 57 (08:18)", 12, RED))
    objs.append(_polyline("p3-004", [[gx0 + (t / n_ep) * (gx1 - gx0), gy1 - min(1.0, v / 160.0) * (gy1 - gy0 - 14) - 6] for t, v in enumerate(ep_a004)], CYAN, 2))
    objs.append(_polyline("p3-010", [[gx0 + (t / n_ep) * (gx1 - gx0), gy1 - min(1.0, v / 50.0) * (gy1 - gy0 - 14) - 6] for t, v in enumerate(ep_a010)], GOLD, 3))
    for m in (0, 2, 4, 6, 8, 10, 12):
        mx = gx0 + ((m * 60.0) / 785.5) * (gx1 - gx0)
        objs.append(_text(f"p3-m-{m}", [mx - 12, gy1 + 20], f"{m:02d}:00", 12, MUTED))
    objs.append(_text("p3-st", [48, 912], f"A_0.010 mean={np.mean(ep_a010):.1f} · max={max(ep_a010)} · min={min(ep_a010)} · Fig.57 A_0.010={ep_a010[nexus_ep]} · Invariants={len(tomo_res['structural_invariants'])}", 13, GOLD))
    objs.extend(hud_stamp_objects("s2", 1062, 18, chiasm_res["future_accessible_volume"], 0.10, chiasm_res["presence_glyph"]))
    objs.append(_text("foot", [28, 968], "Fieldglass Specimen #2 · GEM Causal Chiasm + Kloster A_tau(p) · 0 cloud tokens · executed=False", 13, MUTED))

    scene = Scene.from_dict({
        "schema_version": 1,
        "id": "fieldglass-specimen2-chiasm",
        "title": "Fieldglass Specimen #2 · 13-Min Causal Chiasm & Filtration Tomography",
        "canvas": {"width": w_svg, "height": h_svg},
        "objects": objs,
        "constraints": [{"type": "inside_canvas", "object": "*"}],
    })
    ch_svg = CHIASM_DIR / "specimen2_chiasm.svg"
    ch_png = CHIASM_DIR / "specimen2_chiasm.png"
    write_svg(scene, ch_svg, width=1400)
    subprocess.run(["rsvg-convert", "-w", "1400", "-o", str(ch_png), str(ch_svg)], check=True)

    report = {
        "source_video": str(SRC),
        "duration_sec": 785.55,
        "contract": CHIASM_CONTRACT,
        "equation": "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]",
        "episode_count": len(episodes_8),
        "nexus_sec": 498,
        "nexus_label": "Fig. 57 Stelis leucopogon (Blanche Ames, p. 177)",
        "chiasm_fig57_nexus": chiasm_res,
        "persistent_filtration_tomography": tomo_res,
        "scene_sha256": scene.digest(),
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    (CHIASM_DIR / "specimen2_chiasm_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Render 1280x720 24fps 16x Telemetry Timelapse Reel (~49s, ultra-clean!)
    f_title = _load_font(19, bold=True)
    f_eq = _load_font(15, bold=True)
    f_med = _load_font(15, bold=False)
    f_big = _load_font(23, bold=True)
    f_sm = _load_font(12, bold=False)
    f_sm_b = _load_font(12, bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)
    rx0, rx1 = vid_w + 14, out_w - 16  # 448..1264

    dr.rounded_rectangle([rx0, 12, rx1, 96], radius=10, fill=(16, 23, 35), outline=(52, 78, 108), width=2)
    dr.text((rx0 + 16, 20), "FIELDGLASS SPECIMEN #2 · 13-MIN FIELD SESSION (16x)", fill=(235, 194, 104), font=f_title)
    dr.text((rx0 + 16, 48), "A_tau(p) = |{x in X : p(x) > tau}| = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 16, 72), "Notebook Sketches · Vintage Folio · Fig. 57 Stelis leucopogon · Zoe App", fill=(150, 168, 190), font=f_sm)

    kpi_meta = [
        ("A_0.004(p)", (94, 218, 238)),
        ("A_0.010(p)", (242, 196, 92)),
        ("M_0.01 (dA)", (244, 106, 126)),
        ("H1 / H2 (b)", (168, 226, 142)),
        ("M4^(1/4)", (195, 162, 255)),
    ]
    kpi_w = (rx1 - rx0 - 40) // 5
    kpi_boxes = []
    for idx, (lbl, col) in enumerate(kpi_meta):
        bx0 = rx0 + idx * (kpi_w + 10)
        bx1 = bx0 + kpi_w
        kpi_boxes.append((bx0, 108, bx1, 184))
        dr.rounded_rectangle([bx0, 108, bx1, 184], radius=8, fill=(16, 23, 35), outline=(44, 62, 86), width=1)
        dr.text((bx0 + 10, 116), lbl, fill=col, font=f_sm_b)

    tx0, ty0, tx1, ty1 = rx0, 196, rx1, 452
    dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((tx0 + 14, ty0 + 8), "13-MIN SUPERLEVEL TRAJECTORY A_tau(p_t)  (Cyan: 0.004 · Gold: 0.010 · Ruby: 0.020)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + 44, ty0 + 34, tx1 - 16, ty1 - 28
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    total_real_s = n_frames / sample_fps
    def sx(real_s: float) -> int:
        return int(round(px0 + (real_s / total_real_s) * (px1 - px0)))

    # Shaded chapter bands
    dr.rectangle([sx(0), py0 + 1, sx(228), py1 - 1], fill=(24, 22, 16))
    dr.rectangle([sx(350), py0 + 1, sx(612), py1 - 1], fill=(15, 31, 46))
    dr.rectangle([sx(490), py0 + 1, sx(515), py1 - 1], fill=(48, 20, 34))
    dr.text((sx(8), py0 + 5), "NOTEBOOK", fill=(190, 168, 105), font=f_sm)
    dr.text((sx(356), py0 + 5), "BLANCHE AMES ORCHIDS", fill=(86, 175, 206), font=f_sm)
    dr.text((sx(491), py0 + 20), "FIG.57", fill=(255, 112, 138), font=f_sm_b)

    for val in (0, 15, 30, 45):
        gy = int(round(py1 - (val / 50.0) * (py1 - py0 - 8) - 4))
        dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
        dr.text((tx0 + 10, gy - 6), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)
    for m_tick in (0, 2, 4, 6, 8, 10, 12):
        gx = sx(m_tick * 60.0)
        dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
        dr.text((gx - 12, py1 + 6), f"{m_tick:02d}:00", fill=(128, 146, 168), font=f_sm)

    def draw_series(draw_obj: ImageDraw.ImageDraw, vals: np.ndarray, ymax: float, col: tuple[int, int, int], end_idx: int, w_px: int = 2):
        if end_idx < 1:
            return
        step = max(1, n_frames // 420)
        pts = [
            (
                int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in range(0, end_idx + 1, step)
        ]
        if len(pts) >= 2:
            draw_obj.line(pts, fill=col, width=w_px)

    draw_series(dr, a004, 180.0, (24, 62, 74), n_frames - 1, 1)
    draw_series(dr, a010, 50.0, (78, 64, 30), n_frames - 1, 1)

    hx0, hy0, hx1, hy1 = rx0, 464, rx1, 708
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE DISTRIBUTION p_t(x) (|X|=256) · Gold: p_t(x) > tau=0.010", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + 44, hy0 + 34, hx1 - 16, hy1 - 28
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    p_ymax = 0.040
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    bar_w = (hpx1 - hpx0) / 256.0
    for pv in (0.00, 0.01, 0.02, 0.03, 0.04):
        gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
        dr.text((hx0 + 6, gy - 6), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

    out_mp4 = VIDEO_DIR / "specimen2_a_tau_overlay.mp4"
    poster_png = VIDEO_DIR / "specimen2_overlay_poster.png"
    enc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{out_w}x{out_h}", "-r", str(out_fps), "-i", "-",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_mp4),
        ],
        stdin=subprocess.PIPE,
    )
    assert enc.stdin is not None
    poster_idx = min(n_frames - 1, int(498.0 * sample_fps))

    for i in range(n_frames):
        real_s = i / sample_fps
        mm, ss = divmod(int(real_s), 60)
        canvas = bg.copy()
        canvas.paste(Image.fromarray(frames[i]), (0, 0))
        d = ImageDraw.Draw(canvas)

        ch_lbl, ch_col = chapter_for_sec(real_s)
        d.rounded_rectangle([10, 12, vid_w - 10, 48], radius=8, fill=(10, 14, 22), outline=ch_col, width=2)
        d.text((20, 22), f"{mm:02d}:{ss:02d}  ·  {ch_lbl}", fill=ch_col, font=f_sm_b)
        d.rounded_rectangle([10, out_h - 46, vid_w - 10, out_h - 10], radius=8, fill=(10, 14, 22), outline=(94, 218, 238), width=1)
        d.text((20, out_h - 35), f"A_0.010={a010[i]:>2d}/256   H1={h1_arr[i]:.2f}b   H2={h2_arr[i]:.2f}b", fill=(235, 240, 245), font=f_sm_b)

        mom = int(a010[i] - a010[max(0, i - 6)])
        vals = [
            (f"{a004[i]:>3d}", (94, 218, 238)),
            (f"{a010[i]:>3d}", (242, 196, 92)),
            (f"{mom:+3d}", (244, 106, 126) if mom >= 0 else (94, 218, 238)),
            (f"{h1_arr[i]:.2f}/{h2_arr[i]:.2f}", (168, 226, 142)),
            (f"{m4_arr[i]:.4f}", (195, 162, 255)),
        ]
        for (bx0, by0, _, _), (val_s, col) in zip(kpi_boxes, vals):
            d.text((bx0 + 10, by0 + 36), val_s, fill=col, font=f_big if len(val_s) <= 6 else f_med)

        draw_series(d, a004, 180.0, (86, 212, 232), i, 2)
        draw_series(d, a010, 50.0, (242, 196, 92), i, 3)
        draw_series(d, a020, 50.0, (244, 106, 126), i, 2)
        cur_x = int(round(px0 + (i / max(1, n_frames - 1)) * (px1 - px0)))
        d.line([(cur_x, py0), (cur_x, py1)], fill=(255, 255, 255), width=2)
        cur_y = int(round(py1 - min(1.0, float(a010[i]) / 50.0) * (py1 - py0 - 8) - 4))
        d.ellipse([cur_x - 5, cur_y - 5, cur_x + 5, cur_y + 5], fill=(242, 196, 92), outline=(255, 255, 255), width=2)

        p_now = hists[i]
        for b in range(256):
            pv = float(p_now[b])
            if pv <= 0.0002:
                continue
            bx0 = int(hpx0 + b * bar_w)
            bx1 = max(bx0 + 1, int(hpx0 + (b + 1) * bar_w))
            bh_y = int(round(hpy1 - min(1.0, pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
            bar_col = (242, 196, 92) if pv > 0.010 else ((86, 198, 224) if pv > 0.004 else (58, 78, 102))
            d.rectangle([bx0, bh_y, bx1, hpy1 - 2], fill=bar_col)
        for dx in range(hpx0, hpx1, 12):
            d.line([(dx, tau_y), (min(hpx1, dx + 6), tau_y)], fill=(244, 106, 126), width=2)
        d.text((hpx1 - 196, tau_y - 16), f"tau = 0.010  ->  A_tau = {a010[i]}", fill=(244, 106, 126), font=f_sm_b)

        if i == poster_idx:
            canvas.save(poster_png)
        enc.stdin.write(canvas.tobytes())

    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg overlay render failed")
    print(f"OK Specimen #2 overlay MP4: {out_mp4} ({out_mp4.stat().st_size/1e6:.2f} MB)")
    return {"report": report, "mp4": str(out_mp4), "poster": str(poster_png), "chiasm_png": str(ch_png), "chiasm_svg": str(ch_svg)}


if __name__ == "__main__":
    plates = extract_clean_plates()
    # Hero 1: Fig. 57 Stelis leucopogon (Blanche Ames, p. 177) — isolate pure orchid drawing (below paragraph text, above caption)
    make_hero_specimen_assets(
        plates["04_fig57_stelis_leucopogon"],
        "fig57_stelis_leucopogon",
        title="FIG. 57.  STELIS LEUCOPOGON  Reichb. f.",
        subtitle="Orchids of Guatemala and Belize · Oakes Ames & Donovan Stewart Correll · Drawn by Blanche Ames (p. 177)",
        art_box_frac=(0.14, 0.21, 0.88, 0.87),
        paper_cutoff=0.915,
        ink_floor=0.38,
        gamma=1.22,
        svg_levels=(0.09, 0.25, 1.2),
        braille_cols=70,
    )
    # Hero 2: Nick's original "Birds on a Wire" notebook pen sketch & poem
    make_hero_specimen_assets(
        plates["01_birds_on_a_wire"],
        "nick_birds_on_a_wire",
        title="BIRDS ON A WIRE — ORIGINAL FIELD NOTEBOOK SKETCH",
        subtitle="\"Birds on a wire with nothin to do / So I tell em 'I'll scribble bout you!'\" · Nicholas Kloster",
        art_box_frac=(0.16, 0.05, 0.86, 0.90),
        paper_cutoff=0.905,
        ink_floor=0.42,
        gamma=1.30,
        svg_levels=(0.12, 0.28, 1.2),
        braille_cols=66,
    )
    res = run_chiasm_and_timelapse()
    print("DONE SPECIMEN #2:", json.dumps({
        "chiasm_glyph": res["report"]["chiasm_fig57_nexus"]["presence_glyph"],
        "past_A": res["report"]["chiasm_fig57_nexus"]["past_accessible_volume"],
        "future_A": res["report"]["chiasm_fig57_nexus"]["future_accessible_volume"],
        "invariants": res["report"]["persistent_filtration_tomography"]["structural_invariants"],
        "mp4_mb": round(Path(res["mp4"]).stat().st_size / 1e6, 2),
    }, indent=2))
