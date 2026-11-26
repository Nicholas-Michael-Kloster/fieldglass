#!/usr/bin/env python3
"""Build Fieldglass Specimen #11 — ASCE Guide to Post-Earthquake Investigation of Lifelines.

Unifies all 3 sequential recordings of the May 1997 ASCE Technical Council on Lifeline
Earthquake Engineering (TCLEE) Monograph into a single orientation-corrected archive entry:
  - Part 1: zoe_vid_1795666312840.mp4 (22:25, 13m 14s, landscape upright)
      Highway trusses (Fig. 11.69), bridges, high-voltage substations, CVTs (Fig. 6.28),
      wave traps / air-core inductors (Fig. 6.27), transformers, communications, railroads.
  - Part 2: zoe_vid_1795667195936.mp4 (22:33, 6m 49s, auto-corrected 180-deg flip after 25.5s)
      Liquid fuel lifeline schematic (Fig. 16.1), natural gas separators, navigation lock
      SCADA control room (Ch. 21), EOC command center layout (Fig. 22.4), seismic tank
      elephant-foot buckling (Fig. 23.2), emergency checklists & acronyms.
  - Part 3: zoe_vid_1795667656805.mp4 (22:36, 1m 40s, portrait upright)
      Master Index (Dams, Dark Start, CVT, Circuit Breakers, Microwave Control, Railroads)
      closing atop the pocket U.S. Constitution ("our frontier").
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
P1 = Path("/home/cowboy/fieldglass_ics/zoe_vid_1795666312840/zoe_vid_1795666312840.mp4")
P2 = Path("/home/cowboy/fieldglass_ics/zoe_vid_1795667195936/zoe_vid_1795667195936.mp4")
P3 = Path("/home/cowboy/fieldglass_ics/zoe_vid_1795667656805/zoe_vid_1795667656805.mp4")


def build_specimen11() -> dict:
    print("\n================ BUILDING SPECIMEN #11 (ASCE LIFELINES 3-PART MONOGRAPH) ================")
    root = DOCS / "specimen11"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    # 1) Extract 6 sharp, properly oriented engineering plates across all 3 parts
    plate_specs = [
        # (slug, label, src, start_sec, window_sec, rotate_ccw, crop_box)
        ("01_fig11_69_highway_sign_truss", "P1 00:25 · Fig. 11.69 Sign Trusses", P1, 24.2, 2.2, 90, None),
        ("02_fig6_28_substation_cvt_wave_traps", "P1 06:12 · Fig. 6.28 CVT & Wave Traps", P1, 370.8, 3.0, 0, None),
        ("03_fig16_1_liquid_fuel_lifeline", "P2 01:02 · Fig. 16.1 Liquid Fuel System", P2, 61.6, 1.2, 180, None),
        ("04_ch18_lock_scada_control_room", "P2 03:09 · Fig. 18.5 Lock Control Panel", P2, 188.2, 2.2, 180, None),
        ("05_fig20_4_eoc_command_layout", "P2 03:39 · Fig. 20.4 Telecom EOC Layout", P2, 218.6, 2.6, 180, None),
        ("06_lifelines_index_dark_start_cvt", "P3 00:59 · Index: Dams, Dark Start, CVT", P3, 57.6, 2.6, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, src, t0, win, rot, crop in plate_specs:
        out_p = plates_dir / f"{slug}.jpg"
        ts, p = extract_plate(
            src,
            out_p,
            start_sec=t0,
            window_sec=win,
            sample_fps=3,
            rotate_ccw=rot,
            crop_box=crop,
            max_dim=1600,
        )
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s (rot={rot})")

    # Remove superseded plate filenames if any
    for old in ("04_ch21_lock_scada_control_room.jpg", "05_fig22_4_eoc_command_layout.jpg"):
        (plates_dir / old).unlink(missing_ok=True)

    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen11.jpg", cols=3, tile_w=460, tile_h=360)

    # 2) Two crisp Vector SVGs + 2x4 Unicode Braille bundles of flagship Lifelines engineering diagrams
    fuel_svg = build_svg_and_braille(
        pmap["03_fig16_1_liquid_fuel_lifeline"],
        assets_dir,
        "asce_fig16_1_liquid_fuel_lifeline",
        title="FIG. 16.1 · LIQUID FUEL LIFELINE SYSTEM SCHEMATIC",
        subtitle="ASCE Guide to Post-Earthquake Investigation of Lifelines (May 1997, p. 16-3)",
        crop_box=(0.388, 0.270, 0.785, 0.750),
        sigma=38.0,
        paper_cutoff=0.95,
        ink_floor=0.48,
        gamma=1.18,
        braille_cols=76,
    )
    truss_svg = build_svg_and_braille(
        pmap["01_fig11_69_highway_sign_truss"],
        assets_dir,
        "asce_fig11_69_highway_sign_truss",
        title="FIG. 11.69 · HIGHWAY OVERHEAD SIGN SUPPORT TRUSSES",
        subtitle="ASCE Guide to Post-Earthquake Investigation of Lifelines (May 1997 · Ch. 11)",
        crop_box=(0.03, 0.08, 0.96, 0.728),
        sigma=40.0,
        paper_cutoff=0.945,
        ink_floor=0.46,
        gamma=1.15,
        braille_cols=72,
    )

    # 3) Fast keyframe-decoded unified 3-part 16:9 landscape timelapse (~55s @ 15fps)
    #    Using -skip_frame nokey decodes only I-frames (~1/s), 60x faster than decoding 85,000 4K frames!
    fps = 15
    out_w, out_h = 1280, 720
    vw, vh = 768, 432

    segs = [
        # (name, src, ss, dur, target_frames, vf_extra, real_start)
        ("p1", P1, 0.0, 793.95, 390, "", 0.0),
        ("p2a", P2, 0.0, 25.5, 18, "", 793.95),
        ("p2b", P2, 25.5, 383.89, 270, "hflip,vflip,", 819.45),
        ("p3", P3, 0.0, 100.30, 150, "", 1203.34),
    ]
    total_real_s = 1303.64

    frame_chunks = []
    real_ts_list = []

    for name, src, ss, dur, target_nf, vf_extra, r0 in segs:
        vf = (
            f"{vf_extra}"
            f"scale={vw}:{vh}:force_original_aspect_ratio=decrease,"
            f"pad={vw}:{vh}:(ow-iw)/2:(oh-ih)/2:color=#0b111b"
        )
        cmd = ["ffmpeg", "-v", "error", "-skip_frame", "nokey"]
        if ss > 0:
            cmd += ["-ss", f"{ss:.2f}"]
        cmd += [
            "-i", str(src),
            "-t", f"{dur:.2f}",
            "-vsync", "vfr",
            "-vf", vf,
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
        raw = subprocess.check_output(cmd)
        fbytes = vw * vh * 3
        nf_raw = len(raw) // fbytes
        arr_raw = np.frombuffer(raw[: nf_raw * fbytes], dtype=np.uint8).reshape(nf_raw, vh, vw, 3)
        idxs = np.linspace(0, max(0, nf_raw - 1), target_nf).round().astype(int)
        arr = arr_raw[idxs]
        frame_chunks.append(arr)
        for k in range(len(arr)):
            frac = k / max(1, len(arr) - 1) if len(arr) > 1 else 0.0
            real_ts_list.append(r0 + frac * dur)
        print(f"  Segment {name}: {nf_raw} keyframes -> {len(arr)} frames ({len(arr)/fps:.2f}s out for {dur:.1f}s real)")

    frames = np.concatenate(frame_chunks, axis=0)
    real_ts = np.array(real_ts_list, dtype=np.float64)
    n_frames = len(frames)
    print(f"Total unified Specimen #11 frames: {n_frames} ({n_frames/fps:.2f}s out / {total_real_s:.1f}s real)")

    # 4) Compute live Kloster A_tau(p_t) metrics + 8-state episodes every ~8s real (~163 episodes)
    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    episodes_8, ep_a004, ep_a010, ep_times = [], [], [], []
    next_ep_t = 0.0
    ep_interval = 8.0

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
        if real_ts[i] >= next_ep_t:
            episodes_8.append(lum_to_8state(p))
            ep_a004.append(int(a004[i]))
            ep_a010.append(int(a010[i]))
            ep_times.append(float(real_ts[i]))
            next_ep_t = float(real_ts[i]) + ep_interval

    # 5) Render landscape-native 1280x720 telemetry HUD MP4
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
    dr.text((rx0 + 14, 18), "SPECIMEN #11 · ASCE LIFELINES", fill=(235, 194, 104), font=f_title)
    dr.text((rx0 + 14, 44), "A_tau(p) = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 14, 68), "3-Part Critical Infrastructure Monograph (21m44s)", fill=(150, 168, 190), font=f_sm)

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

    tx0, ty0, tx1, ty1 = 12, vh + 12, vw, out_h - 12
    dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((tx0 + 14, ty0 + 8), "SUPERLEVEL-SET VOLUME A_tau(p_t)  (Cyan: 0.004 · Gold: 0.010 · Ruby: 0.020)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + 44, ty0 + 32, tx1 - 14, ty1 - 26
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    # Mark Part 2 Liquid Fuel & SCADA transition band
    p2_x0 = int(round(px0 + (793.95 / total_real_s) * (px1 - px0)))
    p2_x1 = int(round(px0 + (1203.34 / total_real_s) * (px1 - px0)))
    dr.rectangle([p2_x0, py0 + 1, p2_x1, py1 - 1], fill=(32, 22, 34))
    dr.text((p2_x0 + 6, py0 + 6), "PART 2 · FUEL & SCADA", fill=(255, 130, 150), font=f_sm_b)

    for val in (0, 20, 40, 60):
        gy = int(round(py1 - (val / 65.0) * (py1 - py0 - 8) - 4))
        dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
        dr.text((tx0 + 10, gy - 6), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)
    for k in range(6):
        st = total_real_s * (k / 5.0)
        gx = int(round(px0 + (k / 5.0) * (px1 - px0)))
        mm_t, ss_t = divmod(int(st), 60)
        dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
        dr.text((gx - 14, py1 + 6), f"{mm_t}:{ss_t:02d}", fill=(128, 146, 168), font=f_sm)

    def build_pts(vals: np.ndarray, ymax: float, end_idx: int):
        return [
            (
                int(round(px0 + (real_ts[k] / total_real_s) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in range(0, end_idx + 1)
        ]

    dr.line(build_pts(a004, 180.0, n_frames - 1), fill=(24, 62, 74), width=1)
    dr.line(build_pts(a010, 65.0, n_frames - 1), fill=(78, 64, 30), width=1)

    hx0, hy0, hx1, hy1 = rx0, vh + 12, rx1, out_h - 12
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE p_t(x) · Gold: > 0.010", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + 44, hy0 + 32, hx1 - 14, hy1 - 26
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    p_ymax = 0.045
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    bar_w = (hpx1 - hpx0) / 256.0
    for pv in (0.00, 0.01, 0.02, 0.03, 0.04):
        gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
        dr.text((hx0 + 6, gy - 6), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

    out_mp4 = video_dir / "specimen11_asce_lifelines_overlay.mp4"
    poster_png = video_dir / "specimen11_poster.png"
    enc = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ], stdin=subprocess.PIPE)
    assert enc.stdin is not None

    # Poster right at Fig. 16.1 Liquid Fuel Lifeline Schematic (~855s real)
    poster_idx = int(np.argmin(np.abs(real_ts - 855.0)))

    for i in range(n_frames):
        rsec = float(real_ts[i])
        mm_r, ss_r = divmod(int(rsec), 60)
        canvas = bg.copy()
        canvas.paste(Image.fromarray(frames[i]), (0, 0))
        d = ImageDraw.Draw(canvas)

        if rsec < 340:
            plbl, pcol = "P1 · HIGHWAYS, TRUSSES & BRIDGES", (94, 218, 238)
        elif rsec < 793.95:
            plbl, pcol = "P1 · HV SUBSTATIONS, CVT & GRID", (242, 196, 92)
        elif rsec < 975:
            plbl, pcol = "P2 · LIQUID FUEL & GAS LIFELINES", (244, 106, 126)
        elif rsec < 1203.34:
            plbl, pcol = "P2 · LOCK SCADA, EOC & TANKS", (195, 162, 255)
        else:
            plbl, pcol = "P3 · INDEX (DARK START) & FRONTIER", (168, 226, 142)

        d.rounded_rectangle([12, 10, 382, 42], radius=8, fill=(10, 14, 22), outline=pcol, width=2)
        d.text((22, 19), f"{mm_r:02d}:{ss_r:02d}  ·  {plbl}", fill=pcol, font=f_sm_b)

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
        cur_x = int(round(px0 + (rsec / total_real_s) * (px1 - px0)))
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
        raise RuntimeError("Specimen #11 ffmpeg encode failed")

    # 6) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography
    nexus_ep = int(np.argmin(np.abs(np.array(ep_times) - 793.95)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen11_asce_lifelines",
        title="SPECIMEN #11 · ASCE LIFELINES CRITICAL INFRASTRUCTURE (3 PARTS)",
        subtitle="Highways, HV Substations/CVTs, Liquid Fuel, Lock SCADA, EOC & Master Index (21m 44s)",
        nexus_label="FUEL & SCADA TRANSITION (13:14)",
        footer_label="Fieldglass Specimen #11 · ASCE TCLEE Lifelines Monograph (May 1997)",
        episodes_8=episodes_8,
        ep_a004=ep_a004,
        ep_a010=ep_a010,
        ep_times_s=ep_times,
        nexus_ep=nexus_ep,
        h1_mean=float(np.mean(h1_arr)),
        h2_mean=float(np.mean(h2_arr)),
        duration_sec=total_real_s,
        hud_prefix="sp11",
    )
    mp4_mb = round(out_mp4.stat().st_size / 1e6, 2)
    print(f"DONE Specimen #11: mp4={mp4_mb} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    print(json.dumps({
        "specimen11": {
            "mp4_mb": mp4_mb,
            "episode_count": rep["episode_count"],
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }, indent=2))
    return {"mp4_mb": mp4_mb, "report": rep, "fuel_svg": fuel_svg, "truss_svg": truss_svg}


if __name__ == "__main__":
    build_specimen11()
