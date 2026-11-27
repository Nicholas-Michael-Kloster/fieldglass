#!/usr/bin/env python3
"""Build Fieldglass Specimen #25 — "Neruda and I" (Dec 2012 – Oct 2013 Complete Year-Long Journal).

Source:
  - /tmp/zoe_s25/s25_5g4.mp4 (zoe_vid_1795740868240.mp4)
    (2026-11-26 19:12, 17m 44s [1064.48s], 4K portrait 2160x3840 @ 30fps)

Milestone 25th Fieldglass specimen: a complete 17m 44s cover-to-cover walkthrough of
Nicholas Kloster's year-long 2012–2013 ruled poetry journal, spanning Christmas Eve 2012
("Never Return to the Past / Willow Tree in the Kansas Rain", 12/24/12), "The Coffee Pot
Is Up / Neruda and I" (12/28/12 · 2:56 AM), "We All Hum Melancholy / Neruda Is Silent"
(1/5/13), "Tiny Neon Lit Cafe / Playing Jazz, Playing Beethoven" (2/11/13), "If I Were
Able to Run Forever" (2/12/13), and closing with "Dressed in the Night / Eyes That
Confuse the Lightning Bugs" (Oct 29, 2013). Includes Nick's studio reflections on Pablo
Neruda, Thelonious Monk, and how handwritten notebook impressions press into the reverse
side of the sheet "like vinyl... music in the rivets."

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Bookend Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) Opening Leaf (12/28/12 · 2:56 AM): "The Coffee Pot Is Up / Neruda and I"
      2) Closing Leaf (Oct 29, 2013): "Dressed in the Night / Lightning Bugs & Rose Garden"
  - Fast keyframe-decoded 1280x720 18x silent Kloster A_tau(p_t) telemetry reel (~59s, <10 MB)
  - ~178-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC25 = Path("/tmp/zoe_s25/s25_5g4.mp4")


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


def build_specimen25() -> dict:
    print("\n================ BUILDING SPECIMEN #25 ('NERUDA AND I' · DEC 2012 – OCT 2013 JOURNAL) ================")
    root = DOCS / "specimen25"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K literary plates
        im01 = _extract_exact_4k(SRC25, 16.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_never_return_to_past_dec24_2012.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC25, 52.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_coffee_pot_neruda_dec28_2012.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC25, 229.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_we_all_hum_melancholy_jan5_2013.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC25, 484.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_tiny_neon_cafe_feb11_2013.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC25, 516.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_run_forever_feb12_2013.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC25, 1011.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_dressed_in_the_night_oct29_2013.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:16 · 12/24/12: 'Kansas Rain'", p01),
            ("00:52 · 12/28/12: 'Coffee Pot & Neruda'", p02),
            ("03:49 · 1/5/13: 'We All Hum Melancholy'", p03),
            ("08:04 · 2/11/13: 'Tiny Neon Lit Cafe'", p04),
            ("08:36 · 2/12/13: 'Run Forever'", p05),
            ("16:51 · Oct 29: 'Lightning Bugs'", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen25.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Bookend Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        pad = 24
        # SVG #1 (Opening of the Year): "The Coffee Pot Is Up / Neruda and I" (12/28/12 · 2:56 AM)
        w2, h2 = im02.size
        arr2 = np.asarray(im02, dtype=np.uint8)
        p2_col = tuple(int(v) for v in np.median(arr2[int(h2 * 0.25):int(h2 * 0.38), int(w2 * 0.78):int(w2 * 0.94)].reshape(-1, 3), axis=0))
        poly2 = [
            (int(w2 * 0.345), int(h2 * 0.155)),
            (int(w2 * 0.985), int(h2 * 0.220)),
            (int(w2 * 0.975), int(h2 * 0.800)),
            (int(w2 * 0.195), int(h2 * 0.706)),
            (int(w2 * 0.225), int(h2 * 0.540)),
            (int(w2 * 0.315), int(h2 * 0.435)),
        ]
        m2 = Image.new("L", (w2, h2), 0)
        ImageDraw.Draw(m2).polygon(poly2, fill=255)
        c2 = Image.new("RGB", (w2, h2), p2_col)
        c2.paste(im02, (0, 0), m2)
        rot2 = c2.rotate(12.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p2_col)
        m2_rot = m2.rotate(12.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m2_rot.getbbox()
        rw2, rh2 = rot2.size
        coffee_src = tmp_p / "coffee_neruda_clean.png"
        rot2.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw2, bx1 + pad), min(rh2, by1 + pad))).save(coffee_src)

        build_svg_and_braille(
            coffee_src,
            assets_dir,
            "coffee_pot_neruda_dec28_2012",
            title='"THE COFFEE POT IS UP / NERUDA AND I" (12/28/12 · 2:56 AM)',
            subtitle="Signed Holograph Opening Leaf · 2012–2013 Year-Long Journal (Specimen #25)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.17, 0.37, 1.2),
            braille_cols=72,
        )

        # SVG #2 (Closing of the Year): "Dressed in the Night / Lightning Bugs & Rose Garden" (Oct 29, 2013)
        w6, h6 = im06.size
        arr6 = np.asarray(im06, dtype=np.uint8)
        p6_col = tuple(int(v) for v in np.median(arr6[int(h6 * 0.14):int(h6 * 0.22), int(w6 * 0.75):int(w6 * 0.92)].reshape(-1, 3), axis=0))
        poly6 = [
            (int(w6 * 0.105), int(h6 * 0.135)),
            (int(w6 * 0.975), int(h6 * 0.175)),
            (int(w6 * 0.955), int(h6 * 0.968)),
            (int(w6 * 0.310), int(h6 * 0.945)),
            (int(w6 * 0.135), int(h6 * 0.825)),
            (int(w6 * 0.122), int(h6 * 0.640)),
            (int(w6 * 0.088), int(h6 * 0.560)),
        ]
        m6 = Image.new("L", (w6, h6), 0)
        ImageDraw.Draw(m6).polygon(poly6, fill=255)
        c6 = Image.new("RGB", (w6, h6), p6_col)
        c6.paste(im06, (0, 0), m6)
        rot6 = c6.rotate(4.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p6_col)
        m6_rot = m6.rotate(4.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m6_rot.getbbox()
        rw6, rh6 = rot6.size
        night_src = tmp_p / "dressed_in_night_clean.png"
        rot6.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw6, bx1 + pad), min(rh6, by1 + pad))).save(night_src)

        build_svg_and_braille(
            night_src,
            assets_dir,
            "dressed_in_the_night_oct29_2013",
            title='"DRESSED IN THE NIGHT / LIGHTNING BUGS" (OCT 29 · NICHOLAS KLOSTER)',
            subtitle="Signed Holograph Closing Leaf · 2012–2013 Year-Long Journal (Specimen #25)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.17, 0.37, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 18x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~59s)
        fps = 15
        target_frames = 885  # 59.0s out for 1064.48s real (~18.04x)
        vw, vh = 406, 720
        real_dur = 1064.48
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 17m 44s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC25),
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

        tl_mp4 = tmp_p / "year_poems_tl.mp4"
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
            raise RuntimeError("Specimen #25 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 120:
                return "DEC 2012 · NERUDA", (94, 218, 238)
            if rsec < 275:
                return "JAN 2013 · MELANCHOLY", (242, 196, 92)
            if rsec < 495:
                return "FEB 2013 · JAZZ CAFE", (244, 106, 126)
            if rsec < 610:
                return "FEB 12 · RUN FOREVER", (195, 162, 255)
            if rsec < 860:
                return "JUL 2013 · VINYL INK", (168, 226, 142)
            return "OCT 29 · ROSE GARDEN", (242, 196, 92)

        out_mp4 = video_dir / "specimen25_year_in_poems_overlay.mp4"
        poster_png = video_dir / "specimen25_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #25 · "NERUDA AND I" (DEC 2012 – OCT 2013)',
            header_sub="Complete 17m 44s Year-Long Journal · Coffee Pot, Jazz & Rose Garden (18x Reel)",
            phase_fn=phase_fn,
            nexus_band=(475.0, 535.0, 'NEXUS · "JAZZ CAFE & RUN FOREVER"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=52.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~178 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 516.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen25_year_in_poems",
        title='SPECIMEN #25 · "NERUDA AND I" (DEC 2012 – OCT 2013 JOURNAL)',
        subtitle='17m 44s Year-Long Manuscript · Coffee Pot (12/28/12), Jazz Cafe & Oct 29 Rose Garden',
        nexus_label='"RUN FOREVER" (8:36)',
        footer_label='Fieldglass Specimen #25 · "Neruda and I" (2012–2013) Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp25",
    )

    summary = {
        "specimen25": {
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
    build_specimen25()
