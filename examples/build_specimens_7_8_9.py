#!/usr/bin/env python3
"""Build Fieldglass Specimens #7, #8, and #9 directly into /home/cowboy/fieldglass/docs/.

- Specimen #7 (20:10): Flow Visualization (Wolfgang Merzkirch, 1987, Linda Hall Library)
  — Linda Hall Ex Libris Bookplate (Swan & Three Gauntlets) + Fig. 2.48 Cross-Hatched
  ABLATION Pattern on Teflon Cone (Nachtsheim & Larson, 1971) + full real-time voice telemetry
- Specimen #8 (20:25): Festschrift Zoller (Dissertationes Botanicae 196, 1993)
  — Blank-Book Calibration Baseline + Ulrich Kull Hexagonal Sociocultural System (Wissenschaft)
  + Post-Glacial Europe & Africa Maps + 12x Kloster A_tau(p_t) timelapse
- Specimen #9 (21:21): FLAGSHIP — "Let There Be Light" (Nick & Dr. Helen Ruth Horkan)
  — Full 15-minute auto-straightened upright live-voice Kloster telemetry film + Ogham "Doctor"
  SVG/Braille + Antique Thomas Moore Irish Harp Cover SVG/Braille + 180-episode Chiasm!
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    build_svg_and_braille,
    extract_plate,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC7 = Path("/home/cowboy/fieldglass_new_upload/zoe_vid_1795658666655/zoe_vid_1795658666655.mp4")
SRC8 = Path("/home/cowboy/fieldglass_new_upload/zoe_vid_1795659098599/zoe_vid_1795659098599.mp4")
SRC9 = Path("/home/cowboy/fieldglass_new_upload/zoe_vid_1795662355520/zoe_vid_1795662355520.mp4")


def build_specimen7() -> dict:
    print("\n================ BUILDING SPECIMEN #7 (20:10 FLOW VISUALIZATION / ABLATION) ================")
    root = DOCS / "specimen7"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"

    plate_specs = [
        ("01_linda_hall_bookplate", "Linda Hall Ex Libris (TA357 .M47)", 7.0, 2.5, 0, None),
        ("02_cross_slit_schlieren", "Fig. 3.17 Cross-Slit Schlieren (1968)", 39.5, 2.5, 0, None),
        ("03_grid_deflection_moire", "Fig. 3.22 Moire Deflection Grid", 88.5, 2.5, 0, None),
        ("04_fluorescent_minitufts_car", "Fig. 2.47 Fluorescent Minitufts (160km/h)", 121.0, 2.5, 0, None),
        ("05_ablation_pattern_teflon_cone", "Fig. 2.48 Cross-Hatched ABLATION Cone", 153.5, 2.5, 0, None),
        ("06_mach_zehnder_interferogram", "Fig. 3.30 Zeiss Mach-Zehnder Plume", 235.0, 2.5, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(SRC7, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, rotate_ccw=rot, crop_box=crop)
        pmap[slug] = p
        mm, ss = divmod(int(ts), 60)
        tiles.append((f"{mm}:{ss:02d} · {label}", p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen7.jpg", cols=3, tile_w=420, tile_h=560)

    # 2 Hero SVGs + Braille: (1) Linda Hall Ex Libris Bookplate, (2) Fig. 2.48 Cross-Hatched ABLATION Cone!
    bookplate = build_svg_and_braille(
        pmap["01_linda_hall_bookplate"],
        assets_dir,
        "linda_hall_ex_libris_bookplate",
        title="LINDA HALL LIBRARY · EX LIBRIS BOOKPLATE",
        subtitle="Hall Family Arms (Swan Crest & Three Gauntlets) · Flow Visualization (TA357 .M47)",
        crop_box=(0.10, 0.21, 0.54, 0.54),
        sigma=36.0,
        paper_cutoff=0.92,
        ink_floor=0.42,
        braille_cols=68,
    )
    ablation = build_svg_and_braille(
        pmap["05_ablation_pattern_teflon_cone"],
        assets_dir,
        "fig248_crosshatched_ablation_cone",
        title="FIG. 2.48 · CROSS-HATCHED ABLATION PATTERN ON TEFLON MODEL",
        subtitle="Nachtsheim & Larson (1971) · Merzkirch Flow Visualization · Ablation-Tool",
        crop_box=(0.30, 0.02, 0.85, 0.62),
        braille_cols=64,
        edge_hybrid=True,
    )

    # Trim cleanly at 244s (4m 04s, right after Mach-Zehnder interferogram, before feet-up ending)
    with tempfile.TemporaryDirectory() as tmp:
        trim_mp4 = Path(tmp) / "s7_trim.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-ss", "0", "-t", "244", "-i", str(SRC7),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-vf", "fps=15,scale=540:-2",
            "-c:a", "aac", "-b:a", "96k", str(trim_mp4),
        ], check=True)

        def phase7(rsec: float):
            if rsec < 32.0:
                return "LINDA HALL BOOKPLATE & OPTICS", (94, 218, 238)
            if rsec < 110.0:
                return "SCHLIEREN & MOIRE DEFLECTION", (242, 196, 92)
            if rsec < 175.0:
                return "MINITUFTS & FIG 2.48 ABLATION", (244, 106, 126)
            return "SPATIAL FILTER & INTERFEROGRAM", (168, 226, 142)

        vid_res = render_telemetry_overlay_from_video(
            trim_mp4,
            video_dir / "specimen7_flow_visualization_ablation_overlay.mp4",
            video_dir / "specimen7_poster.png",
            header_title="SPECIMEN #7  ·  FLOW VISUALIZATION & FIG. 2.48 ABLATION",
            header_sub="Merzkirch (1987) · Linda Hall Library · Live Real-Time Voice Telemetry (4m04s)",
            phase_fn=phase7,
            nexus_band=(146.0, 168.0, "ABLATION CONE"),
            out_w=1280,
            out_h=720,
            fps=15,
            crf=27,
            audio_bitrate="80k",
            keep_audio=True,
            poster_sec=154.5,
            episode_interval_s=5.0,
            time_scale=1.0,
        )

    nexus_ep = min(len(vid_res["episodes_8"]) - 1, int(round(154.0 / 5.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen7_flow_visualization",
        title="SPECIMEN #7 · FLOW VISUALIZATION & CROSS-HATCHED ABLATION CONE",
        subtitle="Merzkirch (1987) · Linda Hall Library Bookplate -> Fig. 2.48 Ablation -> Zeiss Interferogram",
        nexus_label="FIG 2.48 ABLATION CONE (2:34)",
        footer_label="Fieldglass Specimen #7 · Flow Visualization (Linda Hall Library)",
        episodes_8=vid_res["episodes_8"],
        ep_a004=vid_res["ep_a004"],
        ep_a010=vid_res["ep_a010"],
        ep_times_s=vid_res["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=vid_res["h1_mean"],
        h2_mean=vid_res["h2_mean"],
        duration_sec=vid_res["duration_real_s"],
        hud_prefix="sp7",
    )
    print(f"DONE Specimen #7: mp4={vid_res['mp4_mb']} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    return {"mp4_mb": vid_res["mp4_mb"], "report": rep, "bookplate": bookplate, "ablation": ablation}


def build_specimen8() -> dict:
    print("\n================ BUILDING SPECIMEN #8 (20:25 FESTSCHRIFT ZOLLER) ================")
    root = DOCS / "specimen8"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"

    plate_specs = [
        ("01_blank_journal_baseline", "Blank-Book Calibration Baseline", 24.5, 2.5, 0, None),
        ("02_schneckenklee_root_fractal", "2.25m Schneckenklee Root Fractal", 128.0, 2.5, 0, None),
        ("03_swiss_pine_heart_rot", "Swiss Stone Pine Heart-Rot Sections", 179.5, 2.5, 0, None),
        ("04_tropical_africa_biogeography", "Tropical Africa Phytogeography Map", 334.5, 2.5, 0, None),
        ("05_kull_sociocultural_wheel", "Ulrich Kull (1979) Wissenschaft Wheel", 425.2, 1.8, 0, None),
        ("06_postglacial_europe_alps_map", "Post-Glacial Europe & Alps Migration", 592.5, 2.5, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(SRC8, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, rotate_ccw=rot, crop_box=crop)
        pmap[slug] = p
        mm, ss = divmod(int(ts), 60)
        tiles.append((f"{mm}:{ss:02d} · {label}", p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen8.jpg", cols=3, tile_w=420, tile_h=560)

    kull = build_svg_and_braille(
        pmap["05_kull_sociocultural_wheel"],
        assets_dir,
        "kull_sociocultural_hex_wheel",
        title="SOZIOKULTURELLES SYSTEM · ULRICH KULL (1979)",
        subtitle="Festschrift Zoller (1993) · Wissenschaft Center Hub & 6 Sociocultural Petals",
        crop_box=(0.04, 0.04, 0.96, 0.88),
        sigma=42.0,
        paper_cutoff=0.92,
        ink_floor=0.40,
        braille_cols=72,
    )
    alps = build_svg_and_braille(
        pmap["06_postglacial_europe_alps_map"],
        assets_dir,
        "postglacial_europe_alps_map",
        title="POST-GLACIAL TREE MIGRATION · NORTHERN ALPS & EUROPE",
        subtitle="Festschrift Zoller (1993) · Spruce (Fichte), Fir (Tanne) & Beech (Buche)",
        crop_box=(0.06, 0.14, 0.99, 0.78),
        sigma=42.0,
        paper_cutoff=0.92,
        ink_floor=0.40,
        braille_cols=72,
    )

    # 12x timelapse across clean 0..675s (11m 15s -> 56.2s, trimmed before whip-pans & 12:10 personal info)
    with tempfile.TemporaryDirectory() as tmp:
        tl_mp4 = Path(tmp) / "s8_timelapse.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-ss", "0", "-t", "675", "-i", str(SRC8),
            "-vf", "setpts=PTS/12.0,fps=15,scale=540:-2",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            str(tl_mp4),
        ], check=True)

        def phase8(rsec: float):
            if rsec < 65.0:
                return "BLANK-BOOK CALIBRATION SLATE", (94, 218, 238)
            if rsec < 260.0:
                return "ROOT FRACTALS & PINE PATHOLOGY", (168, 226, 142)
            if rsec < 470.0:
                return "AFRICA MAP & KULL HEX WHEEL", (244, 106, 126)
            return "POST-GLACIAL ALPS & BIOGEOGRAPHY", (242, 196, 92)

        vid_res = render_telemetry_overlay_from_video(
            tl_mp4,
            video_dir / "specimen8_festschrift_zoller_overlay.mp4",
            video_dir / "specimen8_poster.png",
            header_title="SPECIMEN #8  ·  FESTSCHRIFT ZOLLER (CALIBRATION -> ATLAS)",
            header_sub="Blank-Journal Baseline -> Root Fractals, Kull Hex Wheel & Post-Glacial Maps (12x)",
            phase_fn=phase8,
            nexus_band=(0.0, 65.0, "BLANK BASELINE"),
            out_w=1280,
            out_h=720,
            fps=15,
            crf=25,
            keep_audio=False,
            poster_sec=593.0,
            episode_interval_s=5.0,
            time_scale=12.0,
        )

    nexus_ep = min(len(vid_res["episodes_8"]) - 1, int(round(65.0 / 5.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen8_festschrift_zoller",
        title="SPECIMEN #8 · FESTSCHRIFT ZOLLER (BLANK BASELINE -> BOTANICAL ATLAS)",
        subtitle="Dissertationes Botanicae 196 (1993) · 11m 15s Clean Span (135 Episodes)",
        nexus_label="CALIBRATION -> ATLAS (1:05)",
        footer_label="Fieldglass Specimen #8 · Festschrift Zoller (Linda Hall Library)",
        episodes_8=vid_res["episodes_8"],
        ep_a004=vid_res["ep_a004"],
        ep_a010=vid_res["ep_a010"],
        ep_times_s=vid_res["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=vid_res["h1_mean"],
        h2_mean=vid_res["h2_mean"],
        duration_sec=vid_res["duration_real_s"],
        hud_prefix="sp8",
    )
    print(f"DONE Specimen #8: mp4={vid_res['mp4_mb']} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    return {"mp4_mb": vid_res["mp4_mb"], "report": rep, "kull": kull, "alps": alps}


def build_specimen9() -> dict:
    print("\n================ BUILDING SPECIMEN #9 (21:21 FLAGSHIP: NICK & DR. HELEN) ================")
    root = DOCS / "specimen9"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"

    # Extract 6 crisp UPRIGHT hero plates across the 15-minute film
    plate_specs = [
        ("01_dr_helen_chalkboard_jellyfish", "Dr. Helen Ruth Horkan & Jellyfish Board", 64.0, 2.5, 0, None),
        ("02_moths_ballet_boots_still_life", "Moths, Ballet Shoes, Boots & Genome", 79.5, 2.5, 0, None),
        ("03_lalla_rookh_open_spread", "Thomas Moore — Lalla Rookh (1817)", 309.5, 2.5, 90, None),
        ("04_thomas_moore_irish_harp_cover", "Thomas Moore Antique Gilt Irish Harp", 366.0, 2.5, 90, None),
        ("05_ogham_doctor_script", "Ancient Irish Ogham 'DOCTOR' Script", 818.0, 2.5, 0, None),
        ("06_nick_and_helen_let_there_be_light", "Nick & Dr. Helen — 'Let There Be Light'", 874.5, 2.5, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(SRC9, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, rotate_ccw=rot, crop_box=crop)
        pmap[slug] = p
        mm, ss = divmod(int(ts), 60)
        tiles.append((f"{mm}:{ss:02d} · {label}", p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen9.jpg", cols=3, tile_w=420, tile_h=560)

    # 2 Iconic Vector SVGs + Braille:
    # (1) Ancient Irish Ogham "DOCTOR" script study, (2) Antique Thomas Moore Gilt Irish Harp Cover!
    ogham = build_svg_and_braille(
        pmap["05_ogham_doctor_script"],
        assets_dir,
        "ogham_doctor_script_study",
        title="ANCIENT IRISH OGHAM SCRIPT · 'DOCTOR'",
        subtitle="Dr. Helen Ruth Horkan · Cnidarian Stem-Cell & Radiation Biologist",
        crop_box=(0.24, 0.16, 0.76, 0.86),
        sigma=36.0,
        paper_cutoff=0.93,
        ink_floor=0.45,
        braille_cols=60,
    )
    moore = build_svg_and_braille(
        pmap["04_thomas_moore_irish_harp_cover"],
        assets_dir,
        "thomas_moore_irish_harp_cover",
        title="THOMAS MOORE · POETICAL WORKS (IRISH HARP GILT COVER)",
        subtitle="Ireland's National Poet · Lalla Rookh & Victorian Gilt Stamping Study",
        crop_box=(0.14, 0.04, 0.84, 0.72),
        braille_cols=68,
        edge_hybrid=True,
    )

    # Auto-straighten the full 15-minute film into a crisp upright 406x720 (or 324x576) intermediate:
    #   Seg A:   0.0s .. 117.5s -> Upright Portrait (0 deg)
    #   Seg B: 117.5s .. 771.0s -> Rotated 90 deg CCW (transpose=2), fit cleanly upright inside portrait canvas!
    #   Seg C: 771.0s .. END    -> Upright Portrait (0 deg)
    # Keep 100% of original stereo conversation (Dr. Helen's Nematostella/500 Gy talk, Miss Byrne, Moore, "Let there be light")!
    out_w, out_h = 1024, 576
    vid_w = 324  # exact 9:16 portrait column for 576p canvas
    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)
        segs_spec = [
            (0.0, 117.5, False),
            (117.5, 771.0, True),
            (771.0, None, False),
        ]
        seg_files = []
        for idx, (s0, s1, rot90_ccw) in enumerate(segs_spec):
            sp = tdir / f"s9_seg_{idx}.mp4"
            vf_parts = ["fps=15"]
            if rot90_ccw:
                vf_parts.append("transpose=2")
            vf_parts.append(f"scale={vid_w}:{out_h}:force_original_aspect_ratio=decrease")
            vf_parts.append(f"pad={vid_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=0x0b0f17")
            cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{s0:.2f}"]
            if s1 is not None:
                cmd += ["-to", f"{s1:.2f}"]
            cmd += [
                "-i", str(SRC9),
                "-vf", ",".join(vf_parts),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "88k",
                str(sp),
            ]
            print(f"  Straightening Segment {idx} ({s0}s -> {s1 or 'END'}s, rot={rot90_ccw})...")
            subprocess.run(cmd, check=True)
            seg_files.append(sp)

        list_txt = tdir / "concat9.txt"
        list_txt.write_text("\n".join(f"file '{p}'" for p in seg_files) + "\n", encoding="utf-8")
        upright_mp4 = tdir / "s9_upright_full.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
            "-i", str(list_txt), "-c", "copy", str(upright_mp4),
        ], check=True)

        def phase9(rsec: float):
            if rsec < 65.0:
                return "NO DECEPTION · NICK & DR. HELEN", (242, 196, 92)
            if rsec < 210.0:
                return "NEMATOSTELLA & 500 Gy RADIATION", (94, 218, 238)
            if rsec < 355.0:
                return "MISS BYRNE · GENETICS & NATURE", (168, 226, 142)
            if rsec < 775.0:
                return "THOMAS MOORE · LALLA ROOKH", (244, 106, 126)
            if rsec < 842.0:
                return "IRISH OGHAM SCRIPT · 'DOCTOR'", (195, 162, 255)
            return "LET THERE BE LIGHT · CLOSING", (242, 196, 92)

        vid_res = render_telemetry_overlay_from_video(
            upright_mp4,
            video_dir / "specimen9_let_there_be_light_overlay.mp4",
            video_dir / "specimen9_poster.png",
            header_title="SPECIMEN #9  ·  LET THERE BE LIGHT (NICK & DR. HELEN)",
            header_sub="Nematostella 500 Gy Radiation · Thomas Moore · Ogham 'Doctor' (Auto-Straightened 15m04s)",
            phase_fn=phase9,
            nexus_band=(355.0, 395.0, "SCIENCE -> POETRY"),
            out_w=out_w,
            out_h=out_h,
            fps=15,
            crf=29,
            audio_bitrate="80k",
            keep_audio=True,
            poster_sec=64.0,
            episode_interval_s=5.0,
            time_scale=1.0,
        )

    nexus_ep = min(len(vid_res["episodes_8"]) - 1, int(round(365.0 / 5.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen9_let_there_be_light",
        title="SPECIMEN #9 · LET THERE BE LIGHT (NICK & DR. HELEN RUTH HORKAN)",
        subtitle="Cnidarian Regeneration & 500 Gy Radiation -> Thomas Moore, Ogham & Closing (15m 04s · 180 Ep)",
        nexus_label="SCIENCE -> POETRY & OGHAM (6:05)",
        footer_label="Fieldglass Specimen #9 · Flagship Full-Voice Upright Film (Nick & Dr. Helen)",
        episodes_8=vid_res["episodes_8"],
        ep_a004=vid_res["ep_a004"],
        ep_a010=vid_res["ep_a010"],
        ep_times_s=vid_res["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=vid_res["h1_mean"],
        h2_mean=vid_res["h2_mean"],
        duration_sec=vid_res["duration_real_s"],
        hud_prefix="sp9",
    )
    print(f"DONE Specimen #9: mp4={vid_res['mp4_mb']} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    return {"mp4_mb": vid_res["mp4_mb"], "report": rep, "ogham": ogham, "moore": moore}


if __name__ == "__main__":
    r7 = build_specimen7()
    r8 = build_specimen8()
    r9 = build_specimen9()
    summary = {
        "specimen7": {"mp4_mb": r7["mp4_mb"], "glyph": r7["report"]["chiasm_nexus"]["presence_glyph"], "past_A": r7["report"]["chiasm_nexus"]["past_accessible_volume"], "future_A": r7["report"]["chiasm_nexus"]["future_accessible_volume"], "ei": r7["report"]["chiasm_nexus"]["effective_information_bits"], "invariants": r7["report"]["persistent_filtration_tomography"]["structural_invariants"]},
        "specimen8": {"mp4_mb": r8["mp4_mb"], "glyph": r8["report"]["chiasm_nexus"]["presence_glyph"], "past_A": r8["report"]["chiasm_nexus"]["past_accessible_volume"], "future_A": r8["report"]["chiasm_nexus"]["future_accessible_volume"], "ei": r8["report"]["chiasm_nexus"]["effective_information_bits"], "invariants": r8["report"]["persistent_filtration_tomography"]["structural_invariants"]},
        "specimen9": {"mp4_mb": r9["mp4_mb"], "glyph": r9["report"]["chiasm_nexus"]["presence_glyph"], "past_A": r9["report"]["chiasm_nexus"]["past_accessible_volume"], "future_A": r9["report"]["chiasm_nexus"]["future_accessible_volume"], "ei": r9["report"]["chiasm_nexus"]["effective_information_bits"], "invariants": r9["report"]["persistent_filtration_tomography"]["structural_invariants"]},
    }
    print("\n=== SUMMARY #7-#9 ===")
    print(json.dumps(summary, indent=2))
