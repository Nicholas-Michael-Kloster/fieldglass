#!/usr/bin/env python3
"""Build Fieldglass Specimen #23 — Yellow Folder: "Unpublishable Bullshit" & Time-Traveling "Sovio" Leaves.

Source:
  - /tmp/zoe_s23/s23_825m.mp4 (zoe_vid_1795740161734.mp4)
    (2026-11-26 18:45, 2m 39s [158.86s], 4K portrait 2160x3840 @ 30fps)

Complete flip-through of Nicholas Kloster's yellow folder of loose unlined handwritten
and typewritten poetry sheets (Summer 2012 — the companion folio to Specimen #22's Scarab
Beetle "Unpublishable Bullshit" cover). Features "What Exactly Makes a Poem?" (June 19th),
"Fairy Tales and Stories of Hope" (signed), "Whispering Into the Def Ears of Un-Lined
Paper" (signed), "Kiss Me Silently / The Matador" (6-27-12), and Nick's playful sequence
of fictitiously back-dated poems signed "Sovio" (6-25-1840, 6-25-1857, 6-25-1837,
6-25-1833 — "Just trying to mess with my own head from the past!").

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "Fairy Tales and Stories of Hope" (Signed Nicholas Kloster · Unlined Sheet)
      2) "The 500 Year Old Tree" (Typewritten + Signed "Sovio · 6-25-1840")
  - Fast keyframe-decoded 1280x720 4x silent Kloster A_tau(p_t) telemetry reel (~40s, <7 MB)
  - ~54-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC23 = Path("/tmp/zoe_s23/s23_825m.mp4")


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


def build_specimen23() -> dict:
    print("\n================ BUILDING SPECIMEN #23 (YELLOW FOLDER · 'FAIRY TALES & SOVIO 1840') ================")
    root = DOCS / "specimen23"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K hero plates
        im01 = _extract_exact_4k(SRC23, 12.5, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_what_makes_a_poem_jun19.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC23, 47.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_fairy_tales_and_stories_of_hope.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC23, 49.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_unlined_paper_poet_signed.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC23, 76.0, tmp_p / "raw_04.jpg")
        p04 = plates_dir / "04_500_year_old_tree_sovio_1840.jpg"
        im04_s = im04.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC23, 97.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_voiceless_faceless_songs_1857.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC23, 135.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_kiss_me_silently_matador_jun27.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:12 · 'What Makes a Poem?' (Jun 19)", p01),
            ("00:47 · 'Fairy Tales & Stories of Hope'", p02),
            ("00:49 · 'Ears of Un-Lined Paper'", p03),
            ("01:16 · '500 Year Old Tree' (1840)", p04),
            ("01:37 · 'Voiceless Songs' (Sovio 1857)", p05),
            ("02:15 · 'The Matador' (6-27-12)", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen23.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Vector SVGs + 72-Col 2x4 Braille Broadsides!
        pad = 24
        # SVG #1: "Fairy Tales and Stories of Hope" (Signed Nicholas Kloster · Unlined Sheet)
        w2, h2 = im02.size
        arr2 = np.asarray(im02, dtype=np.uint8)
        p2_col = tuple(int(v) for v in np.median(arr2[int(h2 * 0.30):int(h2 * 0.45), int(w2 * 0.76):int(w2 * 0.92)].reshape(-1, 3), axis=0))
        poly2 = [
            (int(w2 * 0.195), int(h2 * 0.105)),
            (int(w2 * 0.965), int(h2 * 0.145)),
            (int(w2 * 0.945), int(h2 * 0.768)),
            (int(w2 * 0.105), int(h2 * 0.706)),
            (int(w2 * 0.115), int(h2 * 0.595)),
            (int(w2 * 0.165), int(h2 * 0.555)),
        ]
        m2 = Image.new("L", (w2, h2), 0)
        ImageDraw.Draw(m2).polygon(poly2, fill=255)
        c2 = Image.new("RGB", (w2, h2), p2_col)
        c2.paste(im02, (0, 0), m2)
        rot2 = c2.rotate(7.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p2_col)
        m2_rot = m2.rotate(7.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m2_rot.getbbox()
        rw2, rh2 = rot2.size
        fairy_src = tmp_p / "fairy_tales_clean.png"
        rot2.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw2, bx1 + pad), min(rh2, by1 + pad))).save(fairy_src)

        build_svg_and_braille(
            fairy_src,
            assets_dir,
            "fairy_tales_and_stories_of_hope",
            title='"FAIRY TALES AND STORIES OF HOPE" — NICHOLAS KLOSTER',
            subtitle="Signed Unlined Holograph Sheet · Yellow Folder Poetry Manuscript (Specimen #23)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=36.0,
            paper_cutoff=0.90,
            ink_floor=0.38,
            gamma=1.22,
            levels=(0.18, 0.38, 1.2),
            braille_cols=72,
        )

        # SVG #2: "The 500 Year Old Tree" (Typewritten + Signed "Sovio · 6-25-1840")
        w4, h4 = im04.size
        arr4 = np.asarray(im04, dtype=np.uint8)
        p4_col = tuple(int(v) for v in np.median(arr4[int(h4 * 0.44):int(h4 * 0.58), int(w4 * 0.52):int(w4 * 0.78)].reshape(-1, 3), axis=0))
        poly4 = [
            (int(w4 * 0.335), int(h4 * 0.195)),
            (int(w4 * 0.965), int(h4 * 0.240)),
            (int(w4 * 0.938), int(h4 * 0.780)),
            (int(w4 * 0.290), int(h4 * 0.735)),
        ]
        m4 = Image.new("L", (w4, h4), 0)
        ImageDraw.Draw(m4).polygon(poly4, fill=255)
        c4 = Image.new("RGB", (w4, h4), p4_col)
        c4.paste(im04, (0, 0), m4)
        rot4 = c4.rotate(9.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p4_col)
        m4_rot = m4.rotate(9.0, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m4_rot.getbbox()
        rw4, rh4 = rot4.size
        tree_src = tmp_p / "tree_1840_clean.png"
        rot4.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw4, bx1 + pad), min(rh4, by1 + pad))).save(tree_src)

        build_svg_and_braille(
            tree_src,
            assets_dir,
            "five_hundred_year_old_tree_sovio_1840",
            title='"THE 500 YEAR OLD TREE" — SOVIO (6-25-1840)',
            subtitle="Typewritten & Signed Time-Traveling Leaf · Yellow Folder Manuscript (Specimen #23)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=30.0,
            paper_cutoff=0.925,
            ink_floor=0.38,
            gamma=1.18,
            levels=(0.12, 0.30, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 4x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~40s)
        fps = 15
        target_frames = 600  # 40.0s out for 158.86s real (~3.97x)
        vw, vh = 406, 720
        real_dur = 158.86
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 2m 39s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC23),
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

        tl_mp4 = tmp_p / "yellow_folder_tl.mp4"
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
            raise RuntimeError("Specimen #23 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 40:
                return "JUN 19 · WHAT IS POEM", (94, 218, 238)
            if rsec < 68:
                return "STORIES OF HOPE", (242, 196, 92)
            if rsec < 120:
                return "SOVIO · 1833–1999", (244, 106, 126)
            return "JUN 27 · THE MATADOR", (195, 162, 255)

        out_mp4 = video_dir / "specimen23_yellow_folder_overlay.mp4"
        poster_png = video_dir / "specimen23_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #23 · YELLOW FOLDER ("STORIES OF HOPE" & "SOVIO")',
            header_sub="Unlined Holographs & Time-Traveling 1840–1999 Leaves (4x Telemetry Reel)",
            phase_fn=phase_fn,
            nexus_band=(70.0, 84.0, 'NEXUS · "SOVIO · 6-25-1840"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=76.0,
            episode_interval_s=3.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~54 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 76.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen23_yellow_folder",
        title='SPECIMEN #23 · YELLOW FOLDER ("STORIES OF HOPE" & "SOVIO 1840")',
        subtitle='2m 39s Unlined Manuscript · "Fairy Tales", Typewritten 500-Year Tree & Matador',
        nexus_label='"SOVIO 1840" LEAF (1:16)',
        footer_label='Fieldglass Specimen #23 · Yellow Folder ("Sovio") Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp23",
    )

    summary = {
        "specimen23": {
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
    build_specimen23()
