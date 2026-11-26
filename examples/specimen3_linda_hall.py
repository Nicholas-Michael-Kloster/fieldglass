#!/usr/bin/env python3
"""Fieldglass Specimen #3 — Linda Hall Library (Kansas City, MO).

Processes the real-world Linda Hall Library 4K 60fps stacks walkthrough
(`PXL_20261125_211807786.mp4`, 9.82 s, stereo ambient audio) + ZoeLearn field
captures (Magnetic Fabric, Separation of Plasma Proteins Fig. 1 affinity
chromatography elution curves, and Linda Hall autumn arboretum window):
  1. Sharpest 4K stacks stills + 6-tile Linda Hall Library contact sheet
  2. Archival print, framed vector SVG, and 2x4 Unicode Braille of Fig. 1
     (MK-521 Affinity Column Chromatography Elution Patterns, p. 236)
  3. 2x4 Unicode Braille architectural study of the Linda Hall stacks corridor
  4. 20-episode GEM Causal Chiasm & Persistent Filtration Tomography SVG + JSON
  5. Real-time 1280x720 24fps Kloster A_tau(p_t) telemetry video (with original stereo audio)
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

from fieldglass.plate import clean_illumination, ink_to_braille_lines, save_braille_bundle
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

SRC_VID = Path("/home/cowboy/fieldglass_linda_hall/raw/PXL_20261125_211807786.mp4")
ZOE_CAP = Path("/home/cowboy/fieldglass_linda_hall/zoe_learn_captures")
OUT = Path("/home/cowboy/fieldglass_linda_hall")
PLATES_DIR = OUT / "plates"
ASSETS_DIR = OUT / "assets"
CHIASM_DIR = OUT / "chiasm"
VIDEO_DIR = OUT / "video"

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
    g = im.convert("L")
    g.thumbnail((720, 1280))
    return float(ndimage.laplace(np.asarray(g, dtype=np.float32)).var())


def extract_linda_hall_plates() -> dict[str, Path]:
    PLATES_DIR.mkdir(parents=True, exist_ok=True)
    windows = [
        ("01_stacks_aisle_entry", "Stacks Aisle Entry (4K)", 0.0, 2.2),
        ("02_stacks_deep_corridor", "Deep Science Monograph Corridor (4K)", 4.0, 2.2),
        ("03_stacks_bound_journals", "Bound Scientific Journals (4K)", 6.8, 2.3),
    ]
    out_map: dict[str, Path] = {}
    tiles: list[tuple[str, Path]] = []

    with tempfile.TemporaryDirectory() as tmp:
        for slug, label, start, dur in windows:
            cdir = Path(tmp) / slug
            cdir.mkdir()
            subprocess.run([
                "ffmpeg", "-v", "error", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
                "-i", str(SRC_VID), "-vf", "fps=10", "-q:v", "2", str(cdir / "f_%03d.jpg")
            ], check=True)
            cands = sorted(cdir.glob("f_*.jpg"))
            best = max(cands, key=lambda p: sharp_score(Image.open(p)))
            best_ts = start + cands.index(best) / 10.0
            out_jpg = PLATES_DIR / f"{slug}.jpg"
            # Save full 2160x3840 4K crisp 92% JPEG for fast web loading
            raw_png = Path(tmp) / f"{slug}.png"
            subprocess.run([
                "ffmpeg", "-v", "error", "-ss", f"{best_ts:.3f}", "-i", str(SRC_VID),
                "-frames:v", "1", "-y", str(raw_png)
            ], check=True)
            with Image.open(raw_png) as im:
                im.convert("RGB").save(out_jpg, quality=92, optimize=True)
                print(f"OK {slug}: t={best_ts:.2f}s size={im.size} ({out_jpg.stat().st_size/1024:.0f} KB)")
            out_map[slug] = out_jpg
            tiles.append((f"{best_ts:04.1f}s · {label}", out_jpg))

    # Copy the 3 distinct Linda Hall ZoeLearn captures cleanly into plates/
    cap_pairs = [
        ("04_magnetic_fabric_geology", "Magnetic Fabric · Geological Society", ZOE_CAP / "ZoeLearn_20261125_152203_sky.jpg"),
        ("05_plasma_proteins_elution_fig1", "Separation of Plasma Proteins · Fig. 1", ZOE_CAP / "ZoeLearn_20261125_154253_sky.jpg"),
        ("06_linda_hall_arboretum_window", "Linda Hall Autumn Arboretum Window", ZOE_CAP / "ZoeLearn_20261125_155819_sky.jpg"),
    ]
    for slug, label, src_p in cap_pairs:
        dst_p = PLATES_DIR / f"{slug}.jpg"
        with Image.open(src_p) as im:
            im.convert("RGB").save(dst_p, quality=92)
        out_map[slug] = dst_p
        tiles.append((label, dst_p))

    # 3x2 Contact Sheet
    tw, th = 420, 700
    sheet = Image.new("RGB", (3 * tw, 2 * th), (12, 15, 22))
    sd = ImageDraw.Draw(sheet)
    f_lbl = _load_font(12, bold=True)
    for idx, (label, pp) in enumerate(tiles):
        im = Image.open(pp).convert("RGB")
        im.thumbnail((tw - 14, th - 36))
        r, c = divmod(idx, 3)
        ox = c * tw + (tw - im.width) // 2
        oy = r * th + 28 + (th - 36 - im.height) // 2
        sheet.paste(im, (ox, oy))
        sd.text((c * tw + 10, r * th + 8), label[:40], fill=(242, 196, 92), font=f_lbl)
    sheet.save(PLATES_DIR / "contact_sheet_linda_hall.jpg", quality=92)
    return out_map


def build_chromatography_and_corridor_assets(plates: dict[str, Path]) -> dict[str, str]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Hero Scientific Figure: Separation of Plasma Proteins, p. 236 — Fig. 1 MK-521 Affinity Chromatography Elution Patterns
    im = Image.open(plates["05_plasma_proteins_elution_fig1"]).convert("RGB")
    w, h = im.size
    # Crop specifically to the crisp Fig. 1 chromatography graph region (top half of page, y: 0.28..0.525, x: 0.04..0.82)
    fig_crop = im.crop((int(w * 0.03), int(h * 0.285), int(w * 0.83), int(h * 0.525)))
    # Upscale 4x for ultra-smooth contour vectorization
    up = fig_crop.resize((fig_crop.width * 4, fig_crop.height * 4), Image.Resampling.BICUBIC)
    ink, archival, bw = clean_illumination(up, sigma=40.0, paper_cutoff=0.925, ink_floor=0.45, gamma=1.12)

    # Trim micro specks
    mask = ink > 0.14
    lab, nc = ndimage.label(mask)
    cleaned = np.where((ndimage.sum(mask, lab, range(1, nc + 1)) >= 5)[lab - 1] & mask, ink, 0.0) if nc else ink

    arch_path = ASSETS_DIR / "linda_hall_fig1_chromatography_archival.png"
    bw_path = ASSETS_DIR / "linda_hall_fig1_chromatography_bw.png"
    archival.save(arch_path)
    bw.save(bw_path)

    # Framed scientific monograph SVG
    ah, aw = cleaned.shape
    vw = 760
    vh = max(64, int(round(ah * (vw / aw))))
    sm = ndimage.gaussian_filter(
        np.asarray(Image.fromarray((cleaned * 255).clip(0, 255).astype(np.uint8)).resize((vw, vh), Image.Resampling.BOX), dtype=np.float32) / 255.0,
        sigma=0.55,
    )
    svg_path = ASSETS_DIR / "linda_hall_fig1_chromatography.svg"
    fig = plt.figure(figsize=(10.0, 6.2), dpi=100, facecolor="#f6f1e4")
    ax = fig.add_axes([0.05, 0.17, 0.90, 0.76], facecolor="#f6f1e4")
    ax.contourf(sm, levels=[0.09, 0.24, 1.2], colors=["#5c6570", "#181b20"])
    ax.set_xlim(0, vw - 1); ax.set_ylim(vh - 1, 0); ax.set_aspect("equal"); ax.axis("off")
    fig.patches.append(plt.Rectangle((0.022, 0.032), 0.956, 0.936, fill=False, edgecolor="#8c7f68", linewidth=1.2, transform=fig.transFigure))
    fig.patches.append(plt.Rectangle((0.030, 0.044), 0.940, 0.912, fill=False, edgecolor="#c4b89f", linewidth=0.6, transform=fig.transFigure))
    fig.text(0.5, 0.102, "LINDA HALL LIBRARY · SEPARATION OF PLASMA PROTEINS (p. 236)", ha="center", va="center", fontsize=11.5, fontweight="bold", family="serif", color="#181b20")
    fig.text(0.5, 0.064, "Fig. 1 — Comparative elution patterns from MK-521 affinity column (lung homogenates) · Kansas City, MO", ha="center", va="center", fontsize=8.4, style="italic", family="serif", color="#4e5259")
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)

    svg_prev = ASSETS_DIR / "linda_hall_fig1_chromatography_svg_preview.png"
    subprocess.run(["rsvg-convert", "-w", "1100", "-o", str(svg_prev), str(svg_path)], check=True)

    # 2x4 Unicode Braille of Fig. 1 elution peaks
    br_lines = ink_to_braille_lines(np.clip(cleaned * 1.35, 0.0, 1.0), cols=76)
    br_fig1 = save_braille_bundle(
        br_lines,
        ASSETS_DIR,
        "linda_hall_fig1_chromatography",
        title="LINDA HALL LIBRARY — FIG. 1 MK-521 AFFINITY CHROMATOGRAPHY",
        subtitle="Separation of Plasma Proteins (p. 236) · 76-col Unicode Braille",
    )

    # 2. Architectural 2x4 Braille study of the iconic Linda Hall Library Deep Stacks Corridor (edge + luminance hybrid!)
    im_c = Image.open(plates["02_stacks_deep_corridor"]).convert("L")
    im_c.thumbnail((720, 1280))
    arr_c = np.asarray(im_c, dtype=np.float32) / 255.0
    # Sobel edge magnitude highlights the dramatic vanishing-point metal shelving & book spines!
    sx = ndimage.sobel(arr_c, axis=1)
    sy = ndimage.sobel(arr_c, axis=0)
    edges = np.hypot(sx, sy)
    edges = np.clip(edges / max(1e-4, float(np.percentile(edges, 96))), 0.0, 1.0)
    # Blend structural edges + dark bookshelf silhouettes for striking architectural Braille
    arch_field = np.clip(edges * 0.80 + (1.0 - arr_c) * 0.28 - 0.14, 0.0, 1.0)
    corridor_lines = ink_to_braille_lines(arch_field, cols=64)
    br_corr = save_braille_bundle(
        corridor_lines,
        ASSETS_DIR,
        "linda_hall_stacks_corridor",
        title="LINDA HALL LIBRARY — SCIENCE STACKS CORRIDOR",
        subtitle="Architectural Edge-Field Study (4K) · Kansas City, MO · 64-col Braille",
    )

    print("OK Linda Hall Fig. 1 SVG/Braille + Corridor Braille built!")
    return {
        "fig1_archival": str(arch_path),
        "fig1_bw": str(bw_path),
        "fig1_svg": str(svg_path),
        "fig1_svg_preview": str(svg_prev),
        "fig1_braille": br_fig1["preview_png"],
        "corridor_braille": br_corr["preview_png"],
    }


def phase_for_sec(sec: float) -> tuple[str, tuple[int, int, int]]:
    if sec < 2.4:
        return "AISLE ENTRY · SCIENCE STACKS", (94, 218, 238)
    if sec < 4.4:
        return "BOOK SPINE SWEEP · SHELVING", (242, 196, 92)
    if sec < 6.7:
        return "DEEP CORRIDOR · VANISHING POINT", (255, 105, 130)
    return "BOUND MONOGRAPHS & JOURNALS", (168, 226, 142)


def run_chiasm_and_overlay() -> dict[str, Any]:
    CHIASM_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    fps = 24
    vid_w, vid_h = 406, 720
    out_w, out_h = 1280, 720

    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(SRC_VID),
        "-vf", f"fps={fps},scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    fbytes = vid_w * vid_h * 3
    n_frames = len(raw) // fbytes
    frames = np.frombuffer(raw[: n_frames * fbytes], dtype=np.uint8).reshape(n_frames, vid_h, vid_w, 3)
    print(f"Decoded {n_frames} frames ({n_frames / fps:.2f}s) from Linda Hall 4K source.")

    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    # Sample 20 half-second episodes across the 9.82s walkthrough for rich Chiasm tomography!
    episodes_8: list[dict[str, float]] = []
    ep_a004: list[int] = []
    ep_a010: list[int] = []
    step_ep = max(1, fps // 2)  # every 0.5s

    for i in range(n_frames):
        sub = frames[i, ::2, ::2, :]
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
        if i % step_ep == 0:
            episodes_8.append(lum_to_8state(p))
            ep_a004.append(int(a004[i]))
            ep_a010.append(int(a010[i]))

    # Deep Corridor nexus at t = 5.0s (episode 10)
    nexus_ep = min(len(episodes_8) - 1, 10)
    past_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes_8[:nexus_ep]])) for s in TONAL_STATES})
    fut_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes_8[nexus_ep:]])) for s in TONAL_STATES})
    chiasm_res = causal_chiasm(past_avg, fut_avg, tau=0.10, horizon=5)
    tomo_res = persistent_filtration_tomography(
        episodes_8,
        thresholds=(0.04, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50),
        invariant_tau=0.14,
    )

    # GEM Scene SVG
    w_svg, h_svg = 1400, 1000
    objs: list[dict[str, Any]] = [
        _rectangle("bg", [0, 0, w_svg, h_svg], BACKGROUND, BACKGROUND, 0),
        _rectangle("p1", [28, 96, 686, 520], RED, PANEL, 2),
        _rectangle("p2", [714, 96, 1372, 520], "#294058", PANEL, 1),
        _rectangle("p3", [28, 544, 1372, 926], "#294058", PANEL, 1),
        _text("title", [28, 44], "LINDA HALL LIBRARY · CAUSAL CHIASM & A_tau(p_t) TOMOGRAPHY", 24, RED),
        _text("sub", [28, 74], "Kansas City, MO · Science & Engineering Stacks 4K Walkthrough (9.82s · 20 Half-Second Episodes)", 14, GOLD),
    ]
    cx, cy = 357, 308
    objs.extend([
        _text("p1-t", [48, 128], "01 / CAUSAL CHIASM AT DEEP CORRIDOR NEXUS (t = 5.0s)", 16, CYAN),
        _text("p1-pl", [52, 164], f"PAST (0.0-5.0s) A_0.10 = {chiasm_res['past_accessible_volume']}", 13, CYAN),
        _text("p1-fl", [428, 164], f"FUTURE (5.0-9.8s) A_0.10 = {chiasm_res['future_accessible_volume']}", 13, GOLD),
    ])
    for idx, (dy, cl, cr) in enumerate([(-92, CYAN, GOLD), (-44, CYAN, RED), (44, GOLD, CYAN), (92, RED, GOLD)]):
        objs.append(_polyline(f"lh-l-{idx}", [[88, cy + dy], [cx - 48, cy + dy * 0.35], [cx, cy]], cl, 2))
        objs.append(_polyline(f"lh-r-{idx}", [[cx, cy], [cx + 48, cy - dy * 0.35], [626, cy - dy]], cr, 2))
    objs.extend(woven_diamond("lh-gem", [cx, cy], 32, RED))
    ei = chiasm_res["effective_information_bits"]
    objs.extend([
        _text("p1-nx", [cx - 98, cy + 56], "DEEP STACKS CORRIDOR", 13, GOLD),
        _text("p1-c1", [48, 478], f"Nexus EI = {ei:.4f} bits · shift = {chiasm_res['chiasm_shift']:+d} · glyph = {chiasm_res['presence_glyph']} · boxed_in = {chiasm_res['future_boxed_in']}", 13, TEXT),
        _text("p1-c2", [48, 502], "Linda Hall Library of Science, Engineering & Technology · Kansas City, MO", 12, MUTED),
    ])

    objs.append(_text("p2-t", [734, 128], f"02 / PERSISTENT FILTRATION TOMOGRAPHY ({len(episodes_8)} EPISODES)", 16, CYAN))
    objs.append(_text("p2-s", [734, 154], "Mean survival threshold P(x) across 4K library stacks walkthrough", 12, MUTED))
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
        _text("p3-t", [48, 578], "03 / LIVE KLOSTER ACCESSIBLE VOLUME TRAJECTORY  A_tau(p_t)", 16, CYAN),
        _text("p3-s", [48, 604], "Cyan: A_0.004(p_t) [0..160]  ·  Gold: A_0.010(p_t) [0..50]  ·  Ruby marker: Deep Corridor Pivot (5.0s)", 12, MUTED),
        _rectangle("p3-grid", [gx0, gy0, gx1, gy1], "#294058", "#0c1420", 1),
    ])
    n_ep = max(1, len(ep_a010) - 1)
    fx = gx0 + (nexus_ep / n_ep) * (gx1 - gx0)
    objs.append(_line("p3-nx", [fx, gy0], [fx, gy1], RED, 2))
    objs.append(_text("p3-nxl", [fx + 6, gy0 + 20], "CORRIDOR PIVOT (5.0s)", 12, RED))
    objs.append(_polyline("p3-004", [[gx0 + (t / n_ep) * (gx1 - gx0), gy1 - min(1.0, v / 160.0) * (gy1 - gy0 - 14) - 6] for t, v in enumerate(ep_a004)], CYAN, 2))
    objs.append(_polyline("p3-010", [[gx0 + (t / n_ep) * (gx1 - gx0), gy1 - min(1.0, v / 50.0) * (gy1 - gy0 - 14) - 6] for t, v in enumerate(ep_a010)], GOLD, 3))
    for s_tick in (0, 2, 4, 6, 8, 10):
        mx = gx0 + (min(s_tick / 9.82, 1.0)) * (gx1 - gx0)
        objs.append(_text(f"p3-s-{s_tick}", [mx - 10, gy1 + 20], f"{s_tick}s", 12, MUTED))
    objs.append(_text("p3-st", [48, 912], f"A_0.010 mean={np.mean(ep_a010):.1f} · max={max(ep_a010)} · min={min(ep_a010)} · H1 mean={float(np.mean(h1_arr)):.2f}b · H2 mean={float(np.mean(h2_arr)):.2f}b", 13, GOLD))
    objs.extend(hud_stamp_objects("lhl", 1062, 18, chiasm_res["future_accessible_volume"], 0.10, chiasm_res["presence_glyph"]))
    objs.append(_text("foot", [28, 968], "Fieldglass Specimen #3 · Linda Hall Library (Kansas City, MO) · 0 cloud tokens · executed=False", 13, MUTED))

    scene = Scene.from_dict({
        "schema_version": 1,
        "id": "fieldglass-linda-hall-chiasm",
        "title": "Fieldglass Specimen #3 · Linda Hall Library Causal Chiasm",
        "canvas": {"width": w_svg, "height": h_svg},
        "objects": objs,
        "constraints": [{"type": "inside_canvas", "object": "*"}],
    })
    ch_svg = CHIASM_DIR / "specimen3_linda_hall_chiasm.svg"
    ch_png = CHIASM_DIR / "specimen3_linda_hall_chiasm.png"
    write_svg(scene, ch_svg, width=1400)
    subprocess.run(["rsvg-convert", "-w", "1400", "-o", str(ch_png), str(ch_svg)], check=True)

    report = {
        "location": "Linda Hall Library of Science, Engineering & Technology (Kansas City, MO)",
        "contract": CHIASM_CONTRACT,
        "equation": "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]",
        "duration_sec": round(n_frames / fps, 2),
        "episode_count": len(episodes_8),
        "nexus_sec": 5.0,
        "chiasm_corridor_nexus": chiasm_res,
        "persistent_filtration_tomography": tomo_res,
        "scene_sha256": scene.digest(),
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    (CHIASM_DIR / "specimen3_linda_hall_chiasm_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Render 1280x720 24fps telemetry video WITH original stereo library audio!
    f_title = _load_font(19, bold=True)
    f_eq = _load_font(15, bold=True)
    f_med = _load_font(15, bold=False)
    f_big = _load_font(23, bold=True)
    f_sm = _load_font(12, bold=False)
    f_sm_b = _load_font(12, bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)
    rx0, rx1 = vid_w + 14, out_w - 16

    dr.rounded_rectangle([rx0, 12, rx1, 96], radius=10, fill=(16, 23, 35), outline=(52, 78, 108), width=2)
    dr.text((rx0 + 16, 20), "LINDA HALL LIBRARY  ·  KLOSTER OPERATIONAL METACOGNITION", fill=(235, 194, 104), font=f_title)
    dr.text((rx0 + 16, 48), "A_tau(p) = |{x in X : p(x) > tau}| = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 16, 72), "Kansas City, MO · Science & Engineering Stacks 4K Live Telemetry", fill=(150, 168, 190), font=f_sm)

    kpi_meta = [
        ("A_0.004(p)", (94, 218, 238)),
        ("A_0.010(p)", (242, 196, 92)),
        ("M_0.01 (dA/s)", (244, 106, 126)),
        ("H1 / H2 (bits)", (168, 226, 142)),
        ("M4^(1/4) PURITY", (195, 162, 255)),
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
    dr.text((tx0 + 14, ty0 + 8), "SUPERLEVEL-SET VOLUME A_tau(p_t)  (Cyan: 0.004 · Gold: 0.010 · Ruby: 0.020)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + 48, ty0 + 34, tx1 - 16, ty1 - 28
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    total_s = n_frames / fps
    def sx(sec: float) -> int:
        return int(round(px0 + (sec / total_s) * (px1 - px0)))

    dr.rectangle([sx(4.4), py0 + 1, sx(6.7), py1 - 1], fill=(44, 20, 32))
    dr.text((sx(4.5), py0 + 6), "DEEP CORRIDOR", fill=(255, 112, 138), font=f_sm_b)
    for val in (0, 15, 30, 45):
        gy = int(round(py1 - (val / 50.0) * (py1 - py0 - 8) - 4))
        dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
        dr.text((tx0 + 12, gy - 6), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)
    for st in (0, 2, 4, 6, 8):
        gx = sx(st)
        dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
        dr.text((gx - 8, py1 + 6), f"{st}s", fill=(128, 146, 168), font=f_sm)

    def draw_series(draw_obj: ImageDraw.ImageDraw, vals: np.ndarray, ymax: float, col: tuple[int, int, int], end_idx: int, w_px: int = 2):
        if end_idx < 1:
            return
        pts = [
            (
                int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in range(0, end_idx + 1)
        ]
        if len(pts) >= 2:
            draw_obj.line(pts, fill=col, width=w_px)

    draw_series(dr, a004, 180.0, (24, 62, 74), n_frames - 1, 1)
    draw_series(dr, a010, 50.0, (78, 64, 30), n_frames - 1, 1)

    hx0, hy0, hx1, hy1 = rx0, 464, rx1, 708
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE DISTRIBUTION p_t(x) (|X|=256) · Gold: p_t(x) > tau=0.010", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + 48, hy0 + 34, hx1 - 16, hy1 - 28
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    p_ymax = 0.040
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    bar_w = (hpx1 - hpx0) / 256.0
    for pv in (0.00, 0.01, 0.02, 0.03, 0.04):
        gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
        dr.text((hx0 + 6, gy - 6), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

    out_mp4 = VIDEO_DIR / "specimen3_linda_hall_a_tau_overlay.mp4"
    poster_png = VIDEO_DIR / "specimen3_linda_hall_poster.png"
    enc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
            "-i", str(SRC_VID),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
            str(out_mp4),
        ],
        stdin=subprocess.PIPE,
    )
    assert enc.stdin is not None
    poster_idx = min(n_frames - 1, int(5.0 * fps))

    for i in range(n_frames):
        sec = i / fps
        canvas = bg.copy()
        canvas.paste(Image.fromarray(frames[i]), (0, 0))
        d = ImageDraw.Draw(canvas)

        plbl, pcol = phase_for_sec(sec)
        d.rounded_rectangle([10, 12, vid_w - 10, 48], radius=8, fill=(10, 14, 22), outline=pcol, width=2)
        d.text((20, 22), f"{sec:04.2f}s  ·  {plbl}", fill=pcol, font=f_sm_b)
        d.rounded_rectangle([10, out_h - 46, vid_w - 10, out_h - 10], radius=8, fill=(10, 14, 22), outline=(94, 218, 238), width=1)
        d.text((20, out_h - 35), f"A_0.010={a010[i]:>2d}/256   H1={h1_arr[i]:.2f}b   H2={h2_arr[i]:.2f}b", fill=(235, 240, 245), font=f_sm_b)

        mom = int(a010[i] - a010[max(0, i - fps)])
        vals = [
            (f"{a004[i]:>3d}", (94, 218, 238)),
            (f"{a010[i]:>3d}", (242, 196, 92)),
            (f"{mom:+3d}/s", (244, 106, 126) if mom >= 0 else (94, 218, 238)),
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
        raise RuntimeError("ffmpeg Linda Hall overlay failed")
    print(f"OK Specimen #3 overlay MP4: {out_mp4} ({out_mp4.stat().st_size/1e6:.2f} MB)")
    return {"report": report, "mp4": str(out_mp4), "poster": str(poster_png), "chiasm_png": str(ch_png)}


if __name__ == "__main__":
    plates = extract_linda_hall_plates()
    assets = build_chromatography_and_corridor_assets(plates)
    res = run_chiasm_and_overlay()
    print("DONE SPECIMEN #3 (LINDA HALL LIBRARY):", json.dumps({
        "chiasm_glyph": res["report"]["chiasm_corridor_nexus"]["presence_glyph"],
        "past_A": res["report"]["chiasm_corridor_nexus"]["past_accessible_volume"],
        "future_A": res["report"]["chiasm_corridor_nexus"]["future_accessible_volume"],
        "invariants": res["report"]["persistent_filtration_tomography"]["structural_invariants"],
        "mp4_mb": round(Path(res["mp4"]).stat().st_size / 1e6, 2),
    }, indent=2))
