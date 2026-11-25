#!/usr/bin/env python3
"""Flowers for Zoe.mp4 — GEM Causal Chiasm Integration + Real-Time A_tau(p_t) Telemetry Overlay Video.

Computes Nicholas Kloster's superlevel-set accessible volume:
    A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]
across every video frame, plugs the 26-second episode trajectory directly into
`guiai.gem.chiasm` (`causal_chiasm` + `persistent_filtration_tomography` + GEM `Scene` SVG),
and renders a 1280x720 24fps broadcast telemetry video with original audio preserved.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_GUIAI = Path("/media/cowboy/research/zoe-monorepo/guiai-lab")
if str(REPO_GUIAI) not in sys.path:
    sys.path.insert(0, str(REPO_GUIAI))

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

SRC_VIDEO = Path("/home/cowboy/Downloads/Flowers for Zoe.mp4")
OUT_ROOT = Path("/home/cowboy/flowers_for_zoe")
CHIASM_DIR = OUT_ROOT / "chiasm"
VIDEO_DIR = OUT_ROOT / "video"

# 8-state interpretable visual-tonal repertoire for Causal Chiasm & Filtration Tomography
TONAL_STATES = (
    "deep_shadow",       # L: 0..31
    "ink_linework",      # L: 32..63
    "dark_midtone",      # L: 64..95
    "botanical_mid",     # L: 96..127
    "warm_sepia",        # L: 128..159
    "aged_paper",        # L: 160..191
    "bright_cream",      # L: 192..223
    "paper_highlight",   # L: 224..255
)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in candidates:
        if Path(p).is_file():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def phase_label(sec: float) -> tuple[str, tuple[int, int, int]]:
    if sec < 3.6:
        return "COVER · AMES & CORRELL", (235, 190, 90)
    if 14.5 <= sec <= 16.5:
        return "FIG. 30 · SPIRANTHES ELATA (p. 109)", (255, 105, 130)
    if sec < 19.2:
        return "BOTANICAL INK PLATE", (86, 212, 232)
    return "ROOM / PORTRAIT PAN", (190, 165, 255)


def a_tau(p: np.ndarray, tau: float) -> int:
    return int(np.sum(p > tau))


def shannon_h1(p: np.ndarray) -> float:
    nz = p[p > 0]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def renyi_h2(p: np.ndarray) -> float:
    s = float(np.sum(p * p))
    return float(-math.log2(max(s, 1e-12)))


def quartic_purity_m4(p: np.ndarray) -> float:
    return float(np.sum(p ** 4) ** 0.25)


def luminance_to_8state(p256: np.ndarray) -> dict[str, float]:
    out: dict[str, float] = {}
    for idx, name in enumerate(TONAL_STATES):
        val = float(p256[idx * 32 : (idx + 1) * 32].sum())
        out[name] = max(val, 1e-9)
    total = sum(out.values())
    return {k: round(v / total, 6) for k, v in out.items()}


def normalize_dist(d: dict[str, float]) -> dict[str, float]:
    clean = {k: max(float(v), 1e-9) for k, v in d.items()}
    total = sum(clean.values())
    norm = {k: v / total for k, v in clean.items()}
    # Adjust largest bucket to guarantee exact float64 sum == 1.0
    max_k = max(norm, key=lambda k: norm[k])
    others = sum(v for k, v in norm.items() if k != max_k)
    norm[max_k] = 1.0 - others
    return norm


def run_chiasm_analysis(
    episodes_8: list[dict[str, float]],
    per_sec_a010: list[int],
    per_sec_a004: list[int],
    per_sec_h1: list[float],
    per_sec_h2: list[float],
) -> tuple[dict[str, Any], Path, Path]:
    CHIASM_DIR.mkdir(parents=True, exist_ok=True)
    episodes_norm = [normalize_dist(ep) for ep in episodes_8]

    # Retrograde past cone: cover + early plates (0..13s) -> Present nexus at Fig. 40 (t=15s) -> Counterfactual future cone (16..25s)
    past_avg = normalize_dist({
        s: float(np.mean([ep[s] for ep in episodes_norm[0:14]])) for s in TONAL_STATES
    })
    fig40_now = episodes_norm[min(15, len(episodes_norm) - 1)]
    future_avg = normalize_dist({
        s: float(np.mean([ep[s] for ep in episodes_norm[16:]])) for s in TONAL_STATES
    })

    # Plate-only vs Room-pan causal chiasm
    plates_avg = normalize_dist({
        s: float(np.mean([ep[s] for ep in episodes_norm[4:19]])) for s in TONAL_STATES
    })
    room_avg = normalize_dist({
        s: float(np.mean([ep[s] for ep in episodes_norm[20:]])) for s in TONAL_STATES
    })

    tau_chiasm = 0.10
    chiasm_fig40 = causal_chiasm(past_avg, future_avg, tau=tau_chiasm, horizon=10)
    chiasm_plates_vs_room = causal_chiasm(plates_avg, room_avg, tau=tau_chiasm, horizon=6)

    thresholds = (0.04, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50)
    tomography = persistent_filtration_tomography(
        episodes_norm,
        thresholds=thresholds,
        invariant_tau=0.14,
    )

    # Build a custom GEM Scene populated with REAL Flowers for Zoe.mp4 data
    width, height = 1400, 1000
    objects: list[dict[str, Any]] = [
        _rectangle("background", [0, 0, width, height], BACKGROUND, BACKGROUND, 0),
        _rectangle("panel-chiasm", [28, 96, 686, 520], RED, PANEL, 2),
        _rectangle("panel-filtration", [714, 96, 1372, 520], "#294058", PANEL, 1),
        _rectangle("panel-trajectory", [28, 544, 1372, 926], "#294058", PANEL, 1),
        _text("title", [28, 44], "FLOWERS FOR ZOE · CAUSAL CHIASM & A_tau(p_t) TOMOGRAPHY", 25, RED),
        _text("subtitle", [28, 74], "Orchids of Guatemala and Belize (Ames & Correll) · Fig. 30 Spiranthes elata Nexus (t = 15s)", 14, GOLD),
    ]

    # Panel 1: Causal Chiasm at Fig. 30 nexus
    cx, cy = 357, 308
    objects.extend([
        _text("p1-title", [48, 128], "01 / CAUSAL CHIASM AT FIG. 30 NEXUS (t = 15s)", 16, CYAN),
        _text("p1-past-lbl", [52, 164], f"PAST (0-13s) A_0.10 = {chiasm_fig40['past_accessible_volume']}", 13, CYAN),
        _text("p1-fut-lbl", [430, 164], f"FUTURE (16-25s) A_0.10 = {chiasm_fig40['future_accessible_volume']}", 13, GOLD),
    ])
    for idx, (dy, col_l, col_r) in enumerate([
        (-95, CYAN, GOLD),
        (-46, CYAN, RED),
        (46, GOLD, CYAN),
        (95, RED, GOLD),
    ]):
        objects.append(_polyline(f"chiasm-l-{idx}", [[88, cy + dy], [cx - 48, cy + dy * 0.35], [cx, cy]], col_l, 2))
        objects.append(_polyline(f"chiasm-r-{idx}", [[cx, cy], [cx + 48, cy - dy * 0.35], [626, cy - dy]], col_r, 2))
    objects.extend(woven_diamond("chiasm-nexus-gem", [cx, cy], 32, RED))
    ei_val = chiasm_fig40["effective_information_bits"]
    ei_str = f"{ei_val:.4f}" if isinstance(ei_val, (int, float)) else "n/a"
    objects.extend([
        _text("p1-nexus", [cx - 102, cy + 56], "FIG. 30 SPIRANTHES ELATA", 13, GOLD),
        _text(
            "p1-cap1",
            [48, 472],
            f"Nexus EI = {ei_str} bits · shift = {chiasm_fig40['chiasm_shift']:+d} · glyph = {chiasm_fig40['presence_glyph']}",
            13,
            TEXT,
        ),
        _text(
            "p1-cap2",
            [48, 498],
            f"Plates->Room: A_0.10 {chiasm_plates_vs_room['past_accessible_volume']} -> {chiasm_plates_vs_room['future_accessible_volume']} (EI={chiasm_plates_vs_room['effective_information_bits']:.4f} bits)",
            12,
            MUTED,
        ),
    ])

    # Panel 2: Persistent Filtration Tomography over 8 visual-tonal states
    objects.extend([
        _text("p2-title", [734, 128], "02 / PERSISTENT FILTRATION TOMOGRAPHY (26 EPISODES)", 16, CYAN),
        _text("p2-sub", [734, 154], "Mean survival threshold P(x) across 26s of Flowers for Zoe.mp4", 13, MUTED),
    ])
    scores = tomography["persistence_scores"]
    for idx, (state, score) in enumerate(sorted(scores.items(), key=lambda item: -item[1])):
        by = 188 + idx * 37
        bar_w = max(8, int(min(1.0, score / 0.55) * 340))
        is_inv = state in tomography["structural_invariants"]
        col = RED if is_inv else CYAN
        objects.extend([
            _text(f"p2-st-{idx}", [738, by + 16], f"{state:<16}", 12, TEXT),
            _rectangle(f"p2-bar-{idx}", [885, by + 2, 885 + bar_w, by + 22], col, col, 1),
            _text(f"p2-val-{idx}", [895 + bar_w, by + 17], f"P={score:.3f} {'INV' if is_inv else ''}", 12, GOLD if is_inv else MUTED),
        ])
    objects.append(
        _text(
            "p2-cap",
            [734, 498],
            f"Invariants (tau>={tomography['invariant_tau']:.2f}): {', '.join(tomography['structural_invariants']) or 'none'}",
            12,
            GOLD,
        )
    )

    # Panel 3: Full 26s A_tau(p_t) Trajectory Plot inside GEM Scene
    objects.extend([
        _text("p3-title", [48, 578], "03 / LIVE KLOSTER ACCESSIBLE VOLUME TRAJECTORY  A_tau(p_t) = sum_x 1[p_t(x) > tau]", 16, CYAN),
        _text("p3-sub", [48, 604], "Cyan: A_0.004(p_t) [0..140]  ·  Gold: A_0.010(p_t) [0..45]  ·  Red highlight: Botanical Plates (4s..18s) & Fig. 30 (15s)", 12, MUTED),
    ])
    gx0, gy0, gx1, gy1 = 92, 630, 1330, 868
    objects.append(_rectangle("p3-grid", [gx0, gy0, gx1, gy1], "#294058", "#0c1420", 1))
    # Shaded botanical plate region (4s..18s)
    n_eps = max(1, len(per_sec_a010) - 1)
    bx0 = gx0 + (4.0 / n_eps) * (gx1 - gx0)
    bx1 = gx0 + (18.0 / n_eps) * (gx1 - gx0)
    objects.append(_rectangle("p3-plates-band", [bx0, gy0 + 1, bx1, gy1 - 1], "#243a4d", "#112233", 1))
    # Fig. 30 vertical marker at t=15s
    fx = gx0 + (15.0 / n_eps) * (gx1 - gx0)
    objects.append(_line("p3-fig30-line", [fx, gy0], [fx, gy1], RED, 2))
    objects.append(_text("p3-fig30-lbl", [fx + 6, gy0 + 20], "FIG. 30 (15s)", 12, RED))

    # Plot A_0.004 (scaled to 0..160) and A_0.010 (scaled to 0..45)
    pts_004 = [
        [gx0 + (t / n_eps) * (gx1 - gx0), gy1 - min(1.0, v / 160.0) * (gy1 - gy0 - 14) - 6]
        for t, v in enumerate(per_sec_a004)
    ]
    pts_010 = [
        [gx0 + (t / n_eps) * (gx1 - gx0), gy1 - min(1.0, v / 48.0) * (gy1 - gy0 - 14) - 6]
        for t, v in enumerate(per_sec_a010)
    ]
    objects.append(_polyline("p3-curve-004", pts_004, CYAN, 2))
    objects.append(_polyline("p3-curve-010", pts_010, GOLD, 3))
    for sec_mark in (0, 5, 10, 15, 20, 25):
        mx = gx0 + (min(sec_mark, n_eps) / n_eps) * (gx1 - gx0)
        objects.append(_text(f"p3-t-{sec_mark}", [mx - 10, gy1 + 20], f"{sec_mark}s", 12, MUTED))
    objects.append(
        _text(
            "p3-stats",
            [48, 912],
            f"A_0.010 plates mean={np.mean(per_sec_a010[4:19]):.1f} vs room mean={np.mean(per_sec_a010[20:]):.1f}  ·  "
            f"Fig.30 A_0.010={per_sec_a010[15]}  ·  H1={per_sec_h1[15]:.2f}b  ·  H2={per_sec_h2[15]:.2f}b",
            13,
            GOLD,
        )
    )

    objects.extend(hud_stamp_objects("flowers", 1062, 18, chiasm_fig40["future_accessible_volume"], tau_chiasm, chiasm_fig40["presence_glyph"]))
    objects.append(_text("footer", [28, 968], "Flowers for Zoe.mp4 · GEM Causal Chiasm + Kloster A_tau(p) · 0 cloud tokens · executed=False", 13, MUTED))

    scene = Scene.from_dict({
        "schema_version": 1,
        "id": "flowers-for-zoe-chiasm",
        "title": "Flowers for Zoe · Causal Chiasm & Filtration Tomography",
        "canvas": {"width": width, "height": height},
        "objects": objects,
        "constraints": [{"type": "inside_canvas", "object": "*"}],
    })

    svg_path = CHIASM_DIR / "flowers_for_zoe_chiasm.svg"
    png_path = CHIASM_DIR / "flowers_for_zoe_chiasm.png"
    write_svg(scene, svg_path, width=1400)
    subprocess.run(["rsvg-convert", "-w", "1400", "-o", str(png_path), str(svg_path)], check=True)

    report: dict[str, Any] = {
        "source_video": str(SRC_VIDEO),
        "contract": CHIASM_CONTRACT,
        "equation": "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]",
        "tonal_states": list(TONAL_STATES),
        "episode_count": len(episodes_norm),
        "fig40_nexus_second": 15,
        "fig40_state_distribution": fig40_now,
        "chiasm_fig40_nexus": chiasm_fig40,
        "chiasm_plates_vs_room": chiasm_plates_vs_room,
        "persistent_filtration_tomography": tomography,
        "per_second_luminance_metrics": [
            {
                "sec": t,
                "A_0.004": per_sec_a004[t],
                "A_0.010": per_sec_a010[t],
                "momentum_0.010": (per_sec_a010[t] - per_sec_a010[t - 1]) if t > 0 else 0,
                "shannon_H1": round(per_sec_h1[t], 4),
                "renyi_H2": round(per_sec_h2[t], 4),
            }
            for t in range(len(per_sec_a010))
        ],
        "scene_sha256": scene.digest(),
        "svg_path": str(svg_path),
        "png_path": str(png_path),
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["report_sha256"] = hashlib.sha256(canonical).hexdigest()
    report_path = CHIASM_DIR / "flowers_for_zoe_chiasm_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report, svg_path, png_path


def render_overlay_video() -> tuple[dict[str, Any], Path]:
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    fps = 24
    vid_w, vid_h = 406, 720
    out_w, out_h = 1280, 720

    print("Decoding source video at 24fps (406x720) for frame-accurate A_tau(p_t)...")
    raw_bytes = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(SRC_VIDEO),
        "-vf", f"fps={fps},scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ])
    frame_size = vid_w * vid_h * 3
    n_frames = len(raw_bytes) // frame_size
    frames = np.frombuffer(raw_bytes[: n_frames * frame_size], dtype=np.uint8).reshape(n_frames, vid_h, vid_w, 3)
    print(f"Decoded {n_frames} frames ({n_frames / fps:.2f}s).")

    # Compute per-frame metrics
    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    # Also collect 1-second episode distributions for Chiasm
    episodes_8: list[dict[str, float]] = []
    per_sec_a010: list[int] = []
    per_sec_a004: list[int] = []
    per_sec_h1: list[float] = []
    per_sec_h2: list[float] = []

    for i in range(n_frames):
        # Fast subsampled luminance (every 2nd pixel -> 73k samples/frame, ultra-accurate & fast)
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
        m4_arr[i] = quartic_purity_m4(p)

        if i % fps == 0:
            episodes_8.append(luminance_to_8state(p))
            per_sec_a010.append(int(a010[i]))
            per_sec_a004.append(int(a004[i]))
            per_sec_h1.append(float(h1_arr[i]))
            per_sec_h2.append(float(h2_arr[i]))

    print("Running GEM Causal Chiasm & Persistent Filtration Tomography...")
    report, svg_path, png_path = run_chiasm_analysis(
        episodes_8, per_sec_a010, per_sec_a004, per_sec_h1, per_sec_h2
    )
    print(f"Chiasm SVG: {svg_path} | PNG: {png_path} | sha256={report['report_sha256'][:14]}...")

    # Pre-build static dashboard canvas background (874 x 720)
    f_title = _load_font(20, bold=True)
    f_eq = _load_font(15, bold=True)
    f_med = _load_font(15, bold=False)
    f_big = _load_font(24, bold=True)
    f_sm = _load_font(12, bold=False)
    f_sm_b = _load_font(12, bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)

    rx0 = vid_w + 14  # 420
    rx1 = out_w - 16  # 1264

    # Header card
    dr.rounded_rectangle([rx0, 12, rx1, 96], radius=10, fill=(16, 23, 35), outline=(52, 78, 108), width=2)
    dr.text((rx0 + 16, 20), "FLOWERS FOR ZOE  ·  KLOSTER OPERATIONAL METACOGNITION", fill=(235, 194, 104), font=f_title)
    dr.text((rx0 + 16, 48), "A_tau(p) = |{x in X : p(x) > tau}| = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 16, 72), "Ames & Correll · Orchids of Guatemala and Belize · GEM Chiasm Live Telemetry", fill=(150, 168, 190), font=f_sm)

    # KPI boxes row (y: 108..184)
    kpi_labels = [
        ("A_0.004(p)", (94, 218, 238)),
        ("A_0.010(p)", (242, 196, 92)),
        ("M_0.01 (dA/dt)", (244, 106, 126)),
        ("H1 / H2 (bits)", (168, 226, 142)),
        ("M4^(1/4) PURITY", (195, 162, 255)),
    ]
    kpi_w = (rx1 - rx0 - 4 * 10) // 5
    kpi_boxes: list[tuple[int, int, int, int]] = []
    for idx, (lbl, col) in enumerate(kpi_labels):
        bx0 = rx0 + idx * (kpi_w + 10)
        bx1 = bx0 + kpi_w
        kpi_boxes.append((bx0, 108, bx1, 184))
        dr.rounded_rectangle([bx0, 108, bx1, 184], radius=8, fill=(16, 23, 35), outline=(44, 62, 86), width=1)
        dr.text((bx0 + 10, 116), lbl, fill=col, font=f_sm_b)

    # Timeline plot card (y: 196..450)
    tx0, ty0, tx1, ty1 = rx0, 196, rx1, 452
    dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((tx0 + 14, ty0 + 8), "SUPERLEVEL-SET VOLUME TRAJECTORY A_tau(p_t)  (Cyan: tau=0.004  ·  Gold: tau=0.010  ·  Ruby: tau=0.020)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + 48, ty0 + 34, tx1 - 16, ty1 - 28
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    # Shaded botanical plate region (4.0s .. 18.5s) and Fig. 40 highlight (13.8s .. 16.4s)
    total_s = n_frames / fps
    def sx(sec: float) -> int:
        return int(round(px0 + (sec / total_s) * (px1 - px0)))

    dr.rectangle([sx(4.0), py0 + 1, sx(18.5), py1 - 1], fill=(15, 31, 46))
    dr.rectangle([sx(14.5), py0 + 1, sx(16.5), py1 - 1], fill=(44, 20, 32))
    dr.text((sx(4.3), py0 + 5), "BOTANICAL PLATES", fill=(86, 165, 196), font=f_sm)
    dr.text((sx(14.6), py0 + 20), "FIG.30", fill=(255, 112, 138), font=f_sm_b)

    # Horizontal grid lines & Y axis labels for A_0.010 (0..50)
    for val in (0, 15, 30, 45):
        gy = int(round(py1 - (val / 50.0) * (py1 - py0 - 8) - 4))
        dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
        dr.text((tx0 + 12, gy - 6), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)
    for sec_tick in (0, 5, 10, 15, 20, 25):
        if sec_tick <= total_s:
            gx = sx(sec_tick)
            dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
            dr.text((gx - 8, py1 + 6), f"{sec_tick}s", fill=(128, 146, 168), font=f_sm)

    # Faint full-clip ghost curves so viewer sees overall arc ahead of playhead
    def draw_series(draw_obj: ImageDraw.ImageDraw, vals: np.ndarray, ymax: float, col: tuple[int, int, int], end_idx: int, width_px: int = 2) -> None:
        if end_idx < 1:
            return
        pts = [
            (
                int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in range(0, end_idx + 1, 2)
        ]
        if len(pts) >= 2:
            draw_obj.line(pts, fill=col, width=width_px)

    draw_series(dr, a004, 180.0, (24, 62, 74), n_frames - 1, 1)
    draw_series(dr, a010, 50.0, (78, 64, 30), n_frames - 1, 1)

    # Bottom panel: Live 256-bin Luminance Probability Distribution p_t(x) + threshold line tau=0.010 (y: 464..706)
    hx0, hy0, hx1, hy1 = rx0, 464, rx1, 708
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE DISTRIBUTION p_t(x)  (|X| = 256)  ·  Gold bars: p_t(x) > tau = 0.010  (counted in A_tau)", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + 48, hy0 + 34, hx1 - 16, hy1 - 28
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    # Threshold line tau = 0.010 on Y range [0, 0.040]
    p_ymax = 0.040
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    for xtick, lbl in ((0, "0 (ink)"), (64, "64"), (128, "128"), (192, "192"), (255, "255 (cream)")):
        gx = int(round(hpx0 + (xtick / 255.0) * (hpx1 - hpx0)))
        dr.text((max(hpx0, min(hpx1 - 60, gx - 12)), hpy1 + 6), lbl, fill=(128, 146, 168), font=f_sm)
    for pv in (0.00, 0.01, 0.02, 0.03, 0.04):
        gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
        dr.text((hx0 + 6, gy - 6), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

    out_mp4 = VIDEO_DIR / "flowers_for_zoe_a_tau_overlay.mp4"
    print(f"Rendering {n_frames} composited frames -> {out_mp4} (with original audio)...")
    enc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
            "-i", str(SRC_VIDEO),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
            str(out_mp4),
        ],
        stdin=subprocess.PIPE,
    )
    assert enc.stdin is not None

    bar_w = (hpx1 - hpx0) / 256.0
    sample_preview_path = VIDEO_DIR / "overlay_frame_fig40_preview.png"

    for i in range(n_frames):
        sec = i / fps
        canvas = bg.copy()
        # Paste portrait video frame on left
        vframe = Image.fromarray(frames[i])
        canvas.paste(vframe, (0, 0))
        d = ImageDraw.Draw(canvas)

        # Left video top badge
        plbl, pcol = phase_label(sec)
        d.rounded_rectangle([10, 12, vid_w - 10, 50], radius=8, fill=(10, 14, 22), outline=pcol, width=2)
        d.text((22, 23), f"{sec:05.2f}s  ·  {plbl}", fill=pcol, font=f_sm_b)

        # Left video bottom HUD badge
        d.rounded_rectangle([10, out_h - 48, vid_w - 10, out_h - 10], radius=8, fill=(10, 14, 22), outline=(94, 218, 238), width=1)
        d.text((22, out_h - 36), f"A_0.010 = {a010[i]:>2d}/256   H1 = {h1_arr[i]:.2f}b   H2 = {h2_arr[i]:.2f}b", fill=(235, 240, 245), font=f_sm_b)

        # KPI values
        mom = int(a010[i] - a010[max(0, i - fps)])
        kpi_vals = [
            (f"{a004[i]:>3d}", (94, 218, 238)),
            (f"{a010[i]:>3d}", (242, 196, 92)),
            (f"{mom:+3d}/s", (244, 106, 126) if mom >= 0 else (94, 218, 238)),
            (f"{h1_arr[i]:.2f}/{h2_arr[i]:.2f}", (168, 226, 142)),
            (f"{m4_arr[i]:.4f}", (195, 162, 255)),
        ]
        for (bx0, by0, bx1, by1), (val_s, col) in zip(kpi_boxes, kpi_vals):
            d.text((bx0 + 10, by0 + 36), val_s, fill=col, font=f_big if len(val_s) <= 6 else f_med)

        # Active timeline curves up to current frame i
        draw_series(d, a004, 180.0, (86, 212, 232), i, 2)
        draw_series(d, a010, 50.0, (242, 196, 92), i, 3)
        draw_series(d, a020, 50.0, (244, 106, 126), i, 2)

        # Glowing playhead
        cur_x = int(round(px0 + (i / max(1, n_frames - 1)) * (px1 - px0)))
        d.line([(cur_x, py0), (cur_x, py1)], fill=(255, 255, 255), width=2)
        cur_y = int(round(py1 - min(1.0, float(a010[i]) / 50.0) * (py1 - py0 - 8) - 4))
        d.ellipse([cur_x - 5, cur_y - 5, cur_x + 5, cur_y + 5], fill=(242, 196, 92), outline=(255, 255, 255), width=2)

        # Live 256-bin histogram bars (highlight bins strictly > 0.010 in gold!)
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

        # Dashed threshold line tau = 0.010
        for dx in range(hpx0, hpx1, 12):
            d.line([(dx, tau_y), (min(hpx1, dx + 6), tau_y)], fill=(244, 106, 126), width=2)
        d.text((hpx1 - 196, tau_y - 16), f"tau = 0.010  ->  A_tau = {a010[i]}", fill=(244, 106, 126), font=f_sm_b)

        if i == int(15.0 * fps):
            canvas.save(sample_preview_path)

        enc.stdin.write(canvas.tobytes())

    enc.stdin.close()
    rc = enc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg encoder failed with exit code {rc}")
    print(f"Overlay video complete: {out_mp4} ({out_mp4.stat().st_size / 1e6:.2f} MB)")
    return report, out_mp4


if __name__ == "__main__":
    rep, mp4 = render_overlay_video()
    print("SUMMARY:", json.dumps({
        "chiasm_fig40_glyph": rep["chiasm_fig40_nexus"]["presence_glyph"],
        "chiasm_fig40_past_A": rep["chiasm_fig40_nexus"]["past_accessible_volume"],
        "chiasm_fig40_future_A": rep["chiasm_fig40_nexus"]["future_accessible_volume"],
        "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        "overlay_mp4": str(mp4),
    }, indent=2))
