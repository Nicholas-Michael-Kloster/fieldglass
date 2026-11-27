#!/usr/bin/env python3
"""Build Fieldglass Specimen #29 — "A Deal With Bach & My Birds" (Signed Blind-Typed Anthology).

Source:
  - /tmp/zoe_s29/s29.mp4 (zoe_vid_1795745169189.mp4)
    (2026-11-26 20:19, anthology span [0:00–12:38 / 758.0s], 4K portrait 2160x3840 @ 30fps)

Cover-to-cover capture of Nicholas Kloster's hand-signed typewritten first-draft poetry
anthology — composed with the monitor switched off in uninterrupted single-take flow
states ("All first time goes, no edits"). Highlights "A poem a forest a woman / full of
music like a city on fire", the Savio & Greevo dialogue ("A Deal with death, about a
play. With Bach in background." — echoing "Sovio · 6-25-1840" from Specimen #23), the
Tom Waits homage "It is raining some where / the piano plays backwards", "an afair with
rain" ("walked through the rain, like a bookstore"), "to a boy with alligator skin"
(Dinah Washington & Ella Fitzgerald), and "my birds" ("Dance with me... Silence is
perfect."). Rendered as a silent telemetry reel to preserve household privacy.

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "A Deal With Bach" (Savio & Greevo · Signed Nicholas Kloster)
      2) "My Birds / Silence Is Perfect" (Blind-Typed Broadside)
  - Fast keyframe-decoded 1280x720 15x silent Kloster A_tau(p_t) telemetry reel (~52s, <9 MB)
  - ~126-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    build_svg_and_braille,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC29 = Path("/tmp/zoe_s29/s29.mp4")


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


def build_specimen29() -> dict:
    print("\n================ BUILDING SPECIMEN #29 ('A DEAL WITH BACH & MY BIRDS' · SIGNED ANTHOLOGY) ================")
    root = DOCS / "specimen29"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K plates
        im01 = _extract_exact_4k(SRC29, 91.5, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_forest_woman_city_on_fire.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC29, 121.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_savio_deal_with_bach_signed.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC29, 140.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_raining_somewhere_piano_backwards.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC29, 405.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_an_affair_with_rain_signed.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC29, 588.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_boy_with_alligator_skin.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC29, 749.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_my_birds_silence_is_perfect.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("01:31 · 'City on Fire' (Signed)", p01),
            ("02:01 · 'Savio & Bach' (Signed)", p02),
            ("02:20 · 'Piano Plays Backwards'", p03),
            ("06:45 · 'an afair with rain' (Signed)", p04),
            ("09:48 · 'to a boy with alligator skin'", p05),
            ("12:29 · 'my birds / Silence Is Perfect'", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen29.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        pad = 24

        # SVG #1: "A Deal With Bach" (Savio & Greevo · Signed Nicholas Kloster, 121.0s)
        w2, h2 = im02.size
        arr2 = np.asarray(im02, dtype=np.uint8)
        p2_col = tuple(int(v) for v in np.median(arr2[int(h2 * 0.42):int(h2 * 0.54), int(w2 * 0.65):int(w2 * 0.88)].reshape(-1, 3), axis=0))
        poly2 = [
            (int(w2 * 0.215), int(h2 * 0.148)),
            (int(w2 * 0.968), int(h2 * 0.130)),
            (int(w2 * 0.920), int(h2 * 0.872)),
            (int(w2 * 0.310), int(h2 * 0.865)),
            (int(w2 * 0.310), int(h2 * 0.618)),
            (int(w2 * 0.155), int(h2 * 0.612)),
        ]
        m2 = Image.new("L", (w2, h2), 0)
        ImageDraw.Draw(m2).polygon(poly2, fill=255)
        c2 = Image.new("RGB", (w2, h2), p2_col)
        c2.paste(im02, (0, 0), m2.filter(ImageFilter.GaussianBlur(radius=32)))
        rot2 = c2.rotate(0.8, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p2_col)
        m2_rot = m2.rotate(0.8, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m2_rot.getbbox()
        rw2, rh2 = rot2.size
        bach_src = tmp_p / "savio_bach_clean.png"
        rot2.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw2, bx1 + pad), min(rh2, by1 + pad))).save(bach_src)

        build_svg_and_braille(
            bach_src,
            assets_dir,
            "savio_deal_with_bach",
            title='"A DEAL WITH DEATH, ABOUT A PLAY. WITH BACH IN BACKGROUND."',
            subtitle="Savio & Greevo · Signed First-Draft Typewritten Broadside (Specimen #29)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=24.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.18,
            levels=(0.15, 0.35, 1.2),
            braille_cols=72,
        )

        # SVG #2: "my birds / Dance With Me · Silence Is Perfect" (749.0s)
        w6, h6 = im06.size
        arr6 = np.asarray(im06, dtype=np.uint8)
        p6_col = tuple(int(v) for v in np.median(arr6[int(h6 * 0.55):int(h6 * 0.72), int(w6 * 0.65):int(w6 * 0.85)].reshape(-1, 3), axis=0))
        poly6 = [
            (int(w6 * 0.095), int(h6 * 0.068)),
            (int(w6 * 0.850), int(h6 * 0.080)),
            (int(w6 * 0.830), int(h6 * 0.875)),
            (int(w6 * 0.020), int(h6 * 0.845)),
        ]
        m6 = Image.new("L", (w6, h6), 0)
        ImageDraw.Draw(m6).polygon(poly6, fill=255)
        c6 = Image.new("RGB", (w6, h6), p6_col)
        c6.paste(im06, (0, 0), m6)
        rot6 = c6.rotate(2.2, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p6_col)
        m6_rot = m6.rotate(2.2, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m6_rot.getbbox()
        rw6, rh6 = rot6.size
        birds_src = tmp_p / "my_birds_clean.png"
        rot6.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw6, bx1 + pad), min(rh6, by1 + pad))).save(birds_src)

        build_svg_and_braille(
            birds_src,
            assets_dir,
            "my_birds_silence_is_perfect",
            title='"MY BIRDS — DANCE WITH ME · SILENCE IS PERFECT."',
            subtitle="Blind-Typed First-Draft Broadside · Nicholas Kloster Anthology (Specimen #29)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=26.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.18,
            levels=(0.15, 0.35, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 15x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~52s)
        #    Scoped cleanly to [0:00–12:38 / 758.0s] anthology sweep.
        fps = 15
        target_frames = 780  # 52.0s out for 758.0s real (~14.58x)
        vw, vh = 406, 720
        real_dur = 758.0
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 12m 38s anthology -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC29), "-t", f"{real_dur:.2f}",
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

        tl_mp4 = tmp_p / "anthology_tl.mp4"
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
            raise RuntimeError("Specimen #29 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 105:
                return "CITY ON FIRE · SIGNED", (94, 218, 238)
            if rsec < 165:
                return "SAVIO · BACH & WAITS", (244, 106, 126)
            if rsec < 370:
                return "A LETTER · KANSAS", (242, 196, 92)
            if rsec < 480:
                return "AFFAIR WITH RAIN", (195, 162, 255)
            if rsec < 660:
                return "ALLIGATOR SKIN", (168, 226, 142)
            return "MY BIRDS · SILENCE", (242, 196, 92)

        out_mp4 = video_dir / "specimen29_deal_with_bach_overlay.mp4"
        poster_png = video_dir / "specimen29_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #29 · "A DEAL WITH BACH & MY BIRDS" (SIGNED ANTHOLOGY)',
            header_sub="Blind-Typed First-Draft Folios · Savio, Tom Waits, Rain & Silence (15x Silent)",
            phase_fn=phase_fn,
            nexus_band=(108.0, 145.0, 'NEXUS · "SAVIO & BACH"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=121.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~126 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 121.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen29_deal_with_bach",
        title='SPECIMEN #29 · "A DEAL WITH BACH & MY BIRDS" (SIGNED ANTHOLOGY)',
        subtitle='12m 38s Blind-Typed First-Draft Folios · Savio, Bach, Rain & "Silence Is Perfect"',
        nexus_label='"SAVIO & BACH" (2:01)',
        footer_label='Fieldglass Specimen #29 · "A Deal With Bach & My Birds" Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp29",
    )

    summary = {
        "specimen29": {
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
    build_specimen29()
