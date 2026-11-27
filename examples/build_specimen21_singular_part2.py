#!/usr/bin/env python3
"""Build Fieldglass Specimen #21 — "Everything Is Singular" Part II (Aug–Nov 2013 & Blue vs. Black Ink).

Source:
  - /tmp/zoe_s21/s21_2g3.mp4 (zoe_vid_1795738895173.mp4)
    (2026-11-26 18:29, 7m 42s [462.23s], 4K portrait 2160x3840 @ 30fps)

Back half of Nicholas Kloster's yellow-cover 2013 notebook "Everything Is Singular"
(August–November 1, 2013), filmed in the studio to Erik Satie's Gnossiennes alongside
Dr. Helen Ruth Horkan and Thumbs ("Thumbelina") the calico cat. Captures Nick & Dr.
Helen's blue-ink ("like water, like carving into it") vs. black-ink ("like stamped")
debate, Nick's joke about compressing whole poems into numerical symbols, "I Am an Atom,
You Are the Molecule" (signed blue-ink leaf), "Typewriter Still Broken ($70)" (9/17/13),
"Not Shakespeare's, But Tom Waits" (9/17/13 · 12:00 pm probably), "I Write by a Stricken
Match" (Nov 1 · 10:36 pm), and the original yellow back-cover ink drawing by DJ Holt.

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 contrasting Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) Prussian-Indigo Red-Channel SVG: "I Am an Atom, You Are the Molecule" (Blue Ink · Signed)
      2) Archival Sepia Black-Ink SVG: "Not Shakespeare's, But Tom Waits" (9/17/13)
  - Fast keyframe-decoded 1280x720 10x silent Kloster A_tau(p_t) telemetry reel (~46s, <8 MB)
  - ~78-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC21 = Path("/tmp/zoe_s21/s21_2g3.mp4")


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


def build_specimen21() -> dict:
    print("\n================ BUILDING SPECIMEN #21 ('EVERYTHING IS SINGULAR' PART II · AUG–NOV 2013) ================")
    root = DOCS / "specimen21"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K hero plates
        im01 = _extract_exact_4k(SRC21, 8.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_atom_and_molecule_blue_ink.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC21, 100.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_dr_helen_studio_dialogue.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC21, 226.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_typewriter_still_broken_sep17.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC21, 255.5, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_not_shakespeares_but_tom_waits.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC21, 345.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_thumbs_cat_and_open_folio.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC21, 450.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_dj_holt_yellow_back_cover.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:08 · Blue Ink: 'Atom & Molecule'", p01),
            ("01:40 · Dr. Helen Studio Dialogue", p02),
            ("03:46 · 9/17/13: 'Typewriter Broken'", p03),
            ("04:15 · 9/17/13: 'Tom Waits'", p04),
            ("05:45 · Thumbs (Thumbelina) & Folio", p05),
            ("07:30 · Back Cover Art by DJ Holt", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen21.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Contrasting Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        # SVG #1 (Prussian Indigo · Red-Channel Blue-Pen Isolation):
        #   "I Am an Atom, You Are the Molecule" (Signed Nicholas Kloster · Blue Pen)
        w1, h1 = im01.size
        r1 = im01.getchannel("R")
        im01_red = Image.merge("RGB", (r1, r1, r1))
        arr1 = np.asarray(im01_red, dtype=np.uint8)
        p1_col = tuple(int(v) for v in np.median(arr1[int(h1 * 0.32):int(h1 * 0.48), int(w1 * 0.72):int(w1 * 0.90)].reshape(-1, 3), axis=0))
        poly1 = [
            (int(w1 * 0.400), int(h1 * 0.240)),
            (int(w1 * 0.950), int(h1 * 0.335)),
            (int(w1 * 0.870), int(h1 * 0.700)),
            (int(w1 * 0.780), int(h1 * 0.911)),
            (int(w1 * 0.282), int(h1 * 0.796)),
        ]
        m1 = Image.new("L", (w1, h1), 0)
        ImageDraw.Draw(m1).polygon(poly1, fill=255)
        c1 = Image.new("RGB", (w1, h1), p1_col)
        c1.paste(im01_red, (0, 0), m1)
        rot1 = c1.rotate(21.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p1_col)
        m1_rot = m1.rotate(21.5, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m1_rot.getbbox()
        pad = 24
        rw1, rh1 = rot1.size
        atom_src = tmp_p / "atom_red_clean.png"
        rot1.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw1, bx1 + pad), min(rh1, by1 + pad))).save(atom_src)

        build_svg_and_braille(
            atom_src,
            assets_dir,
            "atom_and_molecule_blue_ink",
            title='"I AM AN ATOM, YOU ARE THE MOLECULE" — NICHOLAS KLOSTER',
            subtitle='Red-Channel Blue-Ink Holograph · "Everything Is Singular" Part II (Specimen #21)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=34.0,
            paper_cutoff=0.90,
            ink_floor=0.40,
            gamma=1.22,
            levels=(0.17, 0.36, 1.2),
            colors=("#48709e", "#10284c"),
            braille_cols=72,
        )

        # SVG #2 (Archival Sepia · Black-Ink Broadside):
        #   "Not Shakespeare's, But Tom Waits" (9/17/13 · 12:00 pm probably)
        w4, h4 = im04.size
        arr4 = np.asarray(im04, dtype=np.uint8)
        p4_col = tuple(int(v) for v in np.median(arr4[int(h4 * 0.20):int(h4 * 0.32), int(w4 * 0.72):int(w4 * 0.90)].reshape(-1, 3), axis=0))
        poly4 = [
            (int(w4 * 0.085), int(h4 * 0.135)),
            (int(w4 * 0.955), int(h4 * 0.185)),
            (int(w4 * 0.845), int(h4 * 0.905)),
            (int(w4 * 0.310), int(h4 * 0.865)),
            (int(w4 * 0.075), int(h4 * 0.735)),
        ]
        m4 = Image.new("L", (w4, h4), 0)
        ImageDraw.Draw(m4).polygon(poly4, fill=255)
        c4 = Image.new("RGB", (w4, h4), p4_col)
        c4.paste(im04, (0, 0), m4)
        rot4 = c4.rotate(6.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p4_col)
        rw4, rh4 = rot4.size
        waits_src = tmp_p / "tom_waits_clean.png"
        rot4.crop((int(rw4 * 0.095), int(rh4 * 0.155), int(rw4 * 0.885), int(rh4 * 0.865))).save(waits_src)

        build_svg_and_braille(
            waits_src,
            assets_dir,
            "not_shakespeares_but_tom_waits_sep17",
            title='"NOT SHAKESPEARE\'S, BUT TOM WAITS" (9/17/13 · 12:00 PM)',
            subtitle='Black-Ink Holograph Leaf · "Everything Is Singular" Part II (Specimen #21)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=36.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.18, 0.38, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 10x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~46s)
        fps = 15
        target_frames = 690  # 46.0s out for 462.23s real (~10.05x)
        vw, vh = 406, 720
        real_dur = 462.23
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 7m 42s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC21),
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

        tl_mp4 = tmp_p / "singular2_tl.mp4"
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
            raise RuntimeError("Specimen #21 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 85:
                return "BLUE INK · ATOM", (94, 218, 238)
            if rsec < 165:
                return "STUDIO · DR. HELEN", (244, 106, 126)
            if rsec < 240:
                return "SEP 17 · TYPEWRITER", (242, 196, 92)
            if rsec < 305:
                return "SEP 17 · TOM WAITS", (195, 162, 255)
            if rsec < 395:
                return "THUMBS THE CAT & INK", (168, 226, 142)
            return "NOV 1 & DJ HOLT ART", (242, 196, 92)

        out_mp4 = video_dir / "specimen21_singular_part2_overlay.mp4"
        poster_png = video_dir / "specimen21_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #21 · "EVERYTHING IS SINGULAR" PT. II (AUG–NOV 2013)',
            header_sub="Blue vs. Black Ink, Dr. Helen, Thumbs the Cat & DJ Holt Cover (10x Reel)",
            phase_fn=phase_fn,
            nexus_band=(245.0, 272.0, 'NEXUS · "TOM WAITS" & THUMBS'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=255.5,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~78 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 255.5)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen21_singular_part2",
        title='SPECIMEN #21 · "EVERYTHING IS SINGULAR" PT. II (AUG–NOV 2013)',
        subtitle='7m 42s Folio · Blue vs. Black Ink, Tom Waits, Thumbs the Cat & DJ Holt Cover',
        nexus_label='"TOM WAITS" LEAF (4:15)',
        footer_label='Fieldglass Specimen #21 · "Everything Is Singular" Part II (2013) Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp21",
    )

    summary = {
        "specimen21": {
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
    build_specimen21()
