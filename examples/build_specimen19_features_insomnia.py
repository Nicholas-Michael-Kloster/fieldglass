#!/usr/bin/env python3
"""Build Fieldglass Specimen #19 — "Features and Insomnia" (Sept – Oct 2012 Illustrated Folio).

Source:
  - /tmp/zoe_s19/zoe_vid_1795737568039.mp4
    (2026-11-26 18:08, 9m 07s [546.73s], 4K portrait 2160x3840 @ 30fps)

Cover-to-cover documentation of Nicholas Kloster's stitched kraft-paper journal
"Features and Insomnia" (Sept 11 – Oct 3, 2012), opening with its hand-labeled dark
cover and spanning "Pride Can't Be Bought / 24/7 Cafes" (Sep 11, 12), "Dear Fly" (Sep 18),
signed verses (Sep 27), "Things That Make Sounds", a candid studio cameo, and the
unforgettable closing loose leaf: the illustrated poem & fine-line surrealist pen drawing
"Half Sketched Statue / Poor Gardener" (Sep 11, 12).

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Sepia-Ink Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "Half Sketched Statue / Poor Gardener" Illustrated Pen Drawing & Poem (Sep 11, 12)
      2) "Pride Can't Be Bought / 24/7 Cafes" Complete Holograph Poem (Sep 11, 12)
  - Fast keyframe-decoded 1280x720 11x silent Kloster A_tau(p_t) telemetry reel (~50s, <9 MB)
  - ~91-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
    extract_plate,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC19 = Path("/tmp/zoe_s19/zoe_vid_1795737568039.mp4")


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


def build_specimen19() -> dict:
    print("\n================ BUILDING SPECIMEN #19 ('FEATURES AND INSOMNIA' · SEPT 2012) ================")
    root = DOCS / "specimen19"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp upright GPS-scrubbed hero plates
        im01 = _extract_exact_4k(SRC19, 9.2, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_features_and_insomnia_cover.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC19, 66.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_pride_cant_be_bought_247_cafes.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC19, 318.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_dear_fly_sep18.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC19, 413.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_signed_leaf_sep27.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        ts5, p05 = extract_plate(
            SRC19, plates_dir / "05_studio_cameo_october.jpg",
            start_sec=500.5, window_sec=2.0, sample_fps=4, max_dim=1600,
        )
        print(f"  Plate 05_studio_cameo_october @ {ts5:.1f}s")

        im06 = _extract_exact_4k(SRC19, 540.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_half_sketched_statue_drawing.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:09 · Cover: 'Features and Insomnia'", p01),
            ("01:06 · Sep 11: 'Pride Can't Be Bought'", p02),
            ("05:18 · Sep 18: 'Dear Fly'", p03),
            ("06:53 · Sep 27: Signed Leaf", p04),
            ("08:21 · Studio Cameo", p05),
            ("09:00 · 'Half Sketched Statue' Drawing", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen19.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Museum Archival Sepia-Ink Vector SVGs + 72-Col 2x4 Braille Broadsides!
        # SVG #1: "Half Sketched Statue / Poor Gardener" Illustrated Pen Drawing & Poem (Sep 11, 12)
        #   Clean inner-paper polygon strictly avoiding the torn edge, thumb & right fold shadow!
        w6, h6 = im06.size
        arr6 = np.asarray(im06, dtype=np.uint8)
        p6_col = tuple(int(v) for v in np.median(arr6[int(h6 * 0.14):int(h6 * 0.30), int(w6 * 0.65):int(w6 * 0.85)].reshape(-1, 3), axis=0))
        poly6 = [
            (int(w6 * 0.088), int(h6 * 0.096)),
            (int(w6 * 0.880), int(h6 * 0.096)),
            (int(w6 * 0.885), int(h6 * 0.680)),
            (int(w6 * 0.720), int(h6 * 0.722)),
            (int(w6 * 0.138), int(h6 * 0.722)),
            (int(w6 * 0.125), int(h6 * 0.450)),
        ]
        mask6 = Image.new("L", (w6, h6), 0)
        ImageDraw.Draw(mask6).polygon(poly6, fill=255)
        clean6 = Image.new("RGB", (w6, h6), p6_col)
        clean6.paste(im06, (0, 0), mask6)
        statue_src = tmp_p / "statue_clean.png"
        clean6.crop((int(w6 * 0.088), int(h6 * 0.094), int(w6 * 0.885), int(h6 * 0.725))).save(statue_src)

        statue_svg = build_svg_and_braille(
            statue_src,
            assets_dir,
            "half_sketched_statue_drawing_sep11",
            title='"HALF SKETCHED STATUE" — ORIGINAL ILLUSTRATED POEM (SEP 11, 12)',
            subtitle='Fine-Line Pen Drawing & Manuscript · "Features and Insomnia" (Specimen #19)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=42.0,
            paper_cutoff=0.92,
            ink_floor=0.42,
            gamma=1.18,
            levels=(0.13, 0.32, 1.2),
            braille_cols=76,
        )

        # SVG #2: "Pride Can't Be Bought / 24/7 Cafes" (Sep 11, 12) — 100% spotless hand-free leaf!
        w2, h2 = im02.size
        p2_col = tuple(int(v) for v in np.median(np.asarray(im02)[int(h2 * 0.25):int(h2 * 0.50), int(w2 * 0.75):int(w2 * 0.92)].reshape(-1, 3), axis=0))
        im02_lvl = im02.rotate(3.0, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=p2_col)
        pride_src = tmp_p / "pride_clean.png"
        im02_lvl.crop((int(w2 * 0.165), int(h2 * 0.082), int(w2 * 0.985), int(h2 * 0.865))).save(pride_src)

        pride_svg = build_svg_and_braille(
            pride_src,
            assets_dir,
            "pride_cant_be_bought_sep11",
            title='"PRIDE CAN\'T BE BOUGHT / 24/7 CAFES" (SEP 11, 12)',
            subtitle='Kraft-Paper Holograph Poem · "Features and Insomnia" (Specimen #19)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=44.0,
            paper_cutoff=0.925,
            ink_floor=0.44,
            gamma=1.18,
            levels=(0.14, 0.34, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 11x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~50s)
        fps = 15
        target_frames = 750  # 50.0s out for 546.73s real (~10.93x)
        vw, vh = 406, 720
        real_dur = 546.73
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 9m 07s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC19),
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

        tl_mp4 = tmp_p / "insomnia_tl.mp4"
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
            raise RuntimeError("Specimen #19 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 55:
                return "COVER · FEATURES & INSOMNIA", (94, 218, 238)
            if rsec < 160:
                return "SEP 11 · PRIDE & 24/7 CAFES", (242, 196, 92)
            if rsec < 290:
                return "MID-FOLIO · REVERSED PAGES", (195, 162, 255)
            if rsec < 395:
                return 'SEP 18 · "DEAR FLY"', (244, 106, 126)
            if rsec < 515:
                return "SEP 27–OCT 3 · SIGNED VERSES", (168, 226, 142)
            return "HALF SKETCHED STATUE SKETCH", (242, 196, 92)

        out_mp4 = video_dir / "specimen19_features_insomnia_overlay.mp4"
        poster_png = video_dir / "specimen19_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #19 · "FEATURES AND INSOMNIA" (SEPT–OCT 2012)',
            header_sub='"Pride Can\'t Be Bought", "Dear Fly" & Illustrated "Half Sketched Statue" (11x)',
            phase_fn=phase_fn,
            nexus_band=(308.0, 330.0, 'NEXUS · "DEAR FLY" (5:18)'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=540.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~91 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 318.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen19_features_insomnia",
        title='SPECIMEN #19 · "FEATURES AND INSOMNIA" (SEPT 2012 ILLUSTRATED FOLIO)',
        subtitle='9m 07s Folio · "Pride Can\'t Be Bought", "Dear Fly" & "Half Sketched Statue" Drawing',
        nexus_label='"DEAR FLY" LEAF (5:18)',
        footer_label='Fieldglass Specimen #19 · "Features and Insomnia" (2012) Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp19",
    )

    summary = {
        "specimen19": {
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
    build_specimen19()
