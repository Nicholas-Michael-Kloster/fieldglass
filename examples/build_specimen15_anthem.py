#!/usr/bin/env python3
"""Build Fieldglass Specimen #15 — "The Star-Spangled Banner"
(American Iconography Visual Impulse-Response Study · 71.2s Real-Time Audio).

Source:
  - /home/cowboy/fieldglass_batch4/zoe_vid_1795717907200/zoe_vid_1795717907200.mp4
    (2026-11-26 12:33, 71.23s, 3840x2160 @ 30fps, full Star-Spangled Banner brass band audio)
  - /home/cowboy/fieldglass_batch4/zoe_vid_1795717907200/zoe_cam_1795717710383.jpg
    (2026-11-26 12:28, 4K still of the Great Seal of the United States — Obverse)

Every rapid arrow-key click across 50+ iconic American visuals (Great Seal Obverse,
North America globe, 1850 territorial map, Grand Canyon, White House, NYSE trading floor,
Mark Twain, Hollywood, Great Seal Reverse "Annuit Coeptis", One-Dollar Bill, Stars & Stripes
finale) injects an instantaneous step-function impulse into Kloster A_tau(p_t), momentum
M_0.01, entropy H1/H2, and the live 256-bin luminance histogram — synchronized live to a
brass band rendition of The Star-Spangled Banner.

Generates:
  - 6 crisp landscape highlight plates + 3x2 contact sheet
  - Matched Obverse & Reverse Great Seal Vector SVGs + 2x4 Unicode Braille:
      1) Great Seal of the United States — Obverse ("E Pluribus Unum") from 4K still
      2) Great Seal of the United States — Reverse ("Annuit Coeptis · MDCCLXXVI")
  - Real-time (1.0x) 1280x720 landscape-native 16:9 Kloster A_tau(p_t) telemetry film
    with full original Star-Spangled Banner brass band audio
  - 143-episode (0.5s cadence) SHA-256 sealed GEM Causal Chiasm & Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

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
SRC15 = Path("/home/cowboy/fieldglass_batch4/zoe_vid_1795717907200/zoe_vid_1795717907200.mp4")
CAM15 = Path("/home/cowboy/fieldglass_batch4/zoe_vid_1795717907200/zoe_cam_1795717710383.jpg")


def build_specimen15() -> dict:
    print("\n================ BUILDING SPECIMEN #15 (THE STAR-SPANGLED BANNER · REAL-TIME 71.2s) ================")
    root = DOCS / "specimen15"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1) Save upright 4K Obverse Great Seal plate from 12:28 still (rotate_ccw=270 -> 90 CW upright!)
    p_obv = plates_dir / "01_great_seal_obverse_4k.jpg"
    with Image.open(CAM15) as im:
        up = im.convert("RGB").transpose(Image.Transpose.ROTATE_270)
        up.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        up.save(p_obv, quality=92, optimize=True)
    print(f"  Plate 01_great_seal_obverse_4k (4K still rotated upright): {up.size}")

    # Extract 5 crisp highlight plates across the 71.2s video
    plate_specs = [
        ("02_mountain_peaks_panorama", "00:16 · Mountain Peaks Panorama", 15.2, 1.0),
        ("03_times_square_nasdaq", "00:29 · Times Square & NASDAQ", 28.5, 1.0),
        ("04_statue_of_liberty", "00:38 · Statue of Liberty", 37.3, 1.0),
        ("05_great_seal_reverse_pyramid", "00:47 · Great Seal Reverse (MDCCLXXVI)", 46.3, 1.0),
        ("06_stars_and_stripes_finale", "01:08 · Stars & Stripes Finale", 67.5, 1.5),
    ]
    tiles = [("12:28 · Great Seal Obverse (4K)", p_obv)]
    pmap: dict[str, Path] = {"01_great_seal_obverse_4k": p_obv}
    for slug, label, t0, win in plate_specs:
        ts, p = extract_plate(
            SRC15,
            plates_dir / f"{slug}.jpg",
            start_sec=t0,
            window_sec=win,
            sample_fps=4,
            max_dim=1600,
        )
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s")

    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen15.jpg", cols=3, tile_w=460, tile_h=340)

    # 2) Matched Obverse & Reverse Great Seal Vector SVGs + 2x4 Unicode Braille!
    obv_svg = build_svg_and_braille(
        pmap["01_great_seal_obverse_4k"],
        assets_dir,
        "great_seal_e_pluribus_unum",
        title="GREAT SEAL OF THE UNITED STATES · OBVERSE",
        subtitle="E Pluribus Unum · Edge-Field Currency Engraving (4K Still · Specimen #15)",
        crop_box=(0.06, 0.14, 0.94, 0.822),
        levels=(0.24, 0.40, 1.2),
        braille_cols=72,
        edge_hybrid=True,
    )
    rev_svg = build_svg_and_braille(
        pmap["05_great_seal_reverse_pyramid"],
        assets_dir,
        "great_seal_reverse_annuit_coeptis",
        title="GREAT SEAL OF THE UNITED STATES · REVERSE",
        subtitle="Annuit Coeptis · Novus Ordo Seclorum · MDCCLXXVI (Specimen #15)",
        crop_box=(0.352, 0.128, 0.648, 0.642),
        levels=(0.16, 0.30, 1.2),
        braille_cols=72,
        edge_hybrid=True,
    )

    # 3) Real-time (1.0x) 1280x720 landscape-native 16:9 telemetry HUD + full Star-Spangled Banner audio!
    fps = 15
    out_w, out_h = 1280, 720
    vw, vh = 768, 432

    print("Decoding full 71.23s 4K 30fps stream -> 768x432 @ 15fps (~1,068 frames)...")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(SRC15),
        "-vf", f"fps={fps},scale={vw}:{vh}:force_original_aspect_ratio=decrease,pad={vw}:{vh}:(ow-iw)/2:(oh-ih)/2:color=#0b111b",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    fbytes = vw * vh * 3
    n_frames = len(raw) // fbytes
    frames = np.frombuffer(raw[: n_frames * fbytes], dtype=np.uint8).reshape(n_frames, vh, vw, 3)
    total_real_s = n_frames / float(fps)
    print(f"  Decoded {n_frames} real-time frames ({total_real_s:.2f}s)")

    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    episodes_8, ep_a004, ep_a010, ep_times = [], [], [], []
    ep_step = max(1, int(round(0.5 * fps)))  # 0.5s high-resolution impulse cadence (~143 episodes!)
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
            ep_times.append(i / float(fps))

    # Pre-render crisp landscape-native 1280x720 HUD
    f_title = load_font(15, bold=True)
    f_eq = load_font(12, bold=True)
    f_big = load_font(22, bold=True)
    f_med = load_font(15, bold=True)
    f_sm = load_font(11, bold=False)
    f_sm_b = load_font(11, bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)
    rx0, rx1 = vw + 14, out_w - 14

    dr.rounded_rectangle([rx0, 10, rx1, 96], radius=10, fill=(16, 23, 35), outline=(244, 106, 126), width=2)
    dr.text((rx0 + 14, 18), "SPECIMEN #15 · STAR-SPANGLED BANNER", fill=(242, 196, 92), font=f_title)
    dr.text((rx0 + 14, 44), "A_tau(p) = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 14, 68), "American Iconography Impulse Study (1.0x Stereo)", fill=(150, 168, 190), font=f_sm)

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
    dr.text((tx0 + 14, ty0 + 8), "VISUAL IMPULSE TRAJECTORY A_tau(p_t)  (Cyan: 0.004 · Gold: 0.010 · Ruby: 0.020)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + 44, ty0 + 32, tx1 - 14, ty1 - 26
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    # Highlight finale Stars & Stripes crescendo band (62s..71s)
    fx0 = int(round(px0 + (62.0 / total_real_s) * (px1 - px0)))
    dr.rectangle([fx0, py0 + 1, px1 - 1, py1 - 1], fill=(42, 18, 30))
    dr.text((fx0 + 4, py0 + 6), "FLAG FINALE", fill=(255, 130, 150), font=f_sm_b)

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

    out_mp4 = video_dir / "specimen15_star_spangled_banner_overlay.mp4"
    poster_png = video_dir / "specimen15_poster.png"
    enc = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
        "-i", str(SRC15), "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-c:a", "aac", "-b:a", "96k", "-shortest",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ], stdin=subprocess.PIPE)
    assert enc.stdin is not None

    # Poster right on Stars & Stripes finale (~66.5s) where the entire trajectory is drawn!
    poster_idx = min(n_frames - 1, int(round(66.5 * fps)))

    for i in range(n_frames):
        rsec = i / float(fps)
        mm_r, ss_r = divmod(int(rsec), 60)
        canvas = bg.copy()
        canvas.paste(Image.fromarray(frames[i]), (0, 0))
        d = ImageDraw.Draw(canvas)

        if rsec < 12:
            plbl, pcol = "GREAT SEAL & NORTH AMERICA", (94, 218, 238)
        elif rsec < 26:
            plbl, pcol = "GRAND CANYON & WHITE HOUSE", (242, 196, 92)
        elif rsec < 36:
            plbl, pcol = "NYSE FLOOR & BORDERLANDS", (168, 226, 142)
        elif rsec < 45:
            plbl, pcol = "MARK TWAIN & HOLLYWOOD", (195, 162, 255)
        elif rsec < 62:
            plbl, pcol = "ANNUIT COEPTIS & CURRENCY", (242, 196, 92)
        else:
            plbl, pcol = "STARS & STRIPES FINALE", (244, 106, 126)

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
        raise RuntimeError("Specimen #15 ffmpeg encode failed")

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (0.5s cadence)
    nexus_ep = int(np.argmin(np.abs(np.array(ep_times) - 46.7)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen15_star_spangled_banner",
        title="SPECIMEN #15 · THE STAR-SPANGLED BANNER (IMPULSE STUDY)",
        subtitle="50+ American Iconography Slides Synced to Brass Band Audio (71.2s · 0.5s Cadence)",
        nexus_label="ANNUIT COEPTIS & FINALE (0:47)",
        footer_label="Fieldglass Specimen #15 · Visual Impulse-Response & National Anthem Telemetry",
        episodes_8=episodes_8,
        ep_a004=ep_a004,
        ep_a010=ep_a010,
        ep_times_s=ep_times,
        nexus_ep=nexus_ep,
        h1_mean=float(np.mean(h1_arr)),
        h2_mean=float(np.mean(h2_arr)),
        duration_sec=total_real_s,
        hud_prefix="sp15",
    )

    mp4_mb = round(out_mp4.stat().st_size / 1e6, 2)
    print(f"DONE Specimen #15: mp4={mp4_mb} MB, episodes={rep['episode_count']}, glyph={rep['chiasm_nexus']['presence_glyph']}")
    print(json.dumps({
        "specimen15": {
            "mp4_mb": mp4_mb,
            "episode_count": rep["episode_count"],
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }, indent=2))
    return {"mp4_mb": mp4_mb, "report": rep, "obv_svg": obv_svg, "rev_svg": rev_svg}


if __name__ == "__main__":
    build_specimen15()
