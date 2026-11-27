#!/usr/bin/env python3
"""Build Fieldglass Specimen #18 — Kraft-Paper Poetry Manuscript (Oct 29 – Nov 29, 2012).

Source:
  - /tmp/zoe_s18/zoe_vid_1795736059543.mp4
    (2026-11-26 17:55, 21m 06s [1266.05s], 4K portrait 2160x3840 @ 30fps)

Cover-to-cover page-turn documentation of Nicholas Kloster's unlined kraft-paper poetry
notebook (Oct 29 – Nov 29), filmed in the studio beneath Dr. Helen's chalkboard jellyfish
while Persian oud & setar music plays in the room. Spans "Tonight I Write Saddest Lines"
(Neruda & Rimbaud, Oct 30 · 1:30 am), "He Undressed, Took Out His Pistol, and Wrote His
Final Poem" (Nov 5), "My Charcoal Knowledge / I Have My Hands" (Nov 19 · 4:11 pm, rotated
upright), and the closing signed leaf "I Layed Out in a Field" (Nov 29 · Nicholas Kloster).

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Archival Sepia-Ink Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) "I Layed Out in a Field" (Nov 29 · Signed Nicholas Kloster)
      2) "Tonight I Write Saddest Lines" (Neruda & Rimbaud · Oct 30 · 1:30 am)
  - Fast keyframe-decoded 1280x720 21x silent Kloster A_tau(p_t) telemetry reel (~60s, <10 MB)
  - ~211-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    build_svg_and_braille,
    extract_plate,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC18 = Path("/tmp/zoe_s18/zoe_vid_1795736059543.mp4")


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


def build_specimen18() -> dict:
    print("\n================ BUILDING SPECIMEN #18 (KRAFT-PAPER POETRY MANUSCRIPT · OCT 29 – NOV 29) ================")
    root = DOCS / "specimen18"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp upright GPS-scrubbed hero plates
        # Plate 01: Studio desk with Avin Ahmadi oud & Dr. Helen's chalkboard jellyfish behind (01:12)
        im01 = _extract_exact_4k(SRC18, 72.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_studio_oud_and_chalkboard.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        # Plate 02: "Tonight I Write Saddest Lines" (Neruda & Rimbaud · Oct 30, 1:30 am @ 150.0s)
        im02 = _extract_exact_4k(SRC18, 150.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_tonight_i_write_saddest_lines_oct30.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        # Plate 03: Minimalist Nov 5th page ("He undressed, took out his pistol, and wrote his final poem")
        ts3, p03 = extract_plate(
            SRC18, plates_dir / "03_final_poem_nov5.jpg",
            start_sec=526.0, window_sec=2.5, sample_fps=3, max_dim=1600,
        )
        print(f"  Plate 03_final_poem_nov5 @ {ts3:.1f}s")

        # Plate 04: "My Charcoal Knowledge / I Have My Hands" (Nov 19, 4:11 pm — rotated 90° CCW upright!)
        im04 = _extract_exact_4k(SRC18, 988.0, tmp_p / "raw_04.jpg").transpose(Image.Transpose.ROTATE_90)
        p04 = plates_dir / "04_charcoal_knowledge_hands_nov19.jpg"
        im04.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04.save(p04, quality=92, optimize=True)

        # Plate 05: "Visited Myself at the Public Insane Asylum / Roof at 35th Street" (Nov 19 @ ~1160s)
        ts5, p05 = extract_plate(
            SRC18, plates_dir / "05_roof_at_35th_street_nov19.jpg",
            start_sec=1158.0, window_sec=3.0, sample_fps=3, max_dim=1600,
        )
        print(f"  Plate 05_roof_at_35th_street_nov19 @ {ts5:.1f}s")

        # Plate 06: Closing signed poem "I Layed Out in a Field" (Nov 29 · Nicholas Kloster @ 1246.0s)
        im06 = _extract_exact_4k(SRC18, 1246.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_layed_out_in_a_field_nov29.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("01:12 · Oud Soundtrack & Chalkboard", p01),
            ("02:30 · Oct 30: Neruda & Rimbaud", p02),
            ("08:47 · Nov 5: Minimalist 4-Line Page", p03),
            ("16:28 · Nov 19: 'Charcoal Knowledge'", p04),
            ("19:20 · Nov 19: 'Roof at 35th Street'", p05),
            ("20:46 · Nov 29: 'Layed Out in a Field'", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen18.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Archival Sepia-Ink Vector SVGs + 72-Col 2x4 Braille Broadsides!
        # SVG #1: "I Layed Out in a Field" (Nov 29 · Signed Nicholas Kloster)
        #   Cleanly mask bottom-left thumb tip (x<0.16, y>0.66 inside crop) with exact local kraft paper tone!
        w6, h6 = im06.size
        c6 = im06.crop((int(w6 * 0.335), int(h6 * 0.198), int(w6 * 0.935), int(h6 * 0.785)))
        arr6 = np.asarray(c6, dtype=np.uint8).copy()
        ch6, cw6 = arr6.shape[:2]
        # Sample clean kraft paper median color from right margin
        paper_col = np.median(arr6[int(ch6 * 0.25):int(ch6 * 0.60), int(cw6 * 0.85):int(cw6 * 0.96)].reshape(-1, 3), axis=0).astype(np.uint8)
        # Mask lower-left thumb triangle safely clear of all ink ("I layed out" ends at y~0.68, signature starts x~0.17)
        arr6[int(ch6 * 0.64):, :int(cw6 * 0.155)] = paper_col
        field_src = tmp_p / "field_clean.png"
        Image.fromarray(arr6).save(field_src)

        field_svg = build_svg_and_braille(
            field_src,
            assets_dir,
            "layed_out_in_a_field_nov29",
            title='"I LAYED OUT IN A FIELD" (NOV 29 · NICHOLAS KLOSTER)',
            subtitle="Kraft-Paper Poetry Manuscript · Signed Closing Leaf (Specimen #18 · 2026-11-26)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=42.0,
            paper_cutoff=0.92,
            ink_floor=0.42,
            gamma=1.20,
            levels=(0.14, 0.34, 1.2),
            braille_cols=72,
        )

        # SVG #2: "Tonight I Write Saddest Lines" (Neruda & Rimbaud · Oct 30, 1:30 am)
        #   Polygon-mask strictly inside the kraft paper sheet (erasing laptop vents, top edge & thumb) + deskew +13.5 deg!
        from PIL import ImageDraw
        w2, h2 = im02.size
        p2_col = tuple(int(v) for v in np.median(np.asarray(im02)[int(h2 * 0.30):int(h2 * 0.50), int(w2 * 0.72):int(w2 * 0.84)].reshape(-1, 3), axis=0))
        poly = [
            (int(w2 * 0.145), int(h2 * 0.122)),
            (int(w2 * 0.920), int(h2 * 0.238)),
            (int(w2 * 0.770), int(h2 * 0.790)),
            (int(w2 * 0.055), int(h2 * 0.720)),
            (int(w2 * 0.165), int(h2 * 0.360)),
            (int(w2 * 0.195), int(h2 * 0.295)),
            (int(w2 * 0.180), int(h2 * 0.225)),
        ]
        mask2 = Image.new("L", (w2, h2), 0)
        ImageDraw.Draw(mask2).polygon(poly, fill=255)
        clean2 = Image.new("RGB", (w2, h2), p2_col)
        clean2.paste(im02, (0, 0), mask2)
        im02_rot = clean2.rotate(13.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p2_col)
        rw2, rh2 = im02_rot.size
        neruda_src = tmp_p / "neruda_clean.png"
        im02_rot.crop((int(rw2 * 0.145), int(rh2 * 0.180), int(rw2 * 0.835), int(rh2 * 0.755))).save(neruda_src)

        neruda_svg = build_svg_and_braille(
            neruda_src,
            assets_dir,
            "tonight_i_write_saddest_lines_oct30",
            title='"TONIGHT I WRITE SADDEST LINES" (OCT 30 · 1:30 AM)',
            subtitle="Neruda & Rimbaud Kraft-Paper Holograph · Nicholas Kloster (Specimen #18)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=42.0,
            paper_cutoff=0.92,
            ink_floor=0.42,
            gamma=1.20,
            levels=(0.15, 0.35, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 21x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~60s)
        fps = 15
        target_frames = 900  # 60.0s out for 1266.05s real (~21.10x)
        vw, vh = 406, 720
        real_dur = 1266.05
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 21m 06s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC18),
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

        tl_mp4 = tmp_p / "kraft_tl.mp4"
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
            raise RuntimeError("Specimen #18 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 120:
                return "OCT 29 · STUDIO & OPENING", (94, 218, 238)
            if rsec < 310:
                return "OCT 30 · NERUDA & RIMBAUD", (242, 196, 92)
            if rsec < 550:
                return "NOV 5 · FINAL POEM & SIREN", (244, 106, 126)
            if rsec < 860:
                return "MID-FOLIO · ROTATED VERSES", (195, 162, 255)
            if rsec < 1120:
                return "NOV 19 · CHARCOAL KNOWLEDGE", (168, 226, 142)
            return "NOV 29 · LAYED OUT IN A FIELD", (242, 196, 92)

        out_mp4 = video_dir / "specimen18_kraft_notebook_overlay.mp4"
        poster_png = video_dir / "specimen18_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title="SPECIMEN #18 · KRAFT-PAPER POETRY MANUSCRIPT (OCT–NOV)",
            header_sub='Neruda & Rimbaud, "Charcoal Knowledge" & "Layed Out in a Field" (21x)',
            phase_fn=phase_fn,
            nexus_band=(515.0, 555.0, 'NEXUS · NOV 5 MINIMALIST LEAF'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=1246.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~211 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 530.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen18_kraft_notebook",
        title="SPECIMEN #18 · KRAFT-PAPER POETRY MANUSCRIPT (OCT 29 – NOV 29)",
        subtitle='21m 06s Cover-to-Cover Folio · "Tonight I Write Saddest Lines" & "Layed Out in a Field"',
        nexus_label="NOV 5 MINIMALIST LEAF (8:50)",
        footer_label="Fieldglass Specimen #18 · Kraft-Paper Sepia Poetry Manuscript Telemetry",
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp18",
    )

    summary = {
        "specimen18": {
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
    build_specimen18()
