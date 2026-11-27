#!/usr/bin/env python3
"""Build Fieldglass Specimen #24 — "NICHOLAS KLOSTER" Loose-Leaf Manuscript ("Destiny", "Find Your Muse" & "Satie").

Source:
  - /tmp/zoe_s24/s24_1g2.mp4 (zoe_vid_1795740367625.mp4)
    (2026-11-26 18:50, 4m 05s [245.12s], 4K portrait 2160x3840 @ 30fps)

Loose-leaf unlined white poetry manuscript fronted by a minimalist typewritten title sheet
("NICHOLAS KLOSTER"), filmed alongside Thumbs ("Thumbelina") the calico cat inspecting
the live Antigravity Fieldglass terminal while Erik Satie plays in the studio. Uniquely
includes an archival poem mentioning "Chopin plays, / Chopin plays, / Satie" — filmed live
to our Erik Satie studio soundtrack — alongside "I Remember My Father Being Big / And I
Forgive Him", "Find Your Muse / Like the Roses in November", and "Destiny Is Like a Woman".

Generates:
  - 6 crisp GPS-scrubbed upright-rotated 4K plates + 3x2 contact sheet
  - 2 Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "Destiny Is Like a Woman" (Signed Nicholas Kloster · Unlined White Leaf)
      2) "Find Your Muse / Like the Roses in November" (Signed Nicholas Kloster)
  - Fast keyframe-decoded 1280x720 6x silent Kloster A_tau(p_t) telemetry reel (~41s, <7 MB)
  - ~62-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC24 = Path("/tmp/zoe_s24/s24_1g2.mp4")


def _extract_exact_4k(src: Path, t_sec: float, out_path: Path, rotate_ccw: int = 0) -> Image.Image:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{t_sec:.2f}", "-i", str(src),
            "-frames:v", "1", "-q:v", "2", "-map_metadata", "-1",
            str(out_path),
        ],
        check=True,
    )
    im = Image.open(out_path).convert("RGB")
    if rotate_ccw == 90:
        im = im.transpose(Image.Transpose.ROTATE_90)
    elif rotate_ccw == 180:
        im = im.transpose(Image.Transpose.ROTATE_180)
    elif rotate_ccw == 270:
        im = im.transpose(Image.Transpose.ROTATE_270)
    return im


def build_specimen24() -> dict:
    print("\n================ BUILDING SPECIMEN #24 ('NICHOLAS KLOSTER' LOOSE-LEAF FOLIO) ================")
    root = DOCS / "specimen24"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright-rotated 4K hero plates
        im01 = _extract_exact_4k(SRC24, 20.0, tmp_p / "raw_01.jpg", rotate_ccw=0)
        p01 = plates_dir / "01_nicholas_kloster_title_sheet.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC24, 102.0, tmp_p / "raw_02.jpg", rotate_ccw=90)
        p02 = plates_dir / "02_thumbs_cat_at_antigravity_terminal.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC24, 151.0, tmp_p / "raw_03.jpg", rotate_ccw=180)
        p03 = plates_dir / "03_i_remember_my_father_forgive.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC24, 159.0, tmp_p / "raw_04.jpg", rotate_ccw=180)
        p04 = plates_dir / "04_find_your_muse_roses_november.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC24, 175.2, tmp_p / "raw_05.jpg", rotate_ccw=0)
        p05 = plates_dir / "05_destiny_is_like_a_woman.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC24, 216.0, tmp_p / "raw_06.jpg", rotate_ccw=90)
        p06 = plates_dir / "06_chopin_plays_satie_firefly.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:20 · Title: 'NICHOLAS KLOSTER'", p01),
            ("01:42 · Thumbs at Live Terminal", p02),
            ("02:31 · 'Remember My Father' (Upright)", p03),
            ("02:39 · 'Find Your Muse' (Upright)", p04),
            ("02:56 · 'Destiny Is Like a Woman'", p05),
            ("03:36 · 'Chopin Plays, Satie' (Upright)", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen24.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        pad = 24
        # SVG #1: "Destiny Is Like a Woman" (Signed Nicholas Kloster · Unlined Sheet, 175.2s peak focus)
        w5, h5 = im05.size
        arr5 = np.asarray(im05, dtype=np.uint8)
        p5_col = tuple(int(v) for v in np.median(arr5[int(h5 * 0.20):int(h5 * 0.30), int(w5 * 0.68):int(w5 * 0.84)].reshape(-1, 3), axis=0))
        poly5 = [
            (int(w5 * 0.165), int(h5 * 0.180)),
            (int(w5 * 0.865), int(h5 * 0.192)),
            (int(w5 * 0.855), int(h5 * 0.698)),
            (int(w5 * 0.130), int(h5 * 0.692)),
            (int(w5 * 0.175), int(h5 * 0.530)),
            (int(w5 * 0.220), int(h5 * 0.460)),
            (int(w5 * 0.195), int(h5 * 0.340)),
        ]
        m5 = Image.new("L", (w5, h5), 0)
        ImageDraw.Draw(m5).polygon(poly5, fill=255)
        c5 = Image.new("RGB", (w5, h5), p5_col)
        c5.paste(im05, (0, 0), m5)
        rot5 = c5.rotate(1.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p5_col)
        m5_rot = m5.rotate(1.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m5_rot.getbbox()
        rw5, rh5 = rot5.size
        destiny_src = tmp_p / "destiny_clean.png"
        rot5.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw5, bx1 + pad), min(rh5, by1 + pad))).save(destiny_src)

        build_svg_and_braille(
            destiny_src,
            assets_dir,
            "destiny_is_like_a_woman",
            title='"DESTINY IS LIKE A WOMAN" — NICHOLAS KLOSTER',
            subtitle='Signed Unlined Pencil Holograph · "NICHOLAS KLOSTER" Manuscript (Specimen #24)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=24.0,
            paper_cutoff=0.955,
            ink_floor=0.52,
            gamma=1.00,
            levels=(0.065, 0.18, 1.2),
            braille_cols=72,
        )

        # SVG #2: "Find Your Muse / Like the Roses in November" (Signed Nicholas Kloster, 159.0s rot=180)
        w4, h4 = im04.size
        arr4 = np.asarray(im04, dtype=np.uint8)
        p4_col = tuple(int(v) for v in np.median(arr4[int(h4 * 0.32):int(h4 * 0.44), int(w4 * 0.72):int(w4 * 0.86)].reshape(-1, 3), axis=0))
        poly4 = [
            (int(w4 * 0.155), int(h4 * 0.275)),
            (int(w4 * 0.895), int(h4 * 0.285)),
            (int(w4 * 0.880), int(h4 * 0.760)),
            (int(w4 * 0.395), int(h4 * 0.760)),
            (int(w4 * 0.395), int(h4 * 0.822)),
            (int(w4 * 0.135), int(h4 * 0.822)),
        ]
        m4 = Image.new("L", (w4, h4), 0)
        ImageDraw.Draw(m4).polygon(poly4, fill=255)
        c4 = Image.new("RGB", (w4, h4), p4_col)
        c4.paste(im04, (0, 0), m4)
        rot4 = c4.rotate(1.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p4_col)
        m4_rot = m4.rotate(1.5, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m4_rot.getbbox()
        rw4, rh4 = rot4.size
        muse_src = tmp_p / "muse_clean.png"
        rot4.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw4, bx1 + pad), min(rh4, by1 + pad))).save(muse_src)

        build_svg_and_braille(
            muse_src,
            assets_dir,
            "find_your_muse_roses_november",
            title='"FIND YOUR MUSE / ROSES IN NOVEMBER" — NICHOLAS KLOSTER',
            subtitle='Signed Unlined Holograph Leaf · "NICHOLAS KLOSTER" Manuscript (Specimen #24)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=34.0,
            paper_cutoff=0.91,
            ink_floor=0.38,
            gamma=1.20,
            levels=(0.14, 0.32, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 6x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~41s)
        fps = 15
        target_frames = 615  # 41.0s out for 245.12s real (~5.98x)
        vw, vh = 406, 720
        real_dur = 245.12
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 4m 05s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC24),
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

        tl_mp4 = tmp_p / "kloster_folio_tl.mp4"
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
            raise RuntimeError("Specimen #24 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 32:
                return "TITLE · KLOSTER", (94, 218, 238)
            if rsec < 115:
                return "THUMBS & STACK", (242, 196, 92)
            if rsec < 168:
                return "FATHER & MUSE", (244, 106, 126)
            if rsec < 192:
                return "DESTINY · MOON EYES", (195, 162, 255)
            return "CHOPIN, SATIE & END", (168, 226, 142)

        out_mp4 = video_dir / "specimen24_nicholas_kloster_folio_overlay.mp4"
        poster_png = video_dir / "specimen24_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #24 · "NICHOLAS KLOSTER" LOOSE-LEAF FOLIO',
            header_sub='"Destiny Is Like a Woman", "Find Your Muse" & "Chopin, Satie" (6x Reel)',
            phase_fn=phase_fn,
            nexus_band=(168.0, 186.0, 'NEXUS · "DESTINY IS LIKE A WOMAN"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=176.5,
            episode_interval_s=4.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~62 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 176.5)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen24_nicholas_kloster_folio",
        title='SPECIMEN #24 · "NICHOLAS KLOSTER" LOOSE-LEAF MANUSCRIPT',
        subtitle='4m 05s Unlined White Folio · "Destiny", "Find Your Muse", Thumbs & "Satie"',
        nexus_label='"DESTINY" LEAF (2:56)',
        footer_label='Fieldglass Specimen #24 · "NICHOLAS KLOSTER" Manuscript Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp24",
    )

    summary = {
        "specimen24": {
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
    build_specimen24()
