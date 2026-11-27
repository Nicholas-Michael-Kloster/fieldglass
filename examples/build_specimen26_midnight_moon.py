#!/usr/bin/env python3
"""Build Fieldglass Specimen #26 — "Midnight Moon" (July 2012 – Sept 2013 Multi-Ink Pocket Notebooks).

Source:
  - /tmp/zoe_s26/s26.mp4 (zoe_vid_1795742182023.mp4)
    (2026-11-26 19:34, notebook capture [0:00–11:20 / 680.0s], 4K portrait 2160x3840 @ 30fps)

Cover-to-cover capture of Nicholas Kloster's burgundy-backed July 2012 ruled pocket
notebook (7-9-12 through red/orange-ink and blue-pen spreads) followed by a companion
unlined Sept 2013 pocket notebook (9/9/13 · 3:49 AM). Scoped cleanly to the 11m 20s
notebook capture prior to the closing YouTube music playback. Highlights "A Thornless
Rose in My Mouth" (7-9-12), "Midnight Chicago" (blue-pen leaf), "Midnight Moon, Do You
Ever Write Poems of Me?" (signed), Nick's surprise crimson/red-ink spread ("6AM
Wednesday"), "Plastic Vegas / Nomadic Crimson Eyes", and "A City of Roof Tops" (9/9/13).

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "Midnight Moon, Do You Ever Write Poems of Me?" (Signed Nicholas Kloster)
      2) "A Thornless Rose in My Mouth" (7-9-12 · Signed Nicholas Kloster)
  - Fast keyframe-decoded 1280x720 13x silent Kloster A_tau(p_t) telemetry reel (~52s, <10 MB)
  - ~114-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
    build_svg_and_braille,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC26 = Path("/tmp/zoe_s26/s26.mp4")


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


def build_specimen26() -> dict:
    print("\n================ BUILDING SPECIMEN #26 ('MIDNIGHT MOON' · JULY 2012 – SEPT 2013) ================")
    root = DOCS / "specimen26"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K plates
        im01 = _extract_exact_4k(SRC26, 16.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_thornless_rose_jul9_2012.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC26, 241.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_midnight_chicago_blue_pen.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC26, 471.5, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_midnight_moon_write_poems.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC26, 598.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_crimson_red_ink_6am_wednesday.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC26, 664.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_plastic_vegas_crimson_eyes.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC26, 666.5, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_city_of_rooftops_sep9_2013.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:16 · 7-9-12: 'Thornless Rose'", p01),
            ("04:01 · Blue Ink: 'Midnight Chicago'", p02),
            ("07:51 · 'Midnight Moon' (Signed)", p03),
            ("09:58 · Red Ink: '6AM Wednesday'", p04),
            ("11:04 · 'Plastic Vegas'", p05),
            ("11:06 · 9/9/13: 'City of Roof Tops'", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen26.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        pad = 24
        # SVG #1: "Midnight Moon, Do You Ever Write Poems of Me?" (Signed Nicholas Kloster, 471.5s)
        w3, h3 = im03.size
        arr3 = np.asarray(im03, dtype=np.uint8)
        p3_col = tuple(int(v) for v in np.median(arr3[int(h3 * 0.44):int(h3 * 0.56), int(w3 * 0.65):int(w3 * 0.85)].reshape(-1, 3), axis=0))
        poly3 = [
            (int(w3 * 0.352), int(h3 * 0.160)),
            (int(w3 * 0.975), int(h3 * 0.235)),
            (int(w3 * 0.845), int(h3 * 0.822)),
            (int(w3 * 0.140), int(h3 * 0.738)),
        ]
        m3 = Image.new("L", (w3, h3), 0)
        ImageDraw.Draw(m3).polygon(poly3, fill=255)
        c3 = Image.new("RGB", (w3, h3), p3_col)
        c3.paste(im03, (0, 0), m3)
        rot3 = c3.rotate(17.8, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p3_col)
        m3_rot = m3.rotate(17.8, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m3_rot.getbbox()
        rw3, rh3 = rot3.size
        moon_src = tmp_p / "midnight_moon_clean.png"
        rot3.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw3, bx1 + pad), min(rh3, by1 + pad))).save(moon_src)

        build_svg_and_braille(
            moon_src,
            assets_dir,
            "midnight_moon_write_poems_of_me",
            title='"MIDNIGHT MOON, DO YOU EVER WRITE POEMS OF ME?"',
            subtitle="Signed Pencil Holograph Leaf · July 2012 Pocket Notebook (Specimen #26)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=24.0,
            paper_cutoff=0.925,
            ink_floor=0.46,
            gamma=1.02,
            levels=(0.08, 0.21, 1.2),
            braille_cols=72,
        )

        # SVG #2: "A Thornless Rose in My Mouth" (7-9-12 · Signed Nicholas Kloster, 16.0s)
        w1, h1 = im01.size
        arr1 = np.asarray(im01, dtype=np.uint8)
        p1_col = tuple(int(v) for v in np.median(arr1[int(h1 * 0.18):int(h1 * 0.30), int(w1 * 0.72):int(w1 * 0.90)].reshape(-1, 3), axis=0))
        poly1 = [
            (int(w1 * 0.285), int(h1 * 0.165)),
            (int(w1 * 0.992), int(h1 * 0.175)),
            (int(w1 * 0.992), int(h1 * 0.855)),
            (int(w1 * 0.235), int(h1 * 0.815)),
        ]
        m1 = Image.new("L", (w1, h1), 0)
        ImageDraw.Draw(m1).polygon(poly1, fill=255)
        c1 = Image.new("RGB", (w1, h1), p1_col)
        c1.paste(im01, (0, 0), m1)
        rot1 = c1.rotate(3.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p1_col)
        m1_rot = m1.rotate(3.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m1_rot.getbbox()
        rw1, rh1 = rot1.size
        rose_src = tmp_p / "thornless_rose_clean.png"
        rot1.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw1, bx1 + pad), min(rh1, by1 + pad))).save(rose_src)

        build_svg_and_braille(
            rose_src,
            assets_dir,
            "thornless_rose_jul9_2012",
            title='"A THORNLESS ROSE IN MY MOUTH" (7-9-12 · NICHOLAS KLOSTER)',
            subtitle="Signed Holograph Leaf · July 2012 Pocket Notebook (Specimen #26)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.17, 0.37, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 13x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~52s)
        #    Scoped cleanly to [0:00–11:20 / 680.0s] notebook capture prior to YouTube music playback.
        fps = 15
        target_frames = 780  # 52.0s out for 680.0s real (~13.08x)
        vw, vh = 406, 720
        real_dur = 680.0
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 11m 20s notebook span -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC26), "-t", f"{real_dur:.2f}",
            "-vsync", "vfr",
            "-vf", f"scale={vw}:{vh}:force_original_aspect_ratio=decrease,pad={vw}:{vh}:(ow-iw)/2:(oh-ih)/2:color=#0b111b",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ])
        fbytes = vw * vh * 3
        nf_raw = len(raw) // fbytes
        arr_raw = np.frombuffer(raw[: nf_raw * fbytes], dtype=np.uint8).reshape(nf_raw, vh, vw, 3)
        idxs = np.linspace(0, max(0, nf_raw - 1), target_frames).round().astype(int)
        arr = arr_raw[idxs]
        print(f"  Decoded {nf_raw} keyframes -> {len(arr)} timelapse frames")

        tl_mp4 = tmp_p / "midnight_moon_tl.mp4"
        enc = subprocess.Popen([
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{vw}x{vh}", "-r", str(fps), "-i", "-",
            "-an", "-map_metadata", "-1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-pix_fmt", "yuv420p", str(tl_mp4),
        ], stdin=subprocess.PIPE)
        assert enc.stdin is not None
        enc.stdin.write(arr.tobytes())
        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError("Specimen #26 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 105:
                return "7-9-12 · THORNLESS", (94, 218, 238)
            if rsec < 235:
                return "PEACOCK WINGS", (242, 196, 92)
            if rsec < 350:
                return "BLUE INK · CHICAGO", (195, 162, 255)
            if rsec < 515:
                return "MIDNIGHT MOON", (244, 106, 126)
            if rsec < 635:
                return "RED INK · 6AM WED", (168, 226, 142)
            return "9/9/13 · ROOF TOPS", (242, 196, 92)

        out_mp4 = video_dir / "specimen26_midnight_moon_overlay.mp4"
        poster_png = video_dir / "specimen26_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #26 · "MIDNIGHT MOON" (JULY 2012 – SEPT 2013)',
            header_sub="Multi-Ink Pocket Notebooks · Black, Blue & Crimson Pen (13x Telemetry Reel)",
            phase_fn=phase_fn,
            nexus_band=(455.0, 492.0, 'NEXUS · "MIDNIGHT MOON" LEAF'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=471.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~114 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 471.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen26_midnight_moon",
        title='SPECIMEN #26 · "MIDNIGHT MOON" (JULY 2012 – SEPT 2013)',
        subtitle='11m 20s Pocket Folios · "Midnight Moon", "Thornless Rose", Blue & Crimson Ink',
        nexus_label='"MIDNIGHT MOON" (7:51)',
        footer_label='Fieldglass Specimen #26 · "Midnight Moon" (2012–2013) Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp26",
    )

    summary = {
        "specimen26": {
            "mp4_mb": ov["mp4_mb"],
            "duration_real_s": round(ov["duration_real_s"], 2),
            "episode_count": rep["episode_count"],
            "a_004_mean": rep.get("a_004_mean"),
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build_specimen26()
