#!/usr/bin/env python3
"""Build Fieldglass Specimen #17 — "The American" (2012 Poetry Notebook & Studio Reading).

Source:
  - /tmp/zoe_s17/zoe_vid_1795732573061.mp4
    (2026-11-26 16:56, 17m 44s [1064.25s], 4K portrait 2160x3840 @ 30fps, stereo studio voice)

Nick and Dr. Helen Ruth Horkan read aloud from Nick's 2012 blue-pen poetry notebook
("The American", dedicated "For Farkas, wherever you may be") — timestamped by exact
minute of night rather than year ("I've never experienced 1927, but I've experienced
November 6th, 11:41 p.m."), spanning "I Strike a Match" (Oct 24), "Parking Lot Blues"
(Oct 25), "Will My Poems Last Forever" (1:45 am Oct 25), "The Makeshift Butterfly",
"A Dog Barks / Then It Is Quiet" (Oct 27), Dr. Helen matching his April 4, 2012 poem
to her own day, and closing with "Big Tree, Just Be" (Nov 10) ("straight from the dome,
free-throw, first draft, one-time go").

Generates:
  - 6 crisp GPS-scrubbed upright 4K manuscript plates + 3x2 contact sheet
  - 2 Red-Channel Blue-Pen Prussian-Indigo Vector SVGs + 72-Col 2x4 Braille:
      1) "Will my poems, last forever, on bookshelves..." (1:45 am · Oct 25)
      2) "Big Tree, Just Be." (2:35 pm · Nov 10)
  - Fast keyframe-decoded 1280x720 18x Kloster A_tau(p_t) telemetry reel (~59s, <10 MB)
  - Full 17m 44s GPS-scrubbed studio reading & dialogue MP3 (~4.1 MB)
  - ~177-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    extract_plate,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)
from build_specimen14_poetry import build_blue_pen_indigo_svg_and_braille

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC17 = Path("/tmp/zoe_s17/zoe_vid_1795732573061.mp4")


def build_specimen17() -> dict:
    print("\n================ BUILDING SPECIMEN #17 ('THE AMERICAN' · 2012 POETRY NOTEBOOK) ================")
    root = DOCS / "specimen17"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    audio_dir = root / "audio"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir, audio_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1) Extract 6 razor-sharp upright 4K manuscript plates across the 17m 44s notebook
    plate_specs = [
        ("01_i_strike_a_match_oct24", "01:28 · Oct 24: 'I Strike a Match'", 87.5, 2.0),
        ("02_parking_lot_blues_oct25", "02:39 · Oct 25: 'Parking Lot Blues'", 158.0, 2.5),
        ("03_will_my_poems_last_forever", "04:56 · Oct 25: 'Will My Poems Last Forever'", 295.0, 3.0),
        ("04_makeshift_butterfly_story", "07:23 · 'The Makeshift Butterfly'", 442.0, 2.5),
        ("05_a_dog_barks_then_quiet", "09:45 · Oct 27: 'Then It Is Quiet'", 583.5, 2.0),
        ("06_big_tree_just_be_nov10", "17:30 · Nov 10: 'Big Tree, Just Be'", 1048.5, 3.0),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win in plate_specs:
        ts, p = extract_plate(
            SRC17,
            plates_dir / f"{slug}.jpg",
            start_sec=t0,
            window_sec=win,
            sample_fps=3,
            max_dim=1600,
        )
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s")

    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen17.jpg", cols=3, tile_w=420, tile_h=560)

    # 2) Two Red-Channel Prussian-Indigo Vector SVGs + 72-Col 2x4 Braille Broadsides
    forever_svg = build_blue_pen_indigo_svg_and_braille(
        pmap["03_will_my_poems_last_forever"],
        assets_dir,
        "will_my_poems_last_forever_indigo",
        title='"WILL MY POEMS LAST FOREVER" (1:45 AM · OCT 25)',
        subtitle='Red-Channel Blue-Ink Broadside · "The American" 2012 Notebook (Specimen #17)',
        crop_box=(0.08, 0.215, 0.94, 0.78),
        sigma=40.0,
        paper_cutoff=0.945,
        ink_floor=0.52,
        gamma=1.16,
        braille_cols=72,
    )
    tree_svg = build_blue_pen_indigo_svg_and_braille(
        pmap["06_big_tree_just_be_nov10"],
        assets_dir,
        "big_tree_just_be_indigo",
        title='"BIG TREE, JUST BE." (2:35 PM · NOV 10)',
        subtitle='Red-Channel Blue-Ink Broadside · "The American" 2012 Notebook (Specimen #17)',
        crop_box=(0.275, 0.122, 0.92, 0.955),
        sigma=38.0,
        paper_cutoff=0.945,
        ink_floor=0.54,
        gamma=1.15,
        braille_cols=72,
    )

    # 3) Full 17m 44s GPS-scrubbed companion studio reading & dialogue MP3 (~4.1 MB)
    out_mp3 = audio_dir / "specimen17_the_american_reading.mp3"
    print("Exporting full 17m 44s GPS-scrubbed studio reading MP3...")
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(SRC17), "-vn",
            "-map_metadata", "-1",
            "-ac", "1", "-ar", "22050", "-b:a", "32k",
            str(out_mp3),
        ],
        check=True,
    )
    mp3_mb = round(out_mp3.stat().st_size / 1e6, 2)
    print(f"  Audio ready: {out_mp3.name} ({mp3_mb} MB)")

    # 4) Fast keyframe-decoded 18x portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~59s)
    fps = 15
    target_frames = 885  # 59.0s out for 1064.25s real (~18.04x)
    vw, vh = 406, 720
    real_dur = 1064.25
    time_scale = real_dur / (target_frames / float(fps))

    print(f"Decoding keyframes from 17m 44s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-skip_frame", "nokey",
        "-i", str(SRC17),
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

    with tempfile.TemporaryDirectory() as tmp:
        tl_mp4 = Path(tmp) / "american_tl.mp4"
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
            raise RuntimeError("Specimen #17 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 150:
                return "OCT 24 · I STRIKE A MATCH", (94, 218, 238)
            if rsec < 340:
                return "OCT 25 · WILL MY POEMS LAST", (242, 196, 92)
            if rsec < 540:
                return "MAKESHIFT BUTTERFLY & HELEN", (244, 106, 126)
            if rsec < 760:
                return "OCT 27–NOV 4 · APRIL 2012", (195, 162, 255)
            if rsec < 960:
                return "NOV 8 · TIME OVER YEAR", (168, 226, 142)
            return "NOV 10 · BIG TREE, JUST BE", (94, 218, 238)

        out_mp4 = video_dir / "specimen17_the_american_overlay.mp4"
        poster_png = video_dir / "specimen17_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #17 · "THE AMERICAN" (2012 POETRY NOTEBOOK)',
            header_sub="Blue-Pen Notebook + Studio Reading w/ Dr. Helen (18x Reel + 17m44s MP3)",
            phase_fn=phase_fn,
            nexus_band=(280.0, 325.0, 'NEXUS · "WILL MY POEMS LAST"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=296.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 5) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~177 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 296.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen17_the_american",
        title='SPECIMEN #17 · "THE AMERICAN" (2012 BLUE-PEN NOTEBOOK)',
        subtitle='17m 44s Studio Reading w/ Dr. Helen · "Will My Poems Last Forever" & "Big Tree"',
        nexus_label='"WILL MY POEMS LAST" (4:56)',
        footer_label='Fieldglass Specimen #17 · "The American" (2012) Red-Channel Indigo Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp17",
    )

    summary = {
        "specimen17": {
            "mp4_mb": ov["mp4_mb"],
            "mp3_mb": mp3_mb,
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
    build_specimen17()
