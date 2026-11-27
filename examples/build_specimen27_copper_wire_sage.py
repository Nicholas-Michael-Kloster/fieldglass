#!/usr/bin/env python3
"""Build Fieldglass Specimen #27 — "Copper Wire & The Sage" (Sept 2 – Oct 3 Unlined Cream Pocket Notebook).

Source:
  - /tmp/zoe_s27/s27.mp4 (zoe_vid_1795743364658.mp4)
    (2026-11-26 19:41, 6m 55s / 415.11s, 4K portrait 2160x3840 @ 30fps)

Cover-to-cover capture of Nicholas Kloster's unlined cream pocket poetry notebook
(Sept 2 – Oct 3), featuring the paired opening leaves "Copper Wire Boy" (10:19) and
"Copper Wire Girl" (10:28 a.m.), "Johnny Cash" (10:30 a.m. · "-at an abandoned cafe
near Mexico"), "There's a Smooth Sound to the World / An Orchestra of Chaotic Sounds"
(2:17 pm · Sept, 2), "The Dog Is a True Sage" ("Kansas rain, Kansas snow, Earth, and
the yellow, Bilingual Sun", Sept, 13), "Beautiful Girl / Man With Eyes" (Sept 16),
"I Watched the Moon From a Motionless Ship", and the signed closing epigram
"The irony of the forbidden fruit, is that, it's tasteless." (Nicholas Kloster).

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Vector SVGs + 72-Col 2x4 Braille Broadsides (unlined cream paper, crisp black ink):
      1) "The Dog Is a True Sage" (Kansas Rain, Bilingual Sun · Sept, 13)
      2) "An Orchestra of Chaotic Sounds" ("There's a Smooth Sound to the World" · 2:17 pm Sept, 2)
  - Fast keyframe-decoded 1280x720 9x silent Kloster A_tau(p_t) telemetry reel (~46s, <8 MB)
  - ~70-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC27 = Path("/tmp/zoe_s27/s27.mp4")


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


def build_specimen27() -> dict:
    print("\n================ BUILDING SPECIMEN #27 ('COPPER WIRE & THE SAGE' · SEPT 2 – OCT 3) ================")
    root = DOCS / "specimen27"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K plates
        im01 = _extract_exact_4k(SRC27, 159.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_copper_wire_boy_sep2.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC27, 172.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_copper_wire_girl_sep2.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC27, 186.8, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_johnny_cash_abandoned_cafe.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC27, 216.5, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_orchestra_of_chaotic_sounds.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC27, 243.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_the_dog_is_a_true_sage.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC27, 409.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_forbidden_fruit_signed.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("02:39 · 'Copper Wire Boy' (Sept 2)", p01),
            ("02:52 · 'Copper Wire Girl' (Sept 2)", p02),
            ("03:07 · 'Johnny Cash' (Near Mexico)", p03),
            ("03:36 · 'Orchestra of Chaotic Sounds'", p04),
            ("04:03 · 'The Dog Is a True Sage'", p05),
            ("06:49 · 'Forbidden Fruit' (Signed)", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen27.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Vector SVGs + 72-Col 2x4 Braille Broadsides (pristine unlined cream paper!)
        pad = 24

        # SVG #1: "The Dog Is a True Sage" (Kansas Rain, Bilingual Sun · Sept, 13 · 243.0s)
        w5, h5 = im05.size
        arr5 = np.asarray(im05, dtype=np.uint8)
        p5_col = tuple(int(v) for v in np.median(arr5[int(h5 * 0.72):int(h5 * 0.85), int(w5 * 0.65):int(w5 * 0.88)].reshape(-1, 3), axis=0))
        poly5 = [
            (int(w5 * 0.175), int(h5 * 0.118)),
            (int(w5 * 0.960), int(h5 * 0.150)),
            (int(w5 * 0.960), int(h5 * 0.875)),
            (int(w5 * 0.175), int(h5 * 0.855)),
        ]
        m5 = Image.new("L", (w5, h5), 0)
        ImageDraw.Draw(m5).polygon(poly5, fill=255)
        c5 = Image.new("RGB", (w5, h5), p5_col)
        c5.paste(im05, (0, 0), m5)
        rot5 = c5.rotate(4.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p5_col)
        m5_rot = m5.rotate(4.5, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m5_rot.getbbox()
        rw5, rh5 = rot5.size
        dog_src = tmp_p / "dog_sage_clean.png"
        rot5.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw5, bx1 + pad), min(rh5, by1 + pad))).save(dog_src)

        build_svg_and_braille(
            dog_src,
            assets_dir,
            "the_dog_is_a_true_sage",
            title='"THE DOG IS A TRUE SAGE" (KANSAS RAIN · BILINGUAL SUN)',
            subtitle="Unlined Cream Pocket Holograph · Sept 13 (Specimen #27)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.20,
            levels=(0.16, 0.36, 1.2),
            braille_cols=72,
        )

        # SVG #2: "There's a Smooth Sound to the World / An Orchestra of Chaotic Sounds" (2:17 pm · Sept, 2 · 216.5s)
        w4, h4 = im04.size
        arr4 = np.asarray(im04, dtype=np.uint8)
        p4_col = tuple(int(v) for v in np.median(arr4[int(h4 * 0.72):int(h4 * 0.84), int(w4 * 0.45):int(w4 * 0.65)].reshape(-1, 3), axis=0))
        poly4 = [
            (int(w4 * 0.195), int(h4 * 0.118)),
            (int(w4 * 0.960), int(h4 * 0.150)),
            (int(w4 * 0.960), int(h4 * 0.925)),
            (int(w4 * 0.340), int(h4 * 0.905)),
            (int(w4 * 0.125), int(h4 * 0.715)),
        ]
        m4 = Image.new("L", (w4, h4), 0)
        ImageDraw.Draw(m4).polygon(poly4, fill=255)
        c4 = Image.new("RGB", (w4, h4), p4_col)
        c4.paste(im04, (0, 0), m4)
        rot4 = c4.rotate(5.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p4_col)
        m4_rot = m4.rotate(5.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m4_rot.getbbox()
        rw4, rh4 = rot4.size
        sound_src = tmp_p / "orchestra_chaotic_sounds_clean.png"
        rot4.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw4, bx1 + pad), min(rh4, by1 + pad))).save(sound_src)

        build_svg_and_braille(
            sound_src,
            assets_dir,
            "orchestra_of_chaotic_sounds",
            title='"AN ORCHESTRA OF CHAOTIC SOUNDS" (2:17 PM · SEPT 2)',
            subtitle="Unlined Cream Pocket Holograph · Smooth Sound to the World (Specimen #27)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.20,
            levels=(0.16, 0.36, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 9x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~46s)
        fps = 15
        target_frames = 690  # 46.0s out for 415.11s real (~9.02x)
        vw, vh = 406, 720
        real_dur = 415.11
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 6m 55s capture -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC27),
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

        tl_mp4 = tmp_p / "copper_wire_tl.mp4"
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
            raise RuntimeError("Specimen #27 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 145:
                return "SEPT 2 · OPENING", (94, 218, 238)
            if rsec < 182:
                return "COPPER WIRE DUET", (242, 196, 92)
            if rsec < 208:
                return "JOHNNY CASH · CAFE", (244, 106, 126)
            if rsec < 236:
                return "SMOOTH SOUND", (168, 226, 142)
            if rsec < 295:
                return "THE DOG · TRUE SAGE", (242, 196, 92)
            if rsec < 385:
                return "SEPT 16 · SHIP & KEYS", (195, 162, 255)
            return "FORBIDDEN FRUIT", (244, 106, 126)

        out_mp4 = video_dir / "specimen27_copper_wire_sage_overlay.mp4"
        poster_png = video_dir / "specimen27_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #27 · "COPPER WIRE & THE SAGE" (SEPT 2 – OCT 3)',
            header_sub="Unlined Cream Pocket Notebook · Johnny Cash, Chaotic Sounds & Bilingual Sun (9x)",
            phase_fn=phase_fn,
            nexus_band=(236.0, 260.0, 'NEXUS · "THE DOG IS A TRUE SAGE"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=243.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~70 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 243.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen27_copper_wire_sage",
        title='SPECIMEN #27 · "COPPER WIRE & THE SAGE" (SEPT 2 – OCT 3)',
        subtitle='6m 55s Unlined Cream Pocket Folio · "Copper Wire", "Johnny Cash" & "The Dog Is a True Sage"',
        nexus_label='"THE DOG IS A TRUE SAGE" (4:03)',
        footer_label='Fieldglass Specimen #27 · "Copper Wire & The Sage" Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp27",
    )

    summary = {
        "specimen27": {
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
    build_specimen27()
