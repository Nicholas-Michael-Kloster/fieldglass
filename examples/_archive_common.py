"""Shared Fieldglass archive builder utilities for Specimens #4-#9."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Sequence

from xml.sax.saxutils import escape as _xml_escape

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fieldglass.metrics import (
    CONTRACT as CHIASM_CONTRACT,
    TONAL_STATES,
    a_tau,
    causal_chiasm,
    luminance_to_8state as lum_to_8state,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4 as quartic_m4,
    renyi_h2,
    shannon_h1,
)
from fieldglass.plate import clean_illumination, ink_to_braille_lines, save_braille_bundle

BACKGROUND = "#0b111b"
PANEL = "#121b2a"
CYAN = "#5edaf0"
GOLD = "#f2c45c"
RED = "#f46a7e"
TEXT = "#e8eef5"
MUTED = "#90a4bc"


def _svg_rect(x0: float, y0: float, x1: float, y1: float, stroke: str, fill: str, sw: float = 1.0) -> str:
    return f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def _svg_line(p0: Sequence[float], p1: Sequence[float], stroke: str, sw: float = 1.5) -> str:
    return f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="{stroke}" stroke-width="{sw}"/>'


def _svg_polyline(pts: Sequence[Sequence[float]], stroke: str, sw: float = 2.0) -> str:
    pstr = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{pstr}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>'


def _svg_text(pos: Sequence[float], text: str, size: float, fill: str, weight: str = "600") -> str:
    return f'<text x="{pos[0]:.1f}" y="{pos[1]:.1f}" fill="{fill}" font-family="DejaVu Sans Mono, monospace" font-size="{size:.1f}" font-weight="{weight}">{_xml_escape(text)}</text>'


def _svg_diamond(center: Sequence[float], r: float, color: str) -> list[str]:
    cx, cy = center
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
    pts2 = [(cx, cy - r * 0.58), (cx + r * 0.58, cy), (cx, cy + r * 0.58), (cx - r * 0.58, cy), (cx, cy - r * 0.58)]
    return [
        _svg_polyline(pts, color, 2.5),
        _svg_polyline(pts2, GOLD, 1.8),
        _svg_line((cx - r, cy), (cx + r, cy), CYAN, 1.2),
        _svg_line((cx, cy - r), (cx, cy + r), CYAN, 1.2),
    ]


def _svg_hud_stamp(x: float, y: float, vol: int, tau: float, glyph: str) -> list[str]:
    return [
        _svg_rect(x, y, x + 310, y + 60, CYAN, "#0f1928", 1.5),
        _svg_text((x + 14, y + 26), f"A_{tau:.2f}(p) = {vol}   GLYPH: {glyph}", 14, GOLD, "700"),
        _svg_text((x + 14, y + 48), "FIELDGLASS LOCAL TELEMETRY · 0 TOK", 11, CYAN, "500"),
    ]


def load_font(size: int, bold: bool = False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    return ImageFont.truetype(p, size) if Path(p).is_file() else ImageFont.load_default()


def sharp_score(im: Image.Image) -> float:
    g = im.convert("L")
    g.thumbnail((640, 1138))
    return float(ndimage.laplace(np.asarray(g, dtype=np.float32)).var())


def extract_plate(
    src_vid: Path,
    out_jpg: Path,
    *,
    start_sec: float,
    window_sec: float = 2.0,
    sample_fps: int = 4,
    rotate_ccw: int = 0,
    crop_box: tuple[float, float, float, float] | None = None,
    max_dim: int = 1600,
) -> tuple[float, Path]:
    """Find sharpest frame in [start_sec, start_sec + window_sec] and save crisp web-ready JPEG."""
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        cdir = Path(tmp)
        subprocess.run([
            "ffmpeg", "-v", "error", "-ss", f"{start_sec:.2f}", "-t", f"{max(0.25, window_sec):.2f}",
            "-i", str(src_vid), "-vf", f"fps={sample_fps},scale=720:-1", "-q:v", "3",
            str(cdir / "f_%03d.jpg"),
        ], check=True)
        cands = sorted(cdir.glob("f_*.jpg"))
        if cands:
            best = max(cands, key=lambda p: sharp_score(Image.open(p)))
            best_ts = start_sec + cands.index(best) / float(sample_fps)
        else:
            best_ts = start_sec

        raw_png = cdir / "best.png"
        subprocess.run([
            "ffmpeg", "-v", "error", "-ss", f"{best_ts:.3f}", "-i", str(src_vid),
            "-frames:v", "1", "-y", str(raw_png),
        ], check=True)
        with Image.open(raw_png) as im:
            rgb = im.convert("RGB")
            if rotate_ccw == 90:
                rgb = rgb.transpose(Image.Transpose.ROTATE_90)
            elif rotate_ccw == 180:
                rgb = rgb.transpose(Image.Transpose.ROTATE_180)
            elif rotate_ccw == 270:
                rgb = rgb.transpose(Image.Transpose.ROTATE_270)
            if crop_box is not None:
                w, h = rgb.size
                x0, y0, x1, y1 = crop_box
                rgb = rgb.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
            rgb.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            rgb.save(out_jpg, quality=90, optimize=True)
    return best_ts, out_jpg


def make_contact_sheet(
    tiles: Sequence[tuple[str, Path]],
    out_jpg: Path,
    cols: int = 3,
    tile_w: int = 420,
    tile_h: int = 560,
) -> Path:
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (12, 15, 22))
    sd = ImageDraw.Draw(sheet)
    f_lbl = load_font(12, bold=True)
    for idx, (label, pp) in enumerate(tiles):
        im = Image.open(pp).convert("RGB")
        im.thumbnail((tile_w - 14, tile_h - 36), Image.Resampling.LANCZOS)
        r, c = divmod(idx, cols)
        ox = c * tile_w + (tile_w - im.width) // 2
        oy = r * tile_h + 28 + (tile_h - 36 - im.height) // 2
        sheet.paste(im, (ox, oy))
        sd.text((c * tile_w + 10, r * tile_h + 8), label[:42], fill=(242, 196, 92), font=f_lbl)
    sheet.save(out_jpg, quality=90, optimize=True)
    return out_jpg


def build_svg_and_braille(
    plate_path: Path,
    assets_dir: Path,
    stem: str,
    *,
    title: str,
    subtitle: str,
    crop_box: tuple[float, float, float, float] | None = None,
    sigma: float = 42.0,
    paper_cutoff: float = 0.925,
    ink_floor: float = 0.40,
    gamma: float = 1.15,
    levels: tuple[float, float, float] = (0.085, 0.22, 1.2),
    colors: tuple[str, str] = ("#6b6356", "#181a1f"),
    bg_hex: str = "#f6f1e4",
    braille_cols: int = 72,
    edge_hybrid: bool = False,
) -> dict[str, str]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(plate_path).convert("RGB")
    if crop_box is not None:
        w, h = im.size
        x0, y0, x1, y1 = crop_box
        im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))

    if edge_hybrid:
        g = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
        sx = ndimage.sobel(g, axis=1)
        sy = ndimage.sobel(g, axis=0)
        edges = np.hypot(sx, sy)
        edges = np.clip(edges / max(1e-4, float(np.percentile(edges, 96))), 0.0, 1.0)
        ink = np.clip(edges * 0.72 + (1.0 - g) * 0.35 - 0.14, 0.0, 1.0)
        paper_rgb = np.array([246.0, 241.0, 228.0], dtype=np.float32)
        ink_rgb = np.array([24.0, 26.0, 31.0], dtype=np.float32)
        archival = Image.fromarray((paper_rgb * (1.0 - ink[..., None]) + ink_rgb * ink[..., None]).clip(0, 255).astype(np.uint8))
        bw = Image.fromarray(((1.0 - ink) * 255.0).clip(0, 255).astype(np.uint8))
    else:
        ink, archival, bw = clean_illumination(im, sigma=sigma, paper_cutoff=paper_cutoff, ink_floor=ink_floor, gamma=gamma)

    mask = ink > 0.14
    lab, nc = ndimage.label(mask)
    cleaned = np.where((ndimage.sum(mask, lab, range(1, nc + 1)) >= 5)[lab - 1] & mask, ink, 0.0) if nc else ink

    arch_path = assets_dir / f"{stem}_archival.png"
    arch_small = archival.copy()
    arch_small.thumbnail((1200, 1600), Image.Resampling.LANCZOS)
    arch_small.save(arch_path, optimize=True)

    ah, aw = cleaned.shape
    vw = 640
    vh = max(64, int(round(ah * (vw / max(1, aw)))))
    sm = ndimage.gaussian_filter(
        np.asarray(
            Image.fromarray((cleaned * 255).clip(0, 255).astype(np.uint8)).resize((vw, vh), Image.Resampling.BOX),
            dtype=np.float32,
        ) / 255.0,
        sigma=0.55,
    )

    aspect = vh / float(vw)
    fig_w = 8.4 if aspect >= 1.0 else 9.6
    fig_h = max(5.8, min(11.4, fig_w * aspect + 1.45))

    svg_path = assets_dir / f"{stem}.svg"
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=100, facecolor=bg_hex)
    ax = fig.add_axes([0.05, 0.125, 0.90, 0.825], facecolor=bg_hex)
    ax.contourf(sm, levels=list(levels), colors=list(colors))
    ax.set_xlim(0, vw - 1)
    ax.set_ylim(vh - 1, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patches.append(plt.Rectangle((0.024, 0.022), 0.952, 0.956, fill=False, edgecolor="#8c7f68", linewidth=1.2, transform=fig.transFigure))
    fig.patches.append(plt.Rectangle((0.032, 0.030), 0.936, 0.940, fill=False, edgecolor="#c4b89f", linewidth=0.6, transform=fig.transFigure))
    fig.text(0.5, 0.074, title, ha="center", va="center", fontsize=11.0, fontweight="bold", family="serif", color="#181b20")
    fig.text(0.5, 0.046, subtitle, ha="center", va="center", fontsize=8.0, style="italic", family="serif", color="#4e5259")
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)

    svg_prev = assets_dir / f"{stem}_svg_preview.png"
    subprocess.run(["rsvg-convert", "-w", "1000", "-o", str(svg_prev), str(svg_path)], check=True)

    br_lines = ink_to_braille_lines(np.clip(cleaned * 1.28, 0.0, 1.0), cols=braille_cols)
    br = save_braille_bundle(
        br_lines,
        assets_dir,
        stem,
        title=title,
        subtitle=f"{subtitle} · {braille_cols}-col Braille",
    )
    return {
        "svg": str(svg_path),
        "svg_preview": str(svg_prev),
        "archival": str(arch_path),
        "braille_txt": br["txt"],
        "braille_json": br["json"],
        "braille_preview": br["preview_png"],
    }


def write_chiasm_bundle(
    chiasm_dir: Path,
    slug: str,
    *,
    title: str,
    subtitle: str,
    nexus_label: str,
    footer_label: str,
    episodes_8: list[dict[str, float]],
    ep_a004: list[int],
    ep_a010: list[int],
    ep_times_s: list[float],
    nexus_ep: int,
    h1_mean: float,
    h2_mean: float,
    duration_sec: float,
    hud_prefix: str = "fg",
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chiasm_dir.mkdir(parents=True, exist_ok=True)
    nexus_ep = max(1, min(len(episodes_8) - 1, nexus_ep))
    past_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes_8[:nexus_ep]])) for s in TONAL_STATES})
    fut_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes_8[nexus_ep:]])) for s in TONAL_STATES})
    chiasm_res = causal_chiasm(past_avg, fut_avg, tau=0.10, horizon=5)
    tomo_res = persistent_filtration_tomography(
        episodes_8,
        thresholds=(0.04, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50),
        invariant_tau=0.14,
    )

    nexus_sec = ep_times_s[nexus_ep]
    w_svg, h_svg = 1400, 1000
    svg_elems: list[str] = [
        _svg_rect(0, 0, w_svg, h_svg, BACKGROUND, BACKGROUND, 0),
        _svg_rect(28, 96, 686, 520, RED, PANEL, 2),
        _svg_rect(714, 96, 1372, 520, "#294058", PANEL, 1),
        _svg_rect(28, 544, 1372, 926, "#294058", PANEL, 1),
        _svg_text((28, 44), title, 21, RED, "700"),
        _svg_text((28, 74), subtitle, 13.5, GOLD, "600"),
    ]
    cx, cy = 357, 308
    mm_n, ss_n = divmod(int(nexus_sec), 60)
    mm_d, ss_d = divmod(int(duration_sec), 60)
    svg_elems.extend([
        _svg_text((48, 128), f"01 / CAUSAL CHIASM AT NEXUS ({mm_n}:{ss_n:02d})", 15.5, CYAN, "700"),
        _svg_text((52, 164), f"PAST (0:00-{mm_n}:{ss_n:02d}) A_0.10 = {chiasm_res['past_accessible_volume']}", 13, CYAN),
        _svg_text((410, 164), f"FUTURE ({mm_n}:{ss_n:02d}-{mm_d}:{ss_d:02d}) A_0.10 = {chiasm_res['future_accessible_volume']}", 13, GOLD),
    ])
    for dy, cl, cr in [(-92, CYAN, GOLD), (-44, CYAN, RED), (44, GOLD, CYAN), (92, RED, GOLD)]:
        svg_elems.append(_svg_polyline([[88, cy + dy], [cx - 48, cy + dy * 0.35], [cx, cy]], cl, 2))
        svg_elems.append(_svg_polyline([[cx, cy], [cx + 48, cy - dy * 0.35], [626, cy - dy]], cr, 2))
    svg_elems.extend(_svg_diamond((cx, cy), 32, RED))
    ei = chiasm_res["effective_information_bits"] or 0.0
    svg_elems.extend([
        _svg_text((max(56, cx - len(nexus_label) * 4), cy + 56), nexus_label[:32], 13, GOLD, "700"),
        _svg_text((48, 478), f"Nexus EI = {ei:.4f} bits · shift = {chiasm_res['chiasm_shift']:+d} · glyph = {chiasm_res['presence_glyph']} · boxed_in = {chiasm_res['future_boxed_in']}", 12.5, TEXT),
        _svg_text((48, 502), f"{len(episodes_8)} episodes · 0 cloud tokens · SHA-256 sealed local telemetry", 12, MUTED, "500"),
    ])

    svg_elems.append(_svg_text((734, 128), f"02 / PERSISTENT FILTRATION TOMOGRAPHY ({len(episodes_8)} EPISODES)", 15.5, CYAN, "700"))
    svg_elems.append(_svg_text((734, 154), "Mean survival threshold P(x) across tonal repertoire", 12, MUTED, "500"))
    for idx, (state, score) in enumerate(sorted(tomo_res["persistence_scores"].items(), key=lambda kv: -kv[1])):
        by = 188 + idx * 36
        bw = max(8, int(min(1.0, score / 0.55) * 340))
        is_inv = state in tomo_res["structural_invariants"]
        col = RED if is_inv else CYAN
        svg_elems.extend([
            _svg_text((738, by + 16), state, 12, TEXT),
            _svg_rect(885, by + 2, 885 + bw, by + 22, col, col, 1),
            _svg_text((895 + bw, by + 17), f"P={score:.3f} {'INV' if is_inv else ''}", 12, GOLD if is_inv else MUTED),
        ])
    svg_elems.append(_svg_text((734, 498), f"Invariants (tau>=0.14): {', '.join(tomo_res['structural_invariants']) or 'none'}", 12, GOLD))

    gx0, gy0, gx1, gy1 = 92, 628, 1330, 868
    svg_elems.extend([
        _svg_text((48, 578), "03 / LIVE KLOSTER ACCESSIBLE VOLUME TRAJECTORY  A_tau(p_t)", 15.5, CYAN, "700"),
        _svg_text((48, 604), f"Cyan: A_0.004(p_t) [0..180]  ·  Gold: A_0.010(p_t) [0..60]  ·  Ruby marker: {nexus_label}", 12, MUTED, "500"),
        _svg_rect(gx0, gy0, gx1, gy1, "#294058", "#0c1420", 1),
    ])
    n_ep = max(1, len(ep_a010) - 1)
    fx = gx0 + (nexus_ep / n_ep) * (gx1 - gx0)
    svg_elems.append(_svg_line((fx, gy0), (fx, gy1), RED, 2))
    svg_elems.append(_svg_text((min(gx1 - 190, fx + 6), gy0 + 20), f"NEXUS ({mm_n}:{ss_n:02d})", 12, RED, "700"))
    svg_elems.append(_svg_polyline([[gx0 + (t / n_ep) * (gx1 - gx0), gy1 - min(1.0, v / 180.0) * (gy1 - gy0 - 14) - 6] for t, v in enumerate(ep_a004)], CYAN, 2))
    svg_elems.append(_svg_polyline([[gx0 + (t / n_ep) * (gx1 - gx0), gy1 - min(1.0, v / 60.0) * (gy1 - gy0 - 14) - 6] for t, v in enumerate(ep_a010)], GOLD, 3))
    for k in range(6):
        frac = k / 5.0
        st = duration_sec * frac
        m_t, s_t = divmod(int(st), 60)
        mx = gx0 + frac * (gx1 - gx0)
        svg_elems.append(_svg_text((mx - 14, gy1 + 20), f"{m_t}:{s_t:02d}", 12, MUTED, "500"))
    svg_elems.append(_svg_text((48, 912), f"A_0.010 mean={np.mean(ep_a010):.1f} · max={max(ep_a010)} · min={min(ep_a010)} · H1 mean={h1_mean:.2f}b · H2 mean={h2_mean:.2f}b", 13, GOLD))
    svg_elems.extend(_svg_hud_stamp(1062, 18, chiasm_res["future_accessible_volume"], 0.10, chiasm_res["presence_glyph"]))
    svg_elems.append(_svg_text((28, 968), f"{footer_label} · 0 cloud tokens · executed=False", 13, MUTED, "500"))

    svg_text = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_svg} {h_svg}" width="{w_svg}" height="{h_svg}">\n'
        + "\n".join(svg_elems)
        + "\n</svg>\n"
    )
    ch_svg = chiasm_dir / f"{slug}_chiasm.svg"
    ch_png = chiasm_dir / f"{slug}_chiasm.png"
    ch_svg.write_text(svg_text, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", "1400", "-o", str(ch_png), str(ch_svg)], check=True)
    scene_sha = hashlib.sha256(svg_text.encode("utf-8")).hexdigest()

    report: dict[str, Any] = {
        "slug": slug,
        "title": title,
        "contract": CHIASM_CONTRACT,
        "equation": "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]",
        "duration_sec": round(duration_sec, 2),
        "episode_count": len(episodes_8),
        "nexus_sec": round(nexus_sec, 2),
        "chiasm_nexus": chiasm_res,
        "persistent_filtration_tomography": tomo_res,
        "a_004_mean": round(float(np.mean(ep_a004)), 2),
        "a_010_mean": round(float(np.mean(ep_a010)), 2),
        "h1_mean_bits": round(h1_mean, 3),
        "h2_mean_bits": round(h2_mean, 3),
        "scene_sha256": scene_sha,
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    if extra_meta:
        report.update(extra_meta)
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    (chiasm_dir / f"{slug}_chiasm_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def render_telemetry_overlay_from_video(
    clean_input_mp4: Path,
    out_mp4: Path,
    poster_png: Path,
    *,
    header_title: str,
    header_sub: str,
    phase_fn: Callable[[float], tuple[str, tuple[int, int, int]]],
    nexus_band: tuple[float, float, str] | None = None,
    out_w: int = 1280,
    out_h: int = 720,
    fps: int = 15,
    crf: int = 26,
    audio_bitrate: str = "80k",
    keep_audio: bool = True,
    poster_sec: float | None = None,
    episode_interval_s: float = 5.0,
    time_scale: float = 1.0,
) -> dict[str, Any]:
    """Stream-process a clean input video (1x real-time or pre-sped timelapse) into a live Kloster A_tau(p_t) MP4.

    Two-pass low-memory streaming so even 15-minute videos use minimal RAM and encode cleanly.
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    vid_w = int(round(out_h * 9.0 / 16.0))
    if vid_w % 2:
        vid_w += 1
    vid_h = out_h

    # Pass 1: compute frame metrics in streaming chunks (tiny 120x214 decode for instant speed!)
    p1_w, p1_h = 128, 226
    dec1 = subprocess.Popen([
        "ffmpeg", "-v", "error", "-i", str(clean_input_mp4),
        "-vf", f"fps={fps},scale={p1_w}:{p1_h}",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ], stdout=subprocess.PIPE)
    assert dec1.stdout is not None
    fsize1 = p1_w * p1_h
    a004_l, a010_l, a020_l, h1_l, h2_l, m4_l, hists_l = [], [], [], [], [], [], []
    while True:
        buf = dec1.stdout.read(fsize1)
        if len(buf) < fsize1:
            break
        lum = np.frombuffer(buf, dtype=np.uint8)
        counts = np.bincount(lum, minlength=256).astype(np.float64)
        p = counts / counts.sum()
        a004_l.append(a_tau(p, 0.004))
        a010_l.append(a_tau(p, 0.010))
        a020_l.append(a_tau(p, 0.020))
        h1_l.append(shannon_h1(p))
        h2_l.append(renyi_h2(p))
        m4_l.append(quartic_m4(p))
        hists_l.append(p.astype(np.float32))
    dec1.stdout.close()
    dec1.wait()

    n_frames = len(a004_l)
    if n_frames == 0:
        raise RuntimeError(f"Decoded 0 frames from {clean_input_mp4}")

    a004 = np.array(a004_l, dtype=np.int32)
    a010 = np.array(a010_l, dtype=np.int32)
    a020 = np.array(a020_l, dtype=np.int32)
    h1_arr = np.array(h1_l, dtype=np.float32)
    h2_arr = np.array(h2_l, dtype=np.float32)
    m4_arr = np.array(m4_l, dtype=np.float32)
    hists = np.stack(hists_l, axis=0)
    total_out_s = n_frames / float(fps)
    total_real_s = total_out_s * time_scale

    # Collect episodes for Chiasm
    ep_step = max(1, int(round((episode_interval_s / time_scale) * fps)))
    episodes_8, ep_a004, ep_a010, ep_times = [], [], [], []
    for idx in range(0, n_frames, ep_step):
        episodes_8.append(lum_to_8state(hists[idx]))
        ep_a004.append(int(a004[idx]))
        ep_a010.append(int(a010[idx]))
        ep_times.append((idx / float(fps)) * time_scale)

    # Pre-render static background HUD
    scale = out_h / 720.0
    def S(v: float) -> int:
        return int(round(v * scale))

    f_title = load_font(max(13, S(18)), bold=True)
    f_eq = load_font(max(11, S(14)), bold=True)
    f_med = load_font(max(11, S(14)), bold=False)
    f_big = load_font(max(16, S(22)), bold=True)
    f_sm = load_font(max(9, S(11)), bold=False)
    f_sm_b = load_font(max(10, S(12)), bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)
    rx0, rx1 = vid_w + S(14), out_w - S(16)

    dr.rounded_rectangle([rx0, S(12), rx1, S(96)], radius=S(10), fill=(16, 23, 35), outline=(52, 78, 108), width=2)
    dr.text((rx0 + S(16), S(20)), header_title, fill=(235, 194, 104), font=f_title)
    dr.text((rx0 + S(16), S(48)), "A_tau(p) = |{x in X : p(x) > tau}| = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + S(16), S(72)), header_sub, fill=(150, 168, 190), font=f_sm)

    kpi_meta = [
        ("A_0.004(p)", (94, 218, 238)),
        ("A_0.010(p)", (242, 196, 92)),
        ("M_0.01 (dA/s)", (244, 106, 126)),
        ("H1 / H2 (bits)", (168, 226, 142)),
        ("M4^(1/4) PURITY", (195, 162, 255)),
    ]
    kpi_w = (rx1 - rx0 - S(40)) // 5
    kpi_boxes = []
    for idx, (lbl, col) in enumerate(kpi_meta):
        bx0 = rx0 + idx * (kpi_w + S(10))
        bx1 = bx0 + kpi_w
        kpi_boxes.append((bx0, S(108), bx1, S(184)))
        dr.rounded_rectangle([bx0, S(108), bx1, S(184)], radius=S(8), fill=(16, 23, 35), outline=(44, 62, 86), width=1)
        dr.text((bx0 + S(8), S(116)), lbl, fill=col, font=f_sm_b)

    tx0, ty0, tx1, ty1 = rx0, S(196), rx1, S(452)
    dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=S(10), fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((tx0 + S(14), ty0 + S(8)), "SUPERLEVEL-SET VOLUME A_tau(p_t)  (Cyan: 0.004 · Gold: 0.010 · Ruby: 0.020)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + S(48), ty0 + S(34), tx1 - S(16), ty1 - S(28)
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    def sx_real(rsec: float) -> int:
        return int(round(px0 + (min(rsec, total_real_s) / max(1e-3, total_real_s)) * (px1 - px0)))

    if nexus_band is not None:
        nb0, nb1, nlbl = nexus_band
        dr.rectangle([sx_real(nb0), py0 + 1, sx_real(nb1), py1 - 1], fill=(44, 20, 32))
        dr.text((sx_real(nb0) + S(4), py0 + S(6)), nlbl, fill=(255, 112, 138), font=f_sm_b)

    for val in (0, 20, 40, 60):
        gy = int(round(py1 - (val / 65.0) * (py1 - py0 - 8) - 4))
        dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
        dr.text((tx0 + S(12), gy - S(6)), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)

    for k in range(6):
        st = total_real_s * (k / 5.0)
        gx = sx_real(st)
        mm_t, ss_t = divmod(int(st), 60)
        dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
        dr.text((gx - S(12), py1 + S(6)), f"{mm_t}:{ss_t:02d}", fill=(128, 146, 168), font=f_sm)

    # Pre-compute downsampled curve x-coords (at most ~600 points for fast drawing on 15-min videos!)
    stride = max(1, n_frames // 500)
    def build_pts(vals: np.ndarray, ymax: float, end_idx: int) -> list[tuple[int, int]]:
        ks = list(range(0, end_idx + 1, stride))
        if ks[-1] != end_idx:
            ks.append(end_idx)
        return [
            (
                int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in ks
        ]

    # Dim full-horizon preview track
    full004 = build_pts(a004, 180.0, n_frames - 1)
    full010 = build_pts(a010, 65.0, n_frames - 1)
    if len(full004) >= 2:
        dr.line(full004, fill=(24, 62, 74), width=1)
        dr.line(full010, fill=(78, 64, 30), width=1)

    hx0, hy0, hx1, hy1 = rx0, S(464), rx1, S(708)
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=S(10), fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + S(14), hy0 + S(8)), "LIVE LUMINANCE DISTRIBUTION p_t(x) (|X|=256) · Gold: p_t(x) > tau=0.010", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + S(48), hy0 + S(34), hx1 - S(16), hy1 - S(28)
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    p_ymax = 0.040
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    bar_w = (hpx1 - hpx0) / 256.0
    for pv in (0.00, 0.01, 0.02, 0.03, 0.04):
        gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
        dr.text((hx0 + S(6), gy - S(6)), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

    # Pass 2: stream full-res frames -> composite HUD -> pipe straight to libx264 encoder!
    dec2 = subprocess.Popen([
        "ffmpeg", "-v", "error", "-i", str(clean_input_mp4),
        "-vf", f"fps={fps},scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ], stdout=subprocess.PIPE)
    assert dec2.stdout is not None

    enc_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
    ]
    if keep_audio:
        enc_cmd += ["-i", str(clean_input_mp4), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", audio_bitrate, "-shortest"]
    else:
        enc_cmd += ["-an"]
    enc_cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ]
    enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)
    assert enc.stdin is not None

    fsize2 = vid_w * vid_h * 3
    if poster_sec is None:
        poster_idx = n_frames // 2
    else:
        poster_idx = max(0, min(n_frames - 1, int(round((poster_sec / time_scale) * fps))))

    for i in range(n_frames):
        buf = dec2.stdout.read(fsize2)
        if len(buf) < fsize2:
            break
        rsec = (i / float(fps)) * time_scale
        mm_r, ss_r = divmod(int(rsec), 60)
        frame_im = Image.frombytes("RGB", (vid_w, vid_h), buf)
        canvas = bg.copy()
        canvas.paste(frame_im, (0, 0))
        d = ImageDraw.Draw(canvas)

        plbl, pcol = phase_fn(rsec)
        d.rounded_rectangle([S(10), S(12), vid_w - S(10), S(46)], radius=S(8), fill=(10, 14, 22), outline=pcol, width=2)
        d.text((S(18), S(21)), f"{mm_r}:{ss_r:02d}  ·  {plbl[:26]}", fill=pcol, font=f_sm_b)
        d.rounded_rectangle([S(10), out_h - S(44), vid_w - S(10), out_h - S(10)], radius=S(8), fill=(10, 14, 22), outline=(94, 218, 238), width=1)
        d.text((S(18), out_h - S(34)), f"A_0.010={a010[i]:>2d}/256  H1={h1_arr[i]:.2f}b  H2={h2_arr[i]:.2f}b", fill=(235, 240, 245), font=f_sm_b)

        mom = int(a010[i] - a010[max(0, i - fps)])
        vals = [
            (f"{a004[i]:>3d}", (94, 218, 238)),
            (f"{a010[i]:>3d}", (242, 196, 92)),
            (f"{mom:+3d}/s", (244, 106, 126) if mom >= 0 else (94, 218, 238)),
            (f"{h1_arr[i]:.2f}/{h2_arr[i]:.2f}", (168, 226, 142)),
            (f"{m4_arr[i]:.4f}", (195, 162, 255)),
        ]
        for (bx0, by0, _, _), (val_s, col) in zip(kpi_boxes, vals):
            d.text((bx0 + S(8), by0 + S(36)), val_s, fill=col, font=f_big if len(val_s) <= 6 else f_med)

        if i >= 1:
            p004 = build_pts(a004, 180.0, i)
            p010 = build_pts(a010, 65.0, i)
            p020 = build_pts(a020, 65.0, i)
            if len(p004) >= 2:
                d.line(p004, fill=(86, 212, 232), width=2)
                d.line(p010, fill=(242, 196, 92), width=3)
                d.line(p020, fill=(244, 106, 126), width=2)
        cur_x = int(round(px0 + (i / max(1, n_frames - 1)) * (px1 - px0)))
        d.line([(cur_x, py0), (cur_x, py1)], fill=(255, 255, 255), width=2)
        cur_y = int(round(py1 - min(1.0, float(a010[i]) / 65.0) * (py1 - py0 - 8) - 4))
        d.ellipse([cur_x - 4, cur_y - 4, cur_x + 4, cur_y + 4], fill=(242, 196, 92), outline=(255, 255, 255), width=2)

        p_now = hists[i]
        # Draw histogram every 2 bins for speed & crispness
        for b in range(0, 256, 2):
            pv = float(max(p_now[b], p_now[b + 1]))
            if pv <= 0.0003:
                continue
            bx0 = int(hpx0 + b * bar_w)
            bx1 = max(bx0 + 1, int(hpx0 + (b + 2) * bar_w))
            bh_y = int(round(hpy1 - min(1.0, pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
            bar_col = (242, 196, 92) if pv > 0.010 else ((86, 198, 224) if pv > 0.004 else (58, 78, 102))
            d.rectangle([bx0, bh_y, bx1, hpy1 - 2], fill=bar_col)
        for dx in range(hpx0, hpx1, 12):
            d.line([(dx, tau_y), (min(hpx1, dx + 6), tau_y)], fill=(244, 106, 126), width=2)
        d.text((hpx1 - S(196), tau_y - S(16)), f"tau = 0.010  ->  A_tau = {a010[i]}", fill=(244, 106, 126), font=f_sm_b)

        if i == poster_idx:
            canvas.save(poster_png, optimize=True)
        enc.stdin.write(canvas.tobytes())

    dec2.stdout.close()
    dec2.wait()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"ffmpeg overlay encode failed for {out_mp4}")

    return {
        "n_frames": n_frames,
        "duration_real_s": total_real_s,
        "duration_out_s": total_out_s,
        "mp4_mb": round(out_mp4.stat().st_size / 1e6, 2),
        "episodes_8": episodes_8,
        "ep_a004": ep_a004,
        "ep_a010": ep_a010,
        "ep_times": ep_times,
        "h1_mean": float(np.mean(h1_arr)),
        "h2_mean": float(np.mean(h2_arr)),
        "h1_max": float(np.max(h1_arr)),
        "a004_max": int(np.max(a004)),
        "a010_max": int(np.max(a010)),
    }
