"""Real-time Kloster A_tau(p_t) telemetry overlay video + standalone Causal Chiasm SVG dashboard."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .metrics import (
    CONTRACT,
    TONAL_STATES,
    a_tau,
    causal_chiasm,
    luminance_to_8state,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)


def _load_font(size: int, bold: bool = False):
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


def write_chiasm_svg(
    svg_path: str | Path,
    *,
    title: str,
    subtitle: str,
    chiasm: dict[str, Any],
    tomography: dict[str, Any],
    per_sec_a004: list[int],
    per_sec_a010: list[int],
    nexus_sec: int,
) -> Path:
    """Render a self-contained dark-observatory Causal Chiasm & Filtration Tomography SVG."""
    dst = Path(svg_path).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    w, h = 1400, 1000
    esc = html.escape
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        '<rect width="1400" height="1000" fill="#0b0f17"/>',
        '<rect x="28" y="96" width="658" height="424" fill="#121926" stroke="#f46a7e" stroke-width="2" rx="6"/>',
        '<rect x="714" y="96" width="658" height="424" fill="#121926" stroke="#294058" stroke-width="1.5" rx="6"/>',
        '<rect x="28" y="544" width="1344" height="382" fill="#121926" stroke="#294058" stroke-width="1.5" rx="6"/>',
        f'<text x="28" y="44" fill="#f46a7e" font-family="monospace" font-size="24" font-weight="bold">{esc(title)}</text>',
        f'<text x="28" y="74" fill="#f2c45c" font-family="monospace" font-size="14">{esc(subtitle)}</text>',
        # Top-right HUD box
        '<rect x="1062" y="18" width="310" height="64" fill="#121926" stroke="#f46a7e" stroke-width="2" rx="4"/>',
        '<polygon points="1090,34 1106,50 1090,66 1074,50" fill="none" stroke="#f46a7e" stroke-width="2"/>',
        '<polygon points="1090,42 1098,50 1090,58 1082,50" fill="#f46a7e" stroke="#f2c45c" stroke-width="1"/>',
        f'<text x="1118" y="42" fill="#f2c45c" font-family="monospace" font-size="13" font-weight="bold">FIELDGLASS HUD · {esc(chiasm["presence_glyph"])}</text>',
        f'<text x="1118" y="64" fill="#5edaf0" font-family="monospace" font-size="12">A_tau({chiasm["tau"]:.2f})={chiasm["future_accessible_volume"]} · exec=False</text>',
        # Panel 1: Causal Chiasm double-cone
        f'<text x="48" y="128" fill="#5edaf0" font-family="monospace" font-size="16" font-weight="bold">01 / CAUSAL CHIASM NEXUS (t = {nexus_sec}s)</text>',
        f'<text x="52" y="164" fill="#5edaf0" font-family="monospace" font-size="13">PAST A_tau = {chiasm["past_accessible_volume"]}</text>',
        f'<text x="456" y="164" fill="#f2c45c" font-family="monospace" font-size="13">FUTURE A_tau = {chiasm["future_accessible_volume"]}</text>',
    ]
    cx, cy = 357, 308
    for dy, col_l, col_r in ((-92, "#5edaf0", "#f2c45c"), (-44, "#5edaf0", "#f46a7e"), (44, "#f2c45c", "#5edaf0"), (92, "#f46a7e", "#f2c45c")):
        parts.append(f'<polyline points="88,{cy+dy} {cx-48},{cy+dy*0.35:.1f} {cx},{cy}" fill="none" stroke="{col_l}" stroke-width="2"/>')
        parts.append(f'<polyline points="{cx},{cy} {cx+48},{cy-dy*0.35:.1f} 626,{cy-dy}" fill="none" stroke="{col_r}" stroke-width="2"/>')
    parts.append(f'<polygon points="{cx},{cy-34} {cx+34},{cy} {cx},{cy+34} {cx-34},{cy}" fill="#0b0f17" stroke="#f46a7e" stroke-width="2.5"/>')
    parts.append(f'<text x="{cx-76}" y="{cy+58}" fill="#f2c45c" font-family="monospace" font-size="13">PRESENT NEXUS (t = {nexus_sec}s)</text>')
    ei = chiasm.get("effective_information_bits")
    ei_s = f"{ei:.4f} bits" if isinstance(ei, (int, float)) else "n/a"
    parts.append(
        f'<text x="48" y="492" fill="#eaeff5" font-family="monospace" font-size="13">'
        f'EI = {esc(ei_s)} · shift = {chiasm["chiasm_shift"]:+d} · boxed_in = {chiasm["future_boxed_in"]}</text>'
    )

    # Panel 2: Persistent Filtration Tomography bars
    parts.append(f'<text x="734" y="128" fill="#5edaf0" font-family="monospace" font-size="16" font-weight="bold">02 / PERSISTENT FILTRATION TOMOGRAPHY ({tomography["episode_count"]} EPISODES)</text>')
    parts.append('<text x="734" y="154" fill="#93a6be" font-family="monospace" font-size="12">Mean survival threshold P(x) across episode distributions</text>')
    inv_set = set(tomography["structural_invariants"])
    for idx, (state, score) in enumerate(sorted(tomography["persistence_scores"].items(), key=lambda kv: -kv[1])):
        by = 188 + idx * 36
        bar_w = max(8, int(min(1.0, score / 0.55) * 340))
        col = "#f46a7e" if state in inv_set else "#5edaf0"
        tag = " INV" if state in inv_set else ""
        parts.append(f'<text x="738" y="{by+16}" fill="#eaeff5" font-family="monospace" font-size="12">{esc(state)}</text>')
        parts.append(f'<rect x="885" y="{by+2}" width="{bar_w}" height="20" fill="{col}" rx="2"/>')
        parts.append(f'<text x="{895+bar_w}" y="{by+17}" fill="#f2c45c" font-family="monospace" font-size="12">P={score:.3f}{tag}</text>')
    parts.append(
        f'<text x="734" y="498" fill="#f2c45c" font-family="monospace" font-size="12">'
        f'Invariants (tau &gt;= {tomography["invariant_tau"]:.2f}): {esc(", ".join(tomography["structural_invariants"]) or "none")}</text>'
    )

    # Panel 3: Trajectory plot
    gx0, gy0, gx1, gy1 = 92, 628, 1330, 868
    parts.append('<text x="48" y="578" fill="#5edaf0" font-family="monospace" font-size="16" font-weight="bold">03 / KLOSTER ACCESSIBLE VOLUME TRAJECTORY  A_tau(p_t) = sum_x 1[p_t(x) &gt; tau]</text>')
    parts.append('<text x="48" y="604" fill="#93a6be" font-family="monospace" font-size="12">Cyan: A_0.004(p_t)  ·  Gold: A_0.010(p_t)  ·  Ruby marker: Nexus second</text>')
    parts.append(f'<rect x="{gx0}" y="{gy0}" width="{gx1-gx0}" height="{gy1-gy0}" fill="#090d15" stroke="#294058"/>')
    n_eps = max(1, len(per_sec_a010) - 1)
    nx = gx0 + (min(nexus_sec, n_eps) / n_eps) * (gx1 - gx0)
    parts.append(f'<line x1="{nx:.1f}" y1="{gy0}" x2="{nx:.1f}" y2="{gy1}" stroke="#f46a7e" stroke-width="2"/>')
    pts_004 = " ".join(
        f"{gx0 + (t / n_eps) * (gx1 - gx0):.1f},{gy1 - min(1.0, v / 160.0) * (gy1 - gy0 - 14) - 6:.1f}"
        for t, v in enumerate(per_sec_a004)
    )
    pts_010 = " ".join(
        f"{gx0 + (t / n_eps) * (gx1 - gx0):.1f},{gy1 - min(1.0, v / 50.0) * (gy1 - gy0 - 14) - 6:.1f}"
        for t, v in enumerate(per_sec_a010)
    )
    parts.append(f'<polyline points="{pts_004}" fill="none" stroke="#5edaf0" stroke-width="2"/>')
    parts.append(f'<polyline points="{pts_010}" fill="none" stroke="#f2c45c" stroke-width="3"/>')
    parts.append('<text x="28" y="968" fill="#93a6be" font-family="monospace" font-size="13">Fieldglass · Kloster Operational Metacognition · 0 cloud tokens · executed=False</text>')
    parts.append("</svg>")
    dst.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return dst


def render_telemetry_overlay(
    video_path: str | Path,
    out_dir: str | Path,
    *,
    title: str = "FIELDGLASS · KLOSTER OPERATIONAL METACOGNITION",
    subtitle: str = "Live A_tau(p_t) Superlevel-Set Telemetry",
    fps: int = 24,
    nexus_sec: int | None = None,
) -> dict[str, Any]:
    """Analyze a video frame-by-frame, generate Chiasm SVG/JSON, and render 1280x720 overlay MP4."""
    src = Path(video_path).expanduser().resolve()
    root = Path(out_dir).expanduser().resolve()
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    chiasm_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    vid_w, vid_h = 406, 720
    out_w, out_h = 1280, 720

    raw = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(src),
            "-vf", f"fps={fps},scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
    )
    frame_bytes = vid_w * vid_h * 3
    n_frames = len(raw) // frame_bytes
    if n_frames == 0:
        raise RuntimeError(f"Could not decode frames from {src}")
    frames = np.frombuffer(raw[: n_frames * frame_bytes], dtype=np.uint8).reshape(n_frames, vid_h, vid_w, 3)

    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    episodes: list[dict[str, float]] = []
    sec_a004: list[int] = []
    sec_a010: list[int] = []

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
        m4_arr[i] = quartic_purity_m4(p)
        if i % fps == 0:
            episodes.append(luminance_to_8state(p))
            sec_a004.append(int(a004[i]))
            sec_a010.append(int(a010[i]))

    mid = nexus_sec if nexus_sec is not None else max(1, len(episodes) // 2)
    mid = max(1, min(len(episodes) - 1, mid)) if len(episodes) > 1 else 0
    past_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes[: max(1, mid)]])) for s in TONAL_STATES})
    fut_avg = normalize_dist({s: float(np.mean([ep[s] for ep in episodes[mid:]])) for s in TONAL_STATES})

    chiasm_res = causal_chiasm(past_avg, fut_avg, tau=0.10, horizon=max(1, len(episodes) - mid))
    tomo_res = persistent_filtration_tomography(episodes, invariant_tau=0.14)

    chiasm_svg = write_chiasm_svg(
        chiasm_dir / "chiasm_tomography.svg",
        title=f"{src.stem.upper()} · CAUSAL CHIASM & FILTRATION TOMOGRAPHY",
        subtitle=subtitle,
        chiasm=chiasm_res,
        tomography=tomo_res,
        per_sec_a004=sec_a004,
        per_sec_a010=sec_a010,
        nexus_sec=mid,
    )

    report = {
        "source_video": str(src),
        "contract": CONTRACT,
        "equation": "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]",
        "episode_count": len(episodes),
        "nexus_sec": mid,
        "chiasm": chiasm_res,
        "tomography": tomo_res,
        "chiasm_svg": str(chiasm_svg),
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    report_path = chiasm_dir / "chiasm_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Build static HUD background
    f_title = _load_font(19, bold=True)
    f_eq = _load_font(15, bold=True)
    f_med = _load_font(15, bold=False)
    f_big = _load_font(24, bold=True)
    f_sm = _load_font(12, bold=False)
    f_sm_b = _load_font(12, bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)
    rx0, rx1 = vid_w + 14, out_w - 16

    dr.rounded_rectangle([rx0, 12, rx1, 96], radius=10, fill=(16, 23, 35), outline=(52, 78, 108), width=2)
    dr.text((rx0 + 16, 20), title, fill=(235, 194, 104), font=f_title)
    dr.text((rx0 + 16, 48), "A_tau(p) = |{x in X : p(x) > tau}| = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 16, 72), subtitle, fill=(150, 168, 190), font=f_sm)

    kpi_meta = [
        ("A_0.004(p)", (94, 218, 238)),
        ("A_0.010(p)", (242, 196, 92)),
        ("M_0.01 (dA/dt)", (244, 106, 126)),
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

    def draw_series(draw_obj: ImageDraw.ImageDraw, vals: np.ndarray, ymax: float, col: tuple[int, int, int], end_idx: int, width_px: int = 2):
        if end_idx < 1:
            return
        pts = [
            (
                int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in range(0, end_idx + 1, max(1, n_frames // 320))
        ]
        if len(pts) >= 2:
            draw_obj.line(pts, fill=col, width=width_px)

    draw_series(dr, a004, 180.0, (24, 62, 74), n_frames - 1, 1)
    draw_series(dr, a010, 50.0, (78, 64, 30), n_frames - 1, 1)

    hx0, hy0, hx1, hy1 = rx0, 464, rx1, 708
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE DISTRIBUTION p_t(x) (|X|=256) · Gold bars: p_t(x) > tau=0.010", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + 48, hy0 + 34, hx1 - 16, hy1 - 28
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    p_ymax = 0.040
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    bar_w = (hpx1 - hpx0) / 256.0

    out_mp4 = video_dir / f"{src.stem}_a_tau_overlay.mp4"
    poster_png = video_dir / f"{src.stem}_overlay_poster.png"

    # Detect whether source video has an audio stream
    has_audio = bool(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(src)]
        ).decode().strip()
    )
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
    ]
    if has_audio:
        cmd += ["-i", str(src), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    else:
        cmd += ["-map", "0:v:0"]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", str(out_mp4)]

    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert enc.stdin is not None

    poster_idx = min(n_frames - 1, mid * fps)
    for i in range(n_frames):
        sec = i / fps
        canvas = bg.copy()
        canvas.paste(Image.fromarray(frames[i]), (0, 0))
        d = ImageDraw.Draw(canvas)

        d.rounded_rectangle([10, 12, vid_w - 10, 48], radius=8, fill=(10, 14, 22), outline=(94, 218, 238), width=2)
        d.text((22, 22), f"{sec:05.2f}s  ·  {src.stem[:28]}", fill=(242, 196, 92), font=f_sm_b)
        d.rounded_rectangle([10, out_h - 46, vid_w - 10, out_h - 10], radius=8, fill=(10, 14, 22), outline=(94, 218, 238), width=1)
        d.text((20, out_h - 35), f"A_0.010={a010[i]:>2d}/256  H1={h1_arr[i]:.2f}b  H2={h2_arr[i]:.2f}b", fill=(235, 240, 245), font=f_sm_b)

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
    rc = enc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg encoder exited with code {rc}")

    return {
        "overlay_mp4": str(out_mp4),
        "poster_png": str(poster_png),
        "chiasm_svg": str(chiasm_svg),
        "chiasm_report": str(report_path),
        "frames": n_frames,
        "report": report,
    }
