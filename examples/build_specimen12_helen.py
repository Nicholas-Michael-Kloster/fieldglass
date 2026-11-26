#!/usr/bin/env python3
"""Build Fieldglass Specimen #12 — Dr. Helen Ruth Horkan: Pluripotent Stem Cells,
Developmental Biology & Chromatin ("From the Minute You're Born").

Source: /home/cowboy/fieldglass_ics/zoe_vid_1795664242948/zoe_vid_1795664242948.mp4
(21:57, 19m 44s, portrait 2160x3840 @ 120fps, full live studio voice).

Preserves 100% of Dr. Helen Ruth Horkan's complete 19m 44s live science lecture & dialogue:
  - Act I (0:00-5:40): Standing Presenter Mode before the chalk Cnidarian/Jellyfish
    blackboard ("From the minute you're born, you're dying" — DNA damage, ROS,
    pluripotent stem cells in worms/corals/jellyfish/anemones, bioethics & equity).
  - Act II (5:40-10:15): Seated Developmental Biology Masterclass (primordial germ cells,
    meiosis I & II, protamines, synaptonemal complex & recombination, zygote -> blastomere
    -> gastrulation [endoderm/ectoderm/mesoderm], and apoptosis separating webbed fingers).
  - Act III (10:15-19:44): Folding-Genome / Rotary-Phone Time Analogy -> Chromatin,
    Histones ("Beads on a String"), Epigenetic Expression & DNA Fiber Precipitation.

Generates:
  - 6 crisp studio & chalkboard portrait plates + 3x2 contact sheet
  - Inverted-chalk Vector SVG + 2x4 Braille of Dr. Helen's hand-drawn Chalkboard Jellyfish
  - Edge-field Vector SVG + 2x4 Braille portrait of Dr. Helen in standing presenter mode
  - Full 19m 44s real-time original voice 960x540 Kloster A_tau(p_t) telemetry film (<30 MB)
  - 237-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    build_svg_and_braille,
    extract_plate,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC12 = Path("/home/cowboy/fieldglass_ics/zoe_vid_1795664242948/zoe_vid_1795664242948.mp4")


def _detect_hwaccel() -> list[str]:
    """Return ffmpeg CUDA hwaccel flags if hevc_cuvid works on this GPU, else []."""
    try:
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-hwaccel", "cuda", "-t", "1", "-i", str(SRC12), "-f", "null", "-"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        if r.returncode == 0:
            return ["-hwaccel", "cuda"]
    except Exception:
        pass
    return []


def build_specimen12() -> dict:
    print("\n================ BUILDING SPECIMEN #12 (DR. HELEN RUTH HORKAN · 19m 44s FULL VOICE) ================")
    root = DOCS / "specimen12"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    # 1) Extract 6 sharp studio & chalkboard plates across all 3 acts
    plate_specs = [
        ("01_presenter_mode_stem_cells", "01:51 · Presenter Mode: Stem Cells", 110.0, 2.5, None),
        ("02_ocean_of_aliens_lecture", "03:05 · Ocean of Aliens & DNA Repair", 184.0, 2.5, None),
        ("03_chalkboard_jellyfish_closeup", "06:47 · Hand-Drawn Chalk Jellyfish", 406.0, 2.0, (0.00, 0.34, 1.00, 0.64)),
        ("04_meiosis_and_gastrulation", "08:01 · Meiosis & Gastrulation", 480.0, 2.5, None),
        ("05_chromatin_beads_on_string", "14:11 · Chromatin & Histones", 850.0, 2.5, None),
        ("06_studio_joy_outtake", "16:39 · Studio Joy & Outtake", 998.0, 2.5, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, crop in plate_specs:
        ts, p = extract_plate(
            SRC12,
            plates_dir / f"{slug}.jpg",
            start_sec=t0,
            window_sec=win,
            sample_fps=2,
            crop_box=crop,
            max_dim=1600,
        )
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s")
    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen12.jpg", cols=3, tile_w=420, tile_h=560)

    # 2) Vector SVG #1: Inverted-chalk Haeckel-style engraving of Dr. Helen's Chalkboard Jellyfish!
    #    Use 06_studio_joy_outtake.jpg (16:39) where Helen leans back, exposing 100% of the dome & tentacles!
    with tempfile.TemporaryDirectory() as tmp:
        chalk_inv = Path(tmp) / "chalk_inverted.png"
        im_joy = Image.open(pmap["06_studio_joy_outtake"]).convert("RGB")
        w, h = im_joy.size
        crop_im = im_joy.crop((int(w * 0.055), int(h * 0.418), int(w * 0.66), int(h * 0.675)))
        crop_im.save(plates_dir / "03_chalkboard_jellyfish_closeup.jpg", quality=92, optimize=True)
        inv_l = ImageOps.autocontrast(ImageOps.invert(crop_im.convert("L")), cutoff=2)
        inv_l.convert("RGB").save(chalk_inv)
        jelly_svg = build_svg_and_braille(
            chalk_inv,
            assets_dir,
            "helen_chalkboard_jellyfish",
            title="CNIDARIAN / JELLYFISH CHALKBOARD DIAGRAM · HELEN :)",
            subtitle="Inverted Studio Chalkboard · Dr. Helen Ruth Horkan (Specimen #12 · 2026-11-25)",
            sigma=32.0,
            paper_cutoff=0.91,
            ink_floor=0.35,
            gamma=1.18,
            levels=(0.11, 0.28, 1.2),
            braille_cols=76,
        )

    # 3) Vector SVG #2: Edge-field portrait of Dr. Helen standing in presenter mode
    portrait_svg = build_svg_and_braille(
        pmap["01_presenter_mode_stem_cells"],
        assets_dir,
        "helen_presenter_portrait",
        title="DR. HELEN RUTH HORKAN · PRESENTER MODE",
        subtitle="Pluripotent Stem Cells, Developmental Biology & Chromatin (19m 44s Studio Lecture)",
        crop_box=(0.06, 0.08, 0.94, 0.88),
        braille_cols=68,
        edge_hybrid=True,
    )

    # 4) Pre-transcode ONCE from 4K 120fps to clean portrait 304x540 @ 10fps + 64k AAC audio
    #    so the two-pass telemetry HUD overlay renders in ~25 seconds!
    hw = _detect_hwaccel()
    print(f"Pre-transcoding 19m 44s 4K 120fps -> 304x540 @ 10fps (hwaccel={hw or 'cpu'})...")
    with tempfile.TemporaryDirectory() as tmp:
        clean_mp4 = Path(tmp) / "helen_clean_10fps.mp4"
        cmd = ["ffmpeg", "-y", "-v", "error"] + hw + [
            "-i", str(SRC12),
            "-vf", "fps=10,scale=304:540:force_original_aspect_ratio=decrease,pad=304:540:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
            "-c:a", "aac", "-ac", "1", "-b:a", "64k",
            str(clean_mp4),
        ]
        subprocess.run(cmd, check=True)
        print(f"  Intermediate ready: {clean_mp4.stat().st_size / 1e6:.2f} MB")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 95:
                return "STUDIO SETUP & PRESENTER MODE", (94, 218, 238)
            if rsec < 340:
                return "PLURIPOTENT STEM CELLS & ETHICS", (242, 196, 92)
            if rsec < 615:
                return "MEIOSIS, GASTRULATION & APOPTOSIS", (244, 106, 126)
            if rsec < 940:
                return "FOLDING GENOME & ROTARY TIME", (195, 162, 255)
            return "CHROMATIN, HISTONES & DNA FIBERS", (168, 226, 142)

        out_mp4 = video_dir / "specimen12_dr_helen_biology_overlay.mp4"
        poster_png = video_dir / "specimen12_poster.png"
        ov = render_telemetry_overlay_from_video(
            clean_mp4,
            out_mp4,
            poster_png,
            header_title="SPECIMEN #12 · DR. HELEN RUTH HORKAN (FULL 19m44s VOICE)",
            header_sub="Stem Cells, Regeneration, Meiosis, Gastrulation, Apoptosis & Chromatin",
            phase_fn=phase_fn,
            nexus_band=(330.0, 355.0, "NEXUS · PRESENTER->MASTERCLASS"),
            out_w=960,
            out_h=540,
            fps=10,
            crf=28,
            audio_bitrate="64k",
            keep_audio=True,
            poster_sec=111.0,
            episode_interval_s=5.0,
            time_scale=1.0,
        )

    # 5) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (237 episodes)
    nexus_ep = int(round(340.0 / 5.0))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen12_dr_helen_biology",
        title="SPECIMEN #12 · DR. HELEN RUTH HORKAN (STEM CELLS & CHROMATIN)",
        subtitle="19m 44s Full Real-Time Lecture · Pluripotent Stem Cells, Meiosis, Apoptosis & Histones",
        nexus_label="PRESENTER -> MASTERCLASS (5:40)",
        footer_label="Fieldglass Specimen #12 · Dr. Helen Ruth Horkan Studio Biology Lecture",
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp12",
    )

    print(f"DONE Specimen #12: mp4={ov['mp4_mb']} MB, episodes={rep['episode_count']}, glyph={rep['chiasm_nexus']['presence_glyph']}")
    print(json.dumps({
        "specimen12": {
            "mp4_mb": ov["mp4_mb"],
            "episode_count": rep["episode_count"],
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }, indent=2))
    return {"ov": ov, "report": rep, "jelly_svg": jelly_svg, "portrait_svg": portrait_svg}


if __name__ == "__main__":
    build_specimen12()
