#!/usr/bin/env python3
"""Build Fieldglass Specimen #28 — "Blue Poems & Dear Saba" (Dec 27 – Feb 4 Unlined White Poetry Folio).

Source:
  - /tmp/zoe_s28/s28.mp4 (zoe_vid_1795743869292.mp4)
    (2026-11-26 19:53, poetry folio span [0:00–07:05 / 425.0s], 4K portrait 2160x3840)

Cover-to-cover capture of Nicholas Kloster's unlined white poetry notebook opening with
the cognitive epigraph "This Is the Subconscious" ("Underneath the layers of critical
thought, functions of the conscious mind lay a powerful awareness... a storehouse of
one's knowledge"), moving through vivid royal-blue ink December 27 leaves ("Night
Building City / Blue Poems", "Self-Proclaimed Pilgrimage / Where Beauty Hides and
Kisses Wire", and "Dear Saba" — invoking Italian poet Umberto Saba, Futurism, and
Surrealism), transitioning into black-ink leaves ("Like Some French Film / Record
Player Made of Glass and European Wine Corks", signed "The Jazz Moved Into Her Backbone"
Feb 4), and landscape-turned winter leaves. Scoped cleanly to Nick's own poetry pages
(0:00–07:05) prior to back-cover guest notes and desk wrap-up.

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Red-Channel Prussian-Indigo Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "Night Building City / Blue Poems" (9:55 pm · December 27)
      2) "Self-Proclaimed Pilgrimage / Where Beauty Hides and Kisses Wire" (10:58 pm · December 27)
  - Fast keyframe-decoded 1280x720 9x silent Kloster A_tau(p_t) telemetry reel (~47s, <7 MB)
  - ~71-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC28 = Path("/tmp/zoe_s28/s28.mp4")


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


def _red_channel_rgb(im: Image.Image) -> Image.Image:
    """Use Red channel for maximum optical contrast on royal-blue ink."""
    r = im.split()[0]
    return Image.merge("RGB", (r, r, r))


def build_specimen28() -> dict:
    print("\n================ BUILDING SPECIMEN #28 ('BLUE POEMS & DEAR SABA' · DEC 27 – FEB 4) ================")
    root = DOCS / "specimen28"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K plates
        im01 = _extract_exact_4k(SRC28, 7.5, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_this_is_the_subconscious.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC28, 79.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_night_building_city_blue_poems.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC28, 116.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_self_proclaimed_pilgrimage.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC28, 151.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_dear_saba_futurist_surrealism.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC28, 191.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_like_some_french_film_vinyl.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC28, 209.5, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_jazz_in_her_backbone_feb4_signed.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:08 · 'This Is the Subconscious'", p01),
            ("01:19 · 'Night Building City / Blue Poems'", p02),
            ("01:56 · 'Self-Proclaimed Pilgrimage'", p03),
            ("02:31 · 'Dear Saba' (Umberto Saba)", p04),
            ("03:11 · 'Like Some French Film'", p05),
            ("03:30 · 'Jazz in Her Backbone' (Feb 4)", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen28.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Red-Channel Prussian-Indigo Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        pad = 24
        indigo_colors = ("#4c6d9c", "#14294f")

        # SVG #1: "Night Building City / Blue Poems" (9:55 pm · December 27 · 79.0s, zero fingers!)
        im02_r = _red_channel_rgb(im02)
        w2, h2 = im02_r.size
        arr2 = np.asarray(im02_r, dtype=np.uint8)
        p2_col = tuple(int(v) for v in np.median(arr2[int(h2 * 0.68):int(h2 * 0.80), int(w2 * 0.55):int(w2 * 0.85)].reshape(-1, 3), axis=0))
        poly2 = [
            (int(w2 * 0.055), int(h2 * 0.108)),
            (int(w2 * 0.985), int(h2 * 0.108)),
            (int(w2 * 0.985), int(h2 * 0.840)),
            (int(w2 * 0.045), int(h2 * 0.840)),
        ]
        m2 = Image.new("L", (w2, h2), 0)
        ImageDraw.Draw(m2).polygon(poly2, fill=255)
        c2 = Image.new("RGB", (w2, h2), p2_col)
        c2.paste(im02_r, (0, 0), m2)
        bx0, by0, bx1, by1 = m2.getbbox()
        blue_src = tmp_p / "blue_poems_clean.png"
        c2.crop((max(0, bx0 - pad), max(0, by0 - pad), min(w2, bx1 + pad), min(h2, by1 + pad))).save(blue_src)

        build_svg_and_braille(
            blue_src,
            assets_dir,
            "night_building_city_blue_poems",
            title='"NIGHT BUILDING CITY / BLUE POEMS" (9:55 PM · DEC 27)',
            subtitle="Red-Channel Prussian-Indigo Holograph · Unlined White Folio (Specimen #28)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.18,
            levels=(0.15, 0.34, 1.2),
            colors=indigo_colors,
            braille_cols=72,
        )

        # SVG #2: "Self-Proclaimed Pilgrimage / Where Beauty Hides and Kisses Wire" (10:58 pm · Dec 27 · 116.0s)
        im03_r = _red_channel_rgb(im03)
        w3, h3 = im03_r.size
        arr3 = np.asarray(im03_r, dtype=np.uint8)
        p3_col = tuple(int(v) for v in np.median(arr3[int(h3 * 0.65):int(h3 * 0.78), int(w3 * 0.68):int(w3 * 0.88)].reshape(-1, 3), axis=0))
        poly3 = [
            (int(w3 * 0.265), int(h3 * 0.040)),
            (int(w3 * 0.910), int(h3 * 0.048)),
            (int(w3 * 0.910), int(h3 * 0.765)),
            (int(w3 * 0.130), int(h3 * 0.755)),
            (int(w3 * 0.145), int(h3 * 0.525)),
            (int(w3 * 0.265), int(h3 * 0.495)),
        ]
        m3 = Image.new("L", (w3, h3), 0)
        ImageDraw.Draw(m3).polygon(poly3, fill=255)
        c3 = Image.new("RGB", (w3, h3), p3_col)
        c3.paste(im03_r, (0, 0), m3)
        rot3 = c3.rotate(3.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p3_col)
        m3_rot = m3.rotate(3.5, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m3_rot.getbbox()
        rw3, rh3 = rot3.size
        pilg_src = tmp_p / "self_proclaimed_pilgrimage_clean.png"
        rot3.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw3, bx1 + pad), min(rh3, by1 + pad))).save(pilg_src)

        build_svg_and_braille(
            pilg_src,
            assets_dir,
            "self_proclaimed_pilgrimage",
            title='"SELF-PROCLAIMED PILGRIMAGE / WHERE BEAUTY HIDES" (10:58 PM)',
            subtitle="Red-Channel Prussian-Indigo Holograph · Dec 27 Folio (Specimen #28)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.18,
            levels=(0.15, 0.34, 1.2),
            colors=indigo_colors,
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 9x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~47s)
        #    Scoped cleanly to [0:00–07:05 / 425.0s] Nick's poetry pages.
        fps = 15
        target_frames = 705  # 47.0s out for 425.0s real (~9.04x)
        vw, vh = 406, 720
        real_dur = 425.0
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 7m 05s poetry folio -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC28), "-t", f"{real_dur:.2f}",
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

        tl_mp4 = tmp_p / "blue_poems_tl.mp4"
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
            raise RuntimeError("Specimen #28 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 65:
                return "SUBCONSCIOUS · DEC 26", (94, 218, 238)
            if rsec < 108:
                return "BLUE POEMS · DEC 27", (195, 162, 255)
            if rsec < 138:
                return "PILGRIMAGE · BEAUTY", (244, 106, 126)
            if rsec < 180:
                return "DEAR SABA · ITALY", (242, 196, 92)
            if rsec < 235:
                return "FRENCH FILM · FEB 4", (168, 226, 142)
            return "WINTER · SIDEWAYS", (94, 218, 238)

        out_mp4 = video_dir / "specimen28_blue_poems_saba_overlay.mp4"
        poster_png = video_dir / "specimen28_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #28 · "BLUE POEMS & DEAR SABA" (DEC 27 – FEB 4)',
            header_sub="Unlined White Folio · Subconscious Epigraph, Royal-Blue Ink & Umberto Saba (9x)",
            phase_fn=phase_fn,
            nexus_band=(108.0, 132.0, 'NEXUS · "PILGRIMAGE" (DEC 27)'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=116.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~71 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 116.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen28_blue_poems_saba",
        title='SPECIMEN #28 · "BLUE POEMS & DEAR SABA" (DEC 27 – FEB 4)',
        subtitle='7m 05s Unlined White Folio · "Subconscious", "Blue Poems", "Pilgrimage" & "Dear Saba"',
        nexus_label='"PILGRIMAGE" (1:56)',
        footer_label='Fieldglass Specimen #28 · "Blue Poems & Dear Saba" Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp28",
    )

    summary = {
        "specimen28": {
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
    build_specimen28()
