#!/usr/bin/env python3
"""Build Fieldglass Specimen #10 — Live Studio Screencast ('Fieldglass Building Itself').

Source: /home/cowboy/Screencasts/Screencast From 2026-11-25 21-44-19.mp4 (1920x1080, 13m 28s)
Shows the live Antigravity Fieldglass terminal actively compiling Specimens #4-#9 side-by-side
with a live webcam mirror of Nick in the studio.

Generates:
  - 6 crisp 1080p highlight studio frames + 3x2 contact sheet
  - Architectural/Studio Edge-Field Vector SVG + 2x4 Unicode Braille of the live studio wave frame
  - 161-episode GEM Causal Chiasm & Persistent Filtration Tomography (SHA-256 sealed)
  - Landscape-native 1280x720 16x Kloster A_tau(p_t) telemetry timelapse reel (50.5s)
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    a_tau,
    build_svg_and_braille,
    extract_plate,
    load_font,
    lum_to_8state,
    make_contact_sheet,
    quartic_m4,
    renyi_h2,
    shannon_h1,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC10 = Path("/home/cowboy/Screencasts/Screencast From 2026-11-25 21-44-19.mp4")


def build_specimen10() -> dict:
    print("\n================ BUILDING SPECIMEN #10 (LIVE STUDIO SCREENCAST) ================")
    root = DOCS / "specimen10"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    # 6 crisp studio highlight stills across the 13m 28s live build session
    plate_specs = [
        ("01_studio_wave_live_terminal", "01:16 · Studio Wave & Live Build", 75.0, 2.5),
        ("02_desk_specimen_review", "02:06 · Desk Specimen Review", 125.0, 2.5),
        ("03_kneeling_book_setup", "03:47 · Books & Studio Setup", 226.0, 2.5),
        ("04_standing_present_autofs_fix", "04:38 · Standing Presentation", 277.0, 2.5),
        ("05_parallel_nvme_pipelines", "06:19 · Parallel NVMe Pipelines", 378.0, 2.5),
        ("06_closing_studio_flow", "11:22 · Closing Studio Session", 681.0, 2.5),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win in plate_specs:
        ts, p = extract_plate(SRC10, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, sample_fps=2, max_dim=1440)
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen10.jpg", cols=3, tile_w=480, tile_h=300)

    # Edge-field Vector SVG + 2x4 Braille of Nick waving inside the live webcam frame!
    wave_svg = build_svg_and_braille(
        pmap["01_studio_wave_live_terminal"],
        assets_dir,
        "studio_wave_self_portrait",
        title="LIVE STUDIO SELF-PORTRAIT · FIELDGLASS BUILDING ITSELF",
        subtitle="Screencast From 2026-11-25 21:44 · Webcam Mirror Inside Live Build Session",
        crop_box=(0.24, 0.06, 0.76, 0.90),
        braille_cols=72,
        edge_hybrid=True,
    )

    # Build 16x timelapse intermediate (808.45s -> 50.5s at 15fps)
    fps = 15
    time_scale = 16.0
    out_w, out_h = 1280, 720
    vw, vh = 768, 432  # exact 16:9 landscape viewport at top-left!

    with tempfile.TemporaryDirectory() as tmp:
        tl_mp4 = Path(tmp) / "s10_tl.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(SRC10),
            "-vf", f"setpts=PTS/{time_scale:.1f},fps={fps},scale={vw}:{vh}",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            str(tl_mp4),
        ], check=True)

        # Pass 1: decode raw frames & compute metrics
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(tl_mp4),
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ])
        fbytes = vw * vh * 3
        n_frames = len(raw) // fbytes
        frames = np.frombuffer(raw[: n_frames * fbytes], dtype=np.uint8).reshape(n_frames, vh, vw, 3)
        print(f"Decoded {n_frames} timelapse frames ({n_frames/fps:.2f}s out / {n_frames/fps*time_scale:.1f}s real)")

        a004 = np.zeros(n_frames, dtype=np.int32)
        a010 = np.zeros(n_frames, dtype=np.int32)
        a020 = np.zeros(n_frames, dtype=np.int32)
        h1_arr = np.zeros(n_frames, dtype=np.float32)
        h2_arr = np.zeros(n_frames, dtype=np.float32)
        m4_arr = np.zeros(n_frames, dtype=np.float32)
        hists = np.zeros((n_frames, 256), dtype=np.float32)

        episodes_8, ep_a004, ep_a010, ep_times = [], [], [], []
        ep_step = max(1, int(round((5.0 / time_scale) * fps)))
        for i in range(n_frames):
            sub = frames[i, ::3, ::3, :]
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
            if i % ep_step == 0:
                episodes_8.append(lum_to_8state(p))
                ep_a004.append(int(a004[i]))
                ep_a010.append(int(a010[i]))
                ep_times.append((i / float(fps)) * time_scale)

        total_real_s = (n_frames / float(fps)) * time_scale

        # Pre-render clean landscape-adapted 1280x720 HUD:
        #   Top-left (0..768, 0..432): Crisp 16:9 Live Screencast
        #   Top-right (780..1268, 12..432): Title + Equation + 5 Stacked KPI Boxes
        #   Bottom-left (12..768, 444..708): Live A_tau(p_t) Trajectory Plot
        #   Bottom-right (780..1268, 444..708): Live 256-bin Luminance Histogram
        f_title = load_font(16, bold=True)
        f_eq = load_font(12, bold=True)
        f_big = load_font(22, bold=True)
        f_med = load_font(15, bold=True)
        f_sm = load_font(11, bold=False)
        f_sm_b = load_font(11, bold=True)

        bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
        dr = ImageDraw.Draw(bg)
        rx0, rx1 = vw + 14, out_w - 14

        dr.rounded_rectangle([rx0, 10, rx1, 96], radius=10, fill=(16, 23, 35), outline=(52, 78, 108), width=2)
        dr.text((rx0 + 14, 18), "SPECIMEN #10 · FIELDGLASS STUDIO", fill=(235, 194, 104), font=f_title)
        dr.text((rx0 + 14, 44), "A_tau(p) = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
        dr.text((rx0 + 14, 68), "Live Desktop Build + Webcam Mirror (16x · 13m28s)", fill=(150, 168, 190), font=f_sm)

        kpi_meta = [
            ("A_0.004(p)  BROAD", (94, 218, 238)),
            ("A_0.010(p)  CORE", (242, 196, 92)),
            ("M_0.01  MOMENTUM", (244, 106, 126)),
            ("H1 / H2  ENTROPY", (168, 226, 142)),
            ("M4^(1/4)  PURITY", (195, 162, 255)),
        ]
        kpi_boxes = []
        for idx, (lbl, col) in enumerate(kpi_meta):
            by0 = 108 + idx * 65
            by1 = by0 + 57
            kpi_boxes.append((rx0, by0, rx1, by1))
            dr.rounded_rectangle([rx0, by0, rx1, by1], radius=8, fill=(16, 23, 35), outline=(44, 62, 86), width=1)
            dr.text((rx0 + 14, by0 + 18), lbl, fill=col, font=f_sm_b)

        # Bottom-left: Trajectory chart
        tx0, ty0, tx1, ty1 = 12, vh + 12, vw, out_h - 12
        dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
        dr.text((tx0 + 14, ty0 + 8), "SUPERLEVEL-SET VOLUME A_tau(p_t)  (Cyan: 0.004 · Gold: 0.010 · Ruby: 0.020)", fill=(205, 218, 232), font=f_sm_b)
        px0, py0, px1, py1 = tx0 + 44, ty0 + 32, tx1 - 14, ty1 - 26
        dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
        for val in (0, 20, 40, 60):
            gy = int(round(py1 - (val / 65.0) * (py1 - py0 - 8) - 4))
            dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
            dr.text((tx0 + 10, gy - 6), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)
        for k in range(6):
            st = total_real_s * (k / 5.0)
            gx = int(round(px0 + (k / 5.0) * (px1 - px0)))
            mm_t, ss_t = divmod(int(st), 60)
            dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
            dr.text((gx - 12, py1 + 6), f"{mm_t}:{ss_t:02d}", fill=(128, 146, 168), font=f_sm)

        def build_pts(vals: np.ndarray, ymax: float, end_idx: int):
            return [
                (
                    int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                    int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
                )
                for k in range(0, end_idx + 1)
            ]

        dr.line(build_pts(a004, 180.0, n_frames - 1), fill=(24, 62, 74), width=1)
        dr.line(build_pts(a010, 65.0, n_frames - 1), fill=(78, 64, 30), width=1)

        # Bottom-right: Histogram
        hx0, hy0, hx1, hy1 = rx0, vh + 12, rx1, out_h - 12
        dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
        dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE p_t(x) · Gold: > 0.010", fill=(205, 218, 232), font=f_sm_b)
        hpx0, hpy0, hpx1, hpy1 = hx0 + 44, hy0 + 32, hx1 - 14, hy1 - 26
        dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
        p_ymax = 0.050
        tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        bar_w = (hpx1 - hpx0) / 256.0
        for pv in (0.00, 0.01, 0.02, 0.03, 0.04, 0.05):
            gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
            dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
            dr.text((hx0 + 6, gy - 6), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

        out_mp4 = video_dir / "specimen10_studio_screencast_overlay.mp4"
        poster_png = video_dir / "specimen10_poster.png"
        enc = subprocess.Popen([
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
        ], stdin=subprocess.PIPE)
        assert enc.stdin is not None
        poster_idx = min(n_frames - 1, int(round((76.0 / time_scale) * fps)))

        for i in range(n_frames):
            rsec = (i / float(fps)) * time_scale
            mm_r, ss_r = divmod(int(rsec), 60)
            canvas = bg.copy()
            canvas.paste(Image.fromarray(frames[i]), (0, 0))
            d = ImageDraw.Draw(canvas)

            if rsec < 120:
                plbl, pcol = "LIVE WAVE & TERMINAL LAUNCH", (94, 218, 238)
            elif rsec < 310:
                plbl, pcol = "STUDIO SETUP & AUTOFS DEBUG", (242, 196, 92)
            elif rsec < 520:
                plbl, pcol = "PARALLEL NVMe SPECIMEN BUILD", (244, 106, 126)
            else:
                plbl, pcol = "LIVE BUILD & STUDIO FLOW", (168, 226, 142)

            d.rounded_rectangle([12, 10, 340, 42], radius=8, fill=(10, 14, 22), outline=pcol, width=2)
            d.text((22, 19), f"{mm_r}:{ss_r:02d}  ·  {plbl}", fill=pcol, font=f_sm_b)

            mom = int(a010[i] - a010[max(0, i - fps)])
            vals = [
                (f"{a004[i]:>3d}", (94, 218, 238)),
                (f"{a010[i]:>3d}", (242, 196, 92)),
                (f"{mom:+3d}/s", (244, 106, 126) if mom >= 0 else (94, 218, 238)),
                (f"{h1_arr[i]:.2f} / {h2_arr[i]:.2f} b", (168, 226, 142)),
                (f"{m4_arr[i]:.4f}", (195, 162, 255)),
            ]
            for (bx0, by0, bx1, _), (val_s, col) in zip(kpi_boxes, vals):
                d.text((bx1 - 180, by0 + 15), val_s, fill=col, font=f_big if len(val_s) <= 7 else f_med)

            if i >= 1:
                d.line(build_pts(a004, 180.0, i), fill=(86, 212, 232), width=2)
                d.line(build_pts(a010, 65.0, i), fill=(242, 196, 92), width=3)
                d.line(build_pts(a020, 65.0, i), fill=(244, 106, 126), width=2)
            cur_x = int(round(px0 + (i / max(1, n_frames - 1)) * (px1 - px0)))
            d.line([(cur_x, py0), (cur_x, py1)], fill=(255, 255, 255), width=2)

            p_now = hists[i]
            for b in range(0, 256, 2):
                pv = float(max(p_now[b], p_now[b + 1]))
                if pv <= 0.0003:
                    continue
                bx0 = int(hpx0 + b * bar_w)
                bx1 = max(bx0 + 1, int(hpx0 + (b + 2) * bar_w))
                bh_y = int(round(hpy1 - min(1.0, pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
                bar_col = (242, 196, 92) if pv > 0.010 else ((86, 198, 224) if pv > 0.004 else (58, 78, 102))
                d.rectangle([bx0, bh_y, bx1, hpy1 - 2], fill=bar_col)
            for dx in range(hpx0, hpx1, 10):
                d.line([(dx, tau_y), (min(hpx1, dx + 5), tau_y)], fill=(244, 106, 126), width=2)
            d.text((hpx1 - 150, tau_y - 16), f"tau=0.010 A={a010[i]}", fill=(244, 106, 126), font=f_sm_b)

            if i == poster_idx:
                canvas.save(poster_png, optimize=True)
            enc.stdin.write(canvas.tobytes())

        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError("Specimen #10 ffmpeg encode failed")

    nexus_ep = min(len(episodes_8) - 1, int(round(360.0 / 5.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen10_studio_screencast",
        title="SPECIMEN #10 · LIVE STUDIO SCREENCAST (FIELDGLASS BUILDING ITSELF)",
        subtitle="1920x1080 Desktop Build Terminal + Live Studio Webcam Mirror (13m 28s · 162 Episodes)",
        nexus_label="NVMe PARALLEL PIPELINE SWITCH (6:00)",
        footer_label="Fieldglass Specimen #10 · Meta-Telemetry Live Desktop Session",
        episodes_8=episodes_8,
        ep_a004=ep_a004,
        ep_a010=ep_a010,
        ep_times_s=ep_times,
        nexus_ep=nexus_ep,
        h1_mean=float(np.mean(h1_arr)),
        h2_mean=float(np.mean(h2_arr)),
        duration_sec=total_real_s,
        hud_prefix="sp10",
    )
    mp4_mb = round(out_mp4.stat().st_size / 1e6, 2)
    print(f"DONE Specimen #10: mp4={mp4_mb} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    print(json.dumps({
        "specimen10": {
            "mp4_mb": mp4_mb,
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }, indent=2))
    return {"mp4_mb": mp4_mb, "report": rep, "wave_svg": wave_svg}


if __name__ == "__main__":
    build_specimen10()
