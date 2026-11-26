#!/usr/bin/env python3
"""Build Fieldglass Specimen #16 — The Poetry Briefcase: 25 Notebooks & ~10,000 Poems for Zoe.

Source:
  - /tmp/zoe_s16/zoe_vid_1795731309153.mp4
    (2026-11-26 16:17, 143.95s, 4K portrait 2160x3840 @ 30fps, full live studio voice)

Nick counts out 20 physical poetry notebooks and 5 manuscript folios (including his
Spring 2011 high-school literary magazine "OUT OF HAND" and a hand-drawn Scarab Beetle
calligram cover) across the living-room rug, then opens a vintage Smith-Corona typewriter
briefcase packed with ~10,000 poems written from age 15 until joining the Army at 21 —
closing with: "So then I just have to give Zoe all of these. And then... she will be as
cool as me. Or cooler."

Generates:
  - 6 curated GPS-scrubbed upright plates + 3x2 contact sheet
  - 2 archival Vector SVGs + 72-col 2x4 Unicode Braille:
      1) Hand-drawn Scarab Beetle Calligram ("Endless Poems" · Nicholas Kloster)
      2) Signed Holograph Autograph ("poem will last forever." — Nicholas Kloster)
  - Full 2m 24s real-time (1.0x) original voice 960x540 Kloster A_tau(p_t) HUD film (<20 MB)
  - ~144-episode (1.0s cadence) SHA-256 sealed GEM Causal Chiasm & Filtration Tomography
  - Social-ready exports in /home/cowboy/fieldglass/exports/specimen16_social/:
      - TikTok 1080x1920 vertical 9:16 stereo MP4 (1.0x real-time, GPS-scrubbed)
      - X.com 138.8s (<140s free-tier cap, zero cut words) Fieldglass HUD MP4
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    build_svg_and_braille,
    extract_plate,
    load_font,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
EXPORTS = Path("/home/cowboy/fieldglass/exports/specimen16_social")
SRC16 = Path("/tmp/zoe_s16/zoe_vid_1795731309153.mp4")


def _extract_exact_4k(src: Path, t_sec: float, out_path: Path) -> Image.Image:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{t_sec:.2f}", "-i", str(src),
            "-frames:v", "1", "-q:v", "2", "-map_metadata", "-1",
            str(out_path),
        ],
        check=True,
    )
    return Image.open(out_path).convert("RGB")


def _build_social_exports(src: Path, hud_mp4: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    tiktok_mp4 = out_dir / "specimen16_tiktok_vertical_1080x1920.mp4"
    x_mp4 = out_dir / "specimen16_x_post_139s_hud.mp4"

    # Build crisp transparent PNG overlay banner for TikTok 1080x1920 (top badge + bottom subtle footer)
    with tempfile.TemporaryDirectory() as tmp:
        ov_png = Path(tmp) / "tiktok_overlay.png"
        ov = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        f_kicker = load_font(22, bold=True)
        f_title = load_font(30, bold=True)
        f_sub = load_font(20, bold=False)

        # Subtle top observatory pill (clear of TikTok top status bar)
        dr.rounded_rectangle([42, 118, 1038, 224], radius=18, fill=(12, 17, 26, 175), outline=(220, 168, 84, 215), width=2)
        dr.text((68, 130), "FIELDGLASS SPECIMEN #16  ·  ARCHIVE FOR ZOE", fill=(220, 168, 84, 255), font=f_kicker)
        dr.text((68, 164), "25 Poetry Notebooks & ~10,000 Poems (Ages 15–21)", fill=(244, 240, 232, 255), font=f_title)

        # Subtle lower strip (above TikTok bottom caption/buttons zone)
        dr.rounded_rectangle([42, 1480, 860, 1544], radius=14, fill=(12, 17, 26, 165), outline=(94, 218, 238, 180), width=2)
        dr.text((64, 1498), "nicholas-michael-kloster.github.io/fieldglass/#specimen-16", fill=(94, 218, 238, 255), font=f_sub)
        ov.save(ov_png)

        print("Rendering TikTok 1080x1920 vertical 1.0x stereo MP4 (GPS-scrubbed)...")
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(src), "-i", str(ov_png),
                "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30[base];[base][1:v]overlay=0:0[v]",
                "-map", "[v]", "-map", "0:a:0",
                "-map_metadata", "-1",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(tiktok_mp4),
            ],
            check=True,
        )

    # X.com 138.8s (< 140.0s X standard limit!) using imperceptible 1.030x tempo over 0..142.9s (zero cut words!)
    print("Rendering X.com <140s Fieldglass HUD MP4 (1.030x pitch-preserved, zero cut words)...")
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-t", "142.9", "-i", str(hud_mp4),
            "-filter_complex", "[0:v]setpts=PTS/1.030[v];[0:a]atempo=1.030[a]",
            "-map", "[v]", "-map", "[a]",
            "-map_metadata", "-1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(x_mp4),
        ],
        check=True,
    )
    return {
        "tiktok_mp4": str(tiktok_mp4),
        "tiktok_mb": round(tiktok_mp4.stat().st_size / 1e6, 2),
        "x_mp4": str(x_mp4),
        "x_mb": round(x_mp4.stat().st_size / 1e6, 2),
    }


def build_specimen16() -> dict:
    print("\n================ BUILDING SPECIMEN #16 (THE POETRY BRIEFCASE · 25 BOOKS & ~10,000 POEMS) ================")
    root = DOCS / "specimen16"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1) Extract 6 razor-sharp GPS-scrubbed hero plates
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # Plate 01: Full 25-notebook floor constellation (sharpness peak 287.0 at 104.60s!)
        im_104 = _extract_exact_4k(SRC16, 104.60, tmp_p / "raw_104.jpg")
        p01 = plates_dir / "01_notebooks_constellation_25.jpg"
        im01 = im_104.copy()
        im01.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01.save(p01, quality=92, optimize=True)

        # Plate 02: Hand-drawn Scarab Beetle Calligram title page — rotated 90° CW + deskewed upright!
        w4, h4 = im_104.size
        beetle_crop = im_104.crop((int(w4 * 0.165), int(h4 * 0.785), int(w4 * 0.555), int(h4 * 0.960)))
        beetle_up = beetle_crop.transpose(Image.Transpose.ROTATE_270).rotate(
            -9.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(236, 232, 224)
        )
        bw, bh = beetle_up.size
        beetle_clean = beetle_up.crop((int(bw * 0.14), int(bh * 0.11), int(bw * 0.87), int(bh * 0.86)))
        p02 = plates_dir / "02_scarab_beetle_calligram_cover.jpg"
        beetle_clean.save(p02, quality=94, optimize=True)
        print(f"  Plate 02_scarab_beetle_calligram_cover (4K deskewed upright): {beetle_clean.size}")

        # Plate 03: OUT OF HAND · Spring 2011 high-school literary magazine
        ts3, p03 = extract_plate(
            SRC16, plates_dir / "03_out_of_hand_spring_2011.jpg",
            start_sec=65.2, window_sec=1.2, sample_fps=4, max_dim=1600,
        )
        print(f"  Plate 03_out_of_hand_spring_2011 @ {ts3:.2f}s")

        # Plate 04: Vintage Smith-Corona typewriter briefcase packed with ~10,000 poems
        ts4, p04 = extract_plate(
            SRC16, plates_dir / "04_smith_corona_briefcase_vault.jpg",
            start_sec=92.2, window_sec=1.6, sample_fps=4, max_dim=1600,
        )
        print(f"  Plate 04_smith_corona_briefcase_vault @ {ts4:.2f}s")

        # Plate 05: "poem will last forever." — Nicholas Kloster signed sheet (110.70s!)
        im_110 = _extract_exact_4k(SRC16, 110.70, tmp_p / "raw_110.jpg")
        p05 = plates_dir / "05_poem_will_last_forever_signed.jpg"
        im05 = im_110.copy()
        im05.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05.save(p05, quality=92, optimize=True)

        # Deskewed thumb-free crop of "poem will last forever." for museum SVG engraving!
        ws, hs = im_110.size
        sig_raw = im_110.crop((int(ws * 0.00), int(hs * 0.27), int(ws * 0.96), int(hs * 0.65)))
        sig_rot = sig_raw.rotate(-22.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(232, 226, 218))
        rw, rh = sig_rot.size
        sig_svg_src = tmp_p / "sig_deskewed.png"
        sig_clean = sig_rot.crop((int(rw * 0.01), int(rh * 0.30), int(rw * 0.90), int(rh * 0.78)))
        sig_clean.save(sig_svg_src)

        # Plate 06: Full handwritten poem ("trying to sketch the hips of the moon... on my broken typewriter")
        ts6, p06 = extract_plate(
            SRC16, plates_dir / "06_broken_typewriter_poem.jpg",
            start_sec=113.3, window_sec=1.2, sample_fps=4, max_dim=1600,
        )
        print(f"  Plate 06_broken_typewriter_poem @ {ts6:.2f}s")

        tiles = [
            ("01:45 · 25 Notebooks & Folios on Rug", p01),
            ("01:45 · Scarab Beetle Calligram Cover", p02),
            ("01:05 · OUT OF HAND (Spring 2011)", p03),
            ("01:33 · Smith-Corona Briefcase Vault", p04),
            ("01:51 · \"poem will last forever.\"", p05),
            ("01:54 · \"on my broken typewriter\"", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen16.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Archival Vector SVGs + 72-Col 2x4 Braille
        beetle_svg = build_svg_and_braille(
            p02,
            assets_dir,
            "scarab_beetle_calligram",
            title="ENDLESS POEMS — SCARAB BEETLE CALLIGRAM COVER",
            subtitle="Original Pen Drawing & Calligram · Nicholas Kloster (Specimen #16 · 2026-11-26)",
            crop_box=(0.25, 0.16, 0.87, 0.84),
            sigma=34.0,
            paper_cutoff=0.92,
            ink_floor=0.38,
            gamma=1.20,
            levels=(0.14, 0.34, 1.2),
            braille_cols=72,
        )

        sig_svg = build_svg_and_braille(
            sig_svg_src,
            assets_dir,
            "poem_will_last_forever_autograph",
            title="\"POEM WILL LAST FOREVER.\" — NICHOLAS KLOSTER",
            subtitle="Signed Holograph Manuscript Leaf from Smith-Corona Briefcase (Specimen #16)",
            crop_box=(0.02, 0.02, 0.98, 0.98),
            sigma=38.0,
            paper_cutoff=0.90,
            ink_floor=0.36,
            gamma=1.22,
            levels=(0.18, 0.38, 1.2),
            braille_cols=72,
        )

        # 3) Pre-transcode ONCE from 4K portrait -> clean 304x540 @ 15fps stereo AAC (GPS-scrubbed!)
        clean_mp4 = tmp_p / "briefcase_clean_15fps.mp4"
        print("Pre-transcoding 2m 24s 4K portrait -> 304x540 @ 15fps stereo (GPS-scrubbed)...")
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(SRC16),
                "-vf", "fps=15,scale=304:540:force_original_aspect_ratio=decrease,pad=304:540:(ow-iw)/2:(oh-ih)/2",
                "-map_metadata", "-1",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
                "-c:a", "aac", "-ac", "2", "-b:a", "96k",
                str(clean_mp4),
            ],
            check=True,
        )
        print(f"  Intermediate ready: {clean_mp4.stat().st_size / 1e6:.2f} MB")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 53.0:
                return "COUNTING 20 POETRY NOTEBOOKS", (94, 218, 238)
            if rsec < 76.0:
                return "5 MANUSCRIPTS & OUT OF HAND (2011)", (242, 196, 92)
            if rsec < 106.0:
                return "SMITH-CORONA BRIEFCASE (~10,000 POEMS)", (244, 106, 126)
            if rsec < 132.0:
                return "\"POEM WILL LAST FOREVER.\" · HOLOGRAPHS", (195, 162, 255)
            return "\"GIVE ZOE ALL OF THESE\"", (168, 226, 142)

        out_mp4 = video_dir / "specimen16_poetry_briefcase_overlay.mp4"
        poster_png = video_dir / "specimen16_poster.png"
        ov = render_telemetry_overlay_from_video(
            clean_mp4,
            out_mp4,
            poster_png,
            header_title="SPECIMEN #16 · THE POETRY BRIEFCASE (25 BOOKS & ~10,000 POEMS)",
            header_sub="Ages 15–21 Complete Holograph Vault -> \"Give Zoe All of These\"",
            phase_fn=phase_fn,
            nexus_band=(72.0, 82.0, "NEXUS · 25 BOOKS->BRIEFCASE VAULT"),
            out_w=960,
            out_h=540,
            fps=15,
            crf=24,
            audio_bitrate="96k",
            keep_audio=True,
            poster_sec=104.6,
            episode_interval_s=1.0,
            time_scale=1.0,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~144 episodes)
    nexus_ep = int(round(76.0 / 1.0))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen16_poetry_briefcase",
        title="SPECIMEN #16 · THE POETRY BRIEFCASE (25 NOTEBOOKS & ~10,000 POEMS)",
        subtitle="2m 24s Full Real-Time Voice · Ages 15–21 Holograph Archive for Zoe",
        nexus_label="25 BOOKS -> BRIEFCASE (1:16)",
        footer_label="Fieldglass Specimen #16 · The Poetry Briefcase (Nicholas Kloster)",
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp16",
    )

    # 5) Render TikTok & X.com ready social exports (outside docs/)
    social = _build_social_exports(SRC16, out_mp4, EXPORTS)

    summary = {
        "specimen16": {
            "mp4_mb": ov["mp4_mb"],
            "duration_real_s": round(ov["duration_real_s"], 2),
            "episode_count": rep["episode_count"],
            "a_004_mean": rep.get("a_004_mean"),
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
            "social": social,
        }
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build_specimen16()
