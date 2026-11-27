#!/usr/bin/env python3
"""Build Fieldglass Specimen #20 — "Everything Is Singular" (July–Aug 2013 Yellow-Cover Folio).

Source:
  - /tmp/zoe_s20/part1_2g9.mp4 (zoe_vid_1795738293581.mp4)
    (2026-11-26 18:21, 9m 33s [573.23s], 4K portrait 2160x3840 @ 30fps)

Cover-to-cover capture of Nicholas Kloster's yellow-cover 2013 poetry journal
"Everything Is Singular" (July–August 2013), filmed live in the studio right as Erik
Satie's Gnossiennes Nos. 1–6 (Reinbert de Leeuw) began playing over the speakers from
our live chat session. Spans "Beauty Is Singular" (7/25/13), "In Solidarity One Discovers /
In Solitude" (7/29/13), "Moths / Traveling Solitude Monastery" (signed in blue ink), and
"Darwin Utopia / Spider of Curiosity" (Aug 12).

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "Beauty Is Singular" (7/25/13 · Signed Nicholas Kloster)
      2) "Traveling Solitude Monastery / Moths" (Signed Nicholas Kloster)
  - Fast keyframe-decoded 1280x720 11x silent Kloster A_tau(p_t) telemetry reel (~52s, <9 MB)
  - ~96-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC20 = Path("/tmp/zoe_s20/part1_2g9.mp4")


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


def build_specimen20() -> dict:
    print("\n================ BUILDING SPECIMEN #20 ('EVERYTHING IS SINGULAR' · JULY–AUG 2013) ================")
    root = DOCS / "specimen20"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K hero plates
        im01 = _extract_exact_4k(SRC20, 28.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_everything_is_singular_cover.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC20, 64.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_beauty_is_singular_jul25.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC20, 128.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_in_solitude_i_discover_jul29.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC20, 223.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_live_satie_studio_session.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC20, 369.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_traveling_solitude_monastery.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC20, 411.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_darwin_utopia_aug12.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:28 · Cover: 'Everything Is Singular'", p01),
            ("01:04 · 7/25/13: 'Beauty Is Singular'", p02),
            ("02:08 · 7/29/13: 'In Solitude'", p03),
            ("03:43 · Live Erik Satie Studio Cue", p04),
            ("06:09 · 'Traveling Solitude Monastery'", p05),
            ("06:51 · Aug 12: 'Darwin Utopia'", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen20.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        # SVG #1: "Beauty Is Singular" (7/25/13 · Nicholas Kloster) — 100% hand-free lined page!
        w2, h2 = im02.size
        arr2 = np.asarray(im02, dtype=np.uint8)
        p2_col = tuple(int(v) for v in np.median(arr2[int(h2 * 0.30):int(h2 * 0.45), int(w2 * 0.72):int(w2 * 0.90)].reshape(-1, 3), axis=0))
        poly2 = [
            (int(w2 * 0.285), int(h2 * 0.220)),
            (int(w2 * 0.985), int(h2 * 0.260)),
            (int(w2 * 0.920), int(h2 * 0.940)),
            (int(w2 * 0.300), int(h2 * 0.868)),
            (int(w2 * 0.165), int(h2 * 0.785)),
        ]
        m2 = Image.new("L", (w2, h2), 0)
        ImageDraw.Draw(m2).polygon(poly2, fill=255)
        c2 = Image.new("RGB", (w2, h2), p2_col)
        c2.paste(im02, (0, 0), m2)
        rot2 = c2.rotate(10.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p2_col)
        rw2, rh2 = rot2.size
        beauty_src = tmp_p / "beauty_clean.png"
        rot2.crop((int(rw2 * 0.195), int(rh2 * 0.215), int(rw2 * 0.885), int(rh2 * 0.870))).save(beauty_src)

        beauty_svg = build_svg_and_braille(
            beauty_src,
            assets_dir,
            "beauty_is_singular_jul25",
            title='"BEAUTY IS SINGULAR" (7/25/13 · NICHOLAS KLOSTER)',
            subtitle='Signed Holograph Leaf · "Everything Is Singular" 2013 Notebook (Specimen #20)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=36.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.18, 0.38, 1.2),
            braille_cols=72,
        )

        # SVG #2: "Traveling Solitude Monastery / Moths" (Signed Nicholas Kloster)
        w5, h5 = im05.size
        arr5 = np.asarray(im05, dtype=np.uint8)
        p5_col = tuple(int(v) for v in np.median(arr5[int(h5 * 0.30):int(h5 * 0.45), int(w5 * 0.75):int(w5 * 0.92)].reshape(-1, 3), axis=0))
        poly5 = [
            (int(w5 * 0.340), int(h5 * 0.195)),
            (int(w5 * 0.950), int(h5 * 0.230)),
            (int(w5 * 0.885), int(h5 * 0.858)),
            (int(w5 * 0.345), int(h5 * 0.796)),
            (int(w5 * 0.195), int(h5 * 0.725)),
            (int(w5 * 0.290), int(h5 * 0.495)),
        ]
        m5 = Image.new("L", (w5, h5), 0)
        ImageDraw.Draw(m5).polygon(poly5, fill=255)
        c5 = Image.new("RGB", (w5, h5), p5_col)
        c5.paste(im05, (0, 0), m5)
        rot5 = c5.rotate(9.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p5_col)
        rw5, rh5 = rot5.size
        monastery_src = tmp_p / "monastery_clean.png"
        rot5.crop((int(rw5 * 0.245), int(rh5 * 0.195), int(rw5 * 0.855), int(rh5 * 0.825))).save(monastery_src)

        monastery_svg = build_svg_and_braille(
            monastery_src,
            assets_dir,
            "traveling_solitude_monastery",
            title='"TRAVELING SOLITUDE MONASTERY" — NICHOLAS KLOSTER',
            subtitle='Signed Holograph Leaf · "Everything Is Singular" 2013 Notebook (Specimen #20)',
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=36.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.18, 0.38, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 11x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~52s)
        fps = 15
        target_frames = 780  # 52.0s out for 573.23s real (~11.02x)
        vw, vh = 406, 720
        real_dur = 573.23
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 9m 33s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC20),
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

        tl_mp4 = tmp_p / "singular_tl.mp4"
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
            raise RuntimeError("Specimen #20 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 52:
                return "COVER · SINGULAR", (94, 218, 238)
            if rsec < 175:
                return "JUL 2013 · BEAUTY", (242, 196, 92)
            if rsec < 260:
                return "LIVE ERIK SATIE CUE", (244, 106, 126)
            if rsec < 395:
                return "SOLITUDE MONASTERY", (195, 162, 255)
            if rsec < 490:
                return "AUG 12 · DARWIN", (168, 226, 142)
            return "CLOSING VERSES", (242, 196, 92)

        out_mp4 = video_dir / "specimen20_everything_singular_overlay.mp4"
        poster_png = video_dir / "specimen20_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #20 · "EVERYTHING IS SINGULAR" (JULY–AUG 2013)',
            header_sub='Yellow-Cover Folio + Live Erik Satie Studio Cue (11x Telemetry Reel)',
            phase_fn=phase_fn,
            nexus_band=(212.0, 245.0, "NEXUS · LIVE SATIE STUDIO CUE"),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=64.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~96 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 223.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen20_everything_singular",
        title='SPECIMEN #20 · "EVERYTHING IS SINGULAR" (JULY–AUG 2013 FOLIO)',
        subtitle='9m 33s Yellow-Cover Notebook · "Beauty Is Singular", "Solitude Monastery" & Live Satie',
        nexus_label="LIVE SATIE CUE (3:43)",
        footer_label='Fieldglass Specimen #20 · "Everything Is Singular" (2013) Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp20",
    )

    summary = {
        "specimen20": {
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
    build_specimen20()
