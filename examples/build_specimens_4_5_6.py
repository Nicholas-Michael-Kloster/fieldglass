#!/usr/bin/env python3
"""Build Fieldglass Specimens #4, #5, and #6 directly into /home/cowboy/fieldglass/docs/.

- Specimen #4 (19:32): Laminar-Turbulent Transition + Hewett Cottrell Watson (Darwin 1849,
  Hooker 1855, J.G. Baker, Hochstetter Pico Botanical Altitude Map, Godman 1870 Azores Map)
- Specimen #5 (19:48): Mechanical Characterization of Materials & Wave Dispersion
  (BaTiO3 Spatial Overlay Pitch, Wheatstone Bridge, Shear Piezoelectric Accelerometers, DFT)
- Specimen #6 (19:57): The U.S. Constitution & Declaration of Independence (Privacy-Scrubbed:
  all password-slip segments cut and desk ID card region permanently masked)
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
SRC4 = Path("/home/cowboy/fieldglass_new_upload/zoe_vid_1795656038426.mp4")
SRC5 = Path("/home/cowboy/fieldglass_new_upload/zoe_vid_1795657454836.mp4")
SRC6 = Path("/home/cowboy/fieldglass_new_upload/zoe_vid_1795657959494/zoe_vid_1795657959494.mp4")


def build_specimen4() -> dict:
    print("\n================ BUILDING SPECIMEN #4 (19:32) ================")
    root = DOCS / "specimen4"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"

    # Extract 6 museum-grade plates across both books
    plate_specs = [
        ("01_blasius_wave_plots", "Blasius Boundary Layer Wave Plots", 133.5, 2.5, 90, None),
        ("02_jg_baker_at_work", "J. G. Baker at Work (Kew Herbarium)", 287.5, 2.5, 0, None),
        ("03_charles_darwin_1849", "Charles Darwin (1849), T. H. Maguire", 326.0, 2.5, 0, None),
        ("04_jd_hooker_1855", "Joseph Dalton Hooker (1855), G. Richmond", 441.5, 2.5, 0, None),
        ("05_hochstetter_pico_zonation", "Botanical Zonation of Pico, Hochstetter", 480.0, 2.5, 0, None),
        ("06_godman_azores_map_1870", "Fig. 5 Locator Map of the Azores (1870)", 518.5, 2.5, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(SRC4, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, rotate_ccw=rot, crop_box=crop)
        pmap[slug] = p
        mm, ss = divmod(int(ts), 60)
        tiles.append((f"{mm}:{ss:02d} · {label}", p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen4.jpg", cols=3, tile_w=420, tile_h=560)

    # 2 Vector SVGs + 2x4 Braille: (1) 1870 Azores Map, (2) Hochstetter's Pico Botanical Zonation
    azores = build_svg_and_braille(
        pmap["06_godman_azores_map_1870"],
        assets_dir,
        "godman_azores_map_1870",
        title="LOCATOR MAP OF THE AZORES ISLANDS · GODMAN (1870)",
        subtitle="Hewett Cottrell Watson (Egerton) · Stanford's Geographical Estab. London",
        crop_box=(0.0, 0.0, 0.88, 0.87),
        sigma=48.0,
        paper_cutoff=0.925,
        ink_floor=0.40,
        braille_cols=72,
    )
    pico = build_svg_and_braille(
        pmap["05_hochstetter_pico_zonation"],
        assets_dir,
        "hochstetter_pico_zonation",
        title="ALTITUDINAL BOTANICAL ZONATION OF PICO (AZORES)",
        subtitle="C. F. Hochstetter · Humboldt-style Flora Strata & Volcanic Profile",
        crop_box=(0.0, 0.03, 0.96, 0.76),
        sigma=44.0,
        paper_cutoff=0.92,
        ink_floor=0.38,
        braille_cols=72,
    )

    # Create 12x timelapse (0..580s -> 48.3s, trimmed cleanly right after Watson portrait at 9:40)
    with tempfile.TemporaryDirectory() as tmp:
        tl_mp4 = Path(tmp) / "s4_timelapse.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            "-ss", "0", "-t", "580", "-i", str(SRC4),
            "-vf", "setpts=PTS/12.0,fps=15,scale=540:-2",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            str(tl_mp4),
        ], check=True)

        def phase4(rsec: float):
            if rsec < 215.0:
                return "LAMINAR-TURBULENT TRANSITION", (244, 106, 126)
            if rsec < 355.0:
                return "WATSON · BAKER & DARWIN (1849)", (94, 218, 238)
            if rsec < 465.0:
                return "ORIGIN OF SPECIES & HOOKER", (242, 196, 92)
            return "AZORES 1870 & PICO FLORA MAP", (168, 226, 142)

        vid_res = render_telemetry_overlay_from_video(
            tl_mp4,
            video_dir / "specimen4_fluid_to_botany_overlay.mp4",
            video_dir / "specimen4_poster.png",
            header_title="SPECIMEN #4  ·  FLUID DYNAMICS -> VICTORIAN BOTANY",
            header_sub="Laminar-Turbulent Transition -> Hewett C. Watson (12x Timelapse · 9m40s)",
            phase_fn=phase4,
            nexus_band=(205.0, 230.0, "BOOK SWITCH"),
            out_w=1280,
            out_h=720,
            fps=15,
            crf=25,
            keep_audio=False,
            poster_sec=519.0,
            episode_interval_s=5.0,
            time_scale=12.0,
        )

    nexus_ep = min(len(vid_res["episodes_8"]) - 1, int(round(215.0 / 5.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen4_fluid_to_botany",
        title="SPECIMEN #4 · LAMINAR-TURBULENT TRANSITION -> HEWETT C. WATSON",
        subtitle="Red Springer Fluid Dynamics -> Turquoise Victorian Ecology (9m 40s · 116 Episodes)",
        nexus_label="BOOK TRANSITION (3:35)",
        footer_label="Fieldglass Specimen #4 · Fluid Dynamics to Darwin/Watson Botany",
        episodes_8=vid_res["episodes_8"],
        ep_a004=vid_res["ep_a004"],
        ep_a010=vid_res["ep_a010"],
        ep_times_s=vid_res["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=vid_res["h1_mean"],
        h2_mean=vid_res["h2_mean"],
        duration_sec=vid_res["duration_real_s"],
        hud_prefix="sp4",
    )
    print(f"DONE Specimen #4: mp4={vid_res['mp4_mb']} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    return {"mp4_mb": vid_res["mp4_mb"], "report": rep, "azores": azores, "pico": pico}


def build_specimen5() -> dict:
    print("\n================ BUILDING SPECIMEN #5 (19:48) ================")
    root = DOCS / "specimen5"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"

    plate_specs = [
        ("01_shannon_dft_sampling", "Fig. 6.18 Shannon Sampling & DFT", 68.5, 2.5, 0, None),
        ("02_shear_accelerometers", "Fig. 5.27 Shear Piezo Accelerometers", 84.0, 2.5, 0, None),
        ("03_wheatstone_bridge", "Fig. 5.15 Wheatstone Bridge Circuit", 99.5, 2.5, 0, None),
        ("04_inductive_transducer", "Fig. 5.16 Active/Passive Inductance", 114.8, 2.5, 0, None),
        ("05_batio3_perovskite_cube", "Fig. 4.14 Barium Titanate (BaTiO3)", 167.2, 2.0, 0, None),
        ("06_spatial_overlay_gesture", "Spatial Overlay Gesture over BaTiO3", 145.5, 2.5, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(SRC5, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, rotate_ccw=rot, crop_box=crop)
        pmap[slug] = p
        mm, ss = divmod(int(ts), 60)
        tiles.append((f"{mm}:{ss:02d} · {label}", p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen5.jpg", cols=3, tile_w=420, tile_h=560)

    # Clean vector SVG + Braille of Fig. 4.14 BaTiO3 Perovskite Crystal Structure (from 168s unobstructed!)
    batio3 = build_svg_and_braille(
        pmap["05_batio3_perovskite_cube"],
        assets_dir,
        "batio3_perovskite_crystal",
        title="FIG. 4.14 · BARIUM TITANATE STRUCTURE (BaTiO3)",
        subtitle="Mechanical Characterization of Materials & Wave Dispersion · Spatial Overlay Plate",
        crop_box=(0.48, 0.34, 0.99, 0.61),
        sigma=36.0,
        paper_cutoff=0.93,
        ink_floor=0.42,
        braille_cols=72,
    )
    accel = build_svg_and_braille(
        pmap["02_shear_accelerometers"],
        assets_dir,
        "shear_piezo_accelerometers",
        title="FIG. 5.27 · SHEAR-TYPE PIEZOELECTRIC ACCELEROMETERS",
        subtitle="Annular & Delta Transducers (Bruel & Kjaer) · Mechanical Characterization (Wiley)",
        crop_box=(0.24, 0.12, 0.78, 0.32),
        sigma=38.0,
        paper_cutoff=0.92,
        ink_floor=0.38,
        braille_cols=72,
    )

    # Full real-time voice telemetry video (4m 07s with original audio!)
    def phase5(rsec: float):
        if rsec < 76.0:
            return "SHANNON SAMPLING & DFT", (94, 218, 238)
        if rsec < 138.0:
            return "PIEZO ACCEL & WHEATSTONE BRIDGE", (242, 196, 92)
        if rsec < 185.0:
            return "BaTiO3 SPATIAL OVERLAY PITCH", (244, 106, 126)
        return "MECHANICAL CHARACTERIZATION", (168, 226, 142)

    vid_res = render_telemetry_overlay_from_video(
        SRC5,
        video_dir / "specimen5_materials_batio3_overlay.mp4",
        video_dir / "specimen5_poster.png",
        header_title="SPECIMEN #5  ·  WAVE DISPERSION & BaTiO3 SPATIAL OVERLAY",
        header_sub="Mechanical Characterization of Materials (Wiley) · Live Real-Time Voice Telemetry",
        phase_fn=phase5,
        nexus_band=(142.0, 175.0, "BaTiO3 OVERLAY"),
        out_w=1280,
        out_h=720,
        fps=15,
        crf=27,
        audio_bitrate="80k",
        keep_audio=True,
        poster_sec=168.0,
        episode_interval_s=5.0,
        time_scale=1.0,
    )

    nexus_ep = min(len(vid_res["episodes_8"]) - 1, int(round(146.0 / 5.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen5_materials_batio3",
        title="SPECIMEN #5 · MECHANICAL CHARACTERIZATION & BaTiO3 OVERLAY",
        subtitle="Wiley Materials & Wave Dispersion · Real-Time Voice Field Session (4m 07s)",
        nexus_label="BaTiO3 SPATIAL OVERLAY (2:26)",
        footer_label="Fieldglass Specimen #5 · Mechanical Characterization & BaTiO3 Crystal",
        episodes_8=vid_res["episodes_8"],
        ep_a004=vid_res["ep_a004"],
        ep_a010=vid_res["ep_a010"],
        ep_times_s=vid_res["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=vid_res["h1_mean"],
        h2_mean=vid_res["h2_mean"],
        duration_sec=vid_res["duration_real_s"],
        hud_prefix="sp5",
    )
    print(f"DONE Specimen #5: mp4={vid_res['mp4_mb']} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    return {"mp4_mb": vid_res["mp4_mb"], "report": rep, "batio3": batio3, "accel": accel}


def build_specimen6() -> dict:
    print("\n================ BUILDING SPECIMEN #6 (19:57 PRIVACY-SCRUBBED) ================")
    root = DOCS / "specimen6"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"

    # Extract 4 strictly verified-clean plates (ZERO password slips, ZERO desk cards!)
    plate_specs = [
        ("01_constitution_cover", "Gold-Embossed Constitution Cover", 6.5, 2.0, 0, (0.04, 0.02, 0.96, 0.92)),
        ("02_we_the_people", "We the People Manuscript Facsimile", 66.4, 1.5, 0, (0.02, 0.02, 0.98, 0.62)),
        ("03_declaration_trumbull", "Declaration of Independence Plate", 135.2, 2.0, 0, (0.02, 0.08, 0.98, 0.96)),
        ("04_thumbelina_cat", "Thumbelina ('Thumbs') Cameo", 225.5, 2.5, 0, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(SRC6, plates_dir / f"{slug}.jpg", start_sec=t0, window_sec=win, rotate_ccw=rot, crop_box=crop)
        pmap[slug] = p
        mm, ss = divmod(int(ts), 60)
        tiles.append((f"{mm}:{ss:02d} · {label}", p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen6.jpg", cols=2, tile_w=480, tile_h=540)

    # Vector SVG + Braille of (1) Gold-embossed Constitution cover, (2) Trumbull's Declaration signing engraving
    cover = build_svg_and_braille(
        pmap["01_constitution_cover"],
        assets_dir,
        "constitution_cover_embossed",
        title="THE CONSTITUTION & DECLARATION OF INDEPENDENCE",
        subtitle="Pocket Gilt-Embossed Hardcover · Edge-Field Vector & Braille Study",
        crop_box=(0.14, 0.04, 0.86, 0.72),
        braille_cols=68,
        edge_hybrid=True,
    )
    decl = build_svg_and_braille(
        pmap["03_declaration_trumbull"],
        assets_dir,
        "declaration_of_independence_plate",
        title="THE DECLARATION OF INDEPENDENCE (TRUMBULL PLATE)",
        subtitle="Clean Book-Only Crop · Privacy-Scrubbed Archival Specimen",
        crop_box=(0.04, 0.16, 0.96, 0.56),
        sigma=38.0,
        paper_cutoff=0.92,
        ink_floor=0.35,
        braille_cols=74,
    )

    # Build strictly privacy-scrubbed clean concat video:
    # - Cuts ALL password-slip windows (11..65s, 70..83s, 106..133s, 205..214s, 236..250s)
    # - Masks bottom-right desk-card region (x>=0.44*W, y>=0.60*H) on the book segments (83.5..106s & 133..205s)!
    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)
        segs = [
            (4.5, 10.5, False),     # 6.0s: Gold embossed cover ("Constitution")
            (65.5, 69.5, True),     # 4.0s: We the People (mask corner for safety)
            (83.5, 106.0, True),    # 22.5s: Bill of Rights (mask corner)
            (133.0, 204.5, True),   # 71.5s: Trumbull Declaration + "checklist for future citizens" speech (mask corner)
            (214.0, 235.5, False),  # 21.5s: Helen ("Hi Zoe!") & Thumbelina the cat!
        ]
        seg_paths = []
        for idx, (s0, s1, mask_corner) in enumerate(segs):
            sp = tdir / f"seg_{idx}.mp4"
            vf = "fps=15,scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2"
            if mask_corner:
                # Permanently redact bottom-right corner where desk card sat on Flow Visualization
                vf += ",drawbox=x=230:y=565:w=310:h=395:color=0x0b0f17@1.0:t=fill"
            subprocess.run([
                "ffmpeg", "-y", "-v", "error",
                "-ss", f"{s0:.2f}", "-to", f"{s1:.2f}", "-i", str(SRC6),
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "96k",
                str(sp),
            ], check=True)
            seg_paths.append(sp)

        list_txt = tdir / "concat.txt"
        list_txt.write_text("\n".join(f"file '{p}'" for p in seg_paths) + "\n", encoding="utf-8")
        clean_mp4 = tdir / "clean_specimen6.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
            "-i", str(list_txt), "-c", "copy", str(clean_mp4),
        ], check=True)

        def phase6(rsec: float):
            if rsec < 10.0:
                return "CONSTITUTION & WE THE PEOPLE", (242, 196, 92)
            if rsec < 32.5:
                return "BILL OF RIGHTS (AMENDMENTS I-X)", (94, 218, 238)
            if rsec < 104.0:
                return "DECLARATION · CITIZEN CHECKLIST", (244, 106, 126)
            return "HELEN & THUMBELINA CAMEO", (168, 226, 142)

        vid_res = render_telemetry_overlay_from_video(
            clean_mp4,
            video_dir / "specimen6_constitution_scrubbed_overlay.mp4",
            video_dir / "specimen6_poster.png",
            header_title="SPECIMEN #6  ·  U.S. CONSTITUTION & DECLARATION (SCRUBBED)",
            header_sub="Privacy-Redacted Live Voice Telemetry · Passwords Cut & Desk Card Masked",
            phase_fn=phase6,
            nexus_band=(33.0, 104.0, "DECLARATION"),
            out_w=1280,
            out_h=720,
            fps=15,
            crf=26,
            audio_bitrate="80k",
            keep_audio=True,
            poster_sec=36.0,
            episode_interval_s=4.0,
            time_scale=1.0,
        )

    nexus_ep = min(len(vid_res["episodes_8"]) - 1, int(round(33.0 / 4.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen6_constitution",
        title="SPECIMEN #6 · U.S. CONSTITUTION & DECLARATION (PRIVACY-SCRUBBED)",
        subtitle="Pocket Edition + Trumbull Engraving + Thumbelina Cameo (2m 05s Clean Cut)",
        nexus_label="DECLARATION OF INDEPENDENCE",
        footer_label="Fieldglass Specimen #6 · Privacy-Scrubbed Archival Cut",
        episodes_8=vid_res["episodes_8"],
        ep_a004=vid_res["ep_a004"],
        ep_a010=vid_res["ep_a010"],
        ep_times_s=vid_res["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=vid_res["h1_mean"],
        h2_mean=vid_res["h2_mean"],
        duration_sec=vid_res["duration_real_s"],
        hud_prefix="sp6",
        extra_meta={"privacy_scrubbed": True, "password_segments_removed": True, "desk_card_redacted": True},
    )
    print(f"DONE Specimen #6: mp4={vid_res['mp4_mb']} MB, glyph={rep['chiasm_nexus']['presence_glyph']}")
    return {"mp4_mb": vid_res["mp4_mb"], "report": rep, "cover": cover, "decl": decl}


if __name__ == "__main__":
    r4 = build_specimen4()
    r5 = build_specimen5()
    r6 = build_specimen6()
    summary = {
        "specimen4": {"mp4_mb": r4["mp4_mb"], "glyph": r4["report"]["chiasm_nexus"]["presence_glyph"], "past_A": r4["report"]["chiasm_nexus"]["past_accessible_volume"], "future_A": r4["report"]["chiasm_nexus"]["future_accessible_volume"], "ei": r4["report"]["chiasm_nexus"]["effective_information_bits"], "invariants": r4["report"]["persistent_filtration_tomography"]["structural_invariants"]},
        "specimen5": {"mp4_mb": r5["mp4_mb"], "glyph": r5["report"]["chiasm_nexus"]["presence_glyph"], "past_A": r5["report"]["chiasm_nexus"]["past_accessible_volume"], "future_A": r5["report"]["chiasm_nexus"]["future_accessible_volume"], "ei": r5["report"]["chiasm_nexus"]["effective_information_bits"], "invariants": r5["report"]["persistent_filtration_tomography"]["structural_invariants"]},
        "specimen6": {"mp4_mb": r6["mp4_mb"], "glyph": r6["report"]["chiasm_nexus"]["presence_glyph"], "past_A": r6["report"]["chiasm_nexus"]["past_accessible_volume"], "future_A": r6["report"]["chiasm_nexus"]["future_accessible_volume"], "ei": r6["report"]["chiasm_nexus"]["effective_information_bits"], "invariants": r6["report"]["persistent_filtration_tomography"]["structural_invariants"]},
    }
    print("\n=== SUMMARY #4-#6 ===")
    print(json.dumps(summary, indent=2))
