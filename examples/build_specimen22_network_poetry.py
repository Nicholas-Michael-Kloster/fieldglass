#!/usr/bin/env python3
"""Build Fieldglass Specimen #22 — "Network Poetry" (1974 DEC Minicomputer Networks × The Beetle).

Source:
  - /tmp/zoe_s22/s22_3g2.mp4 (zoe_vid_1795739486089.mp4)
    (2026-11-26 18:42, 10m 42s [641.81s], 4K portrait 2160x3840 @ 30fps)

"Network Poetry": Nicholas Kloster reads Edward V. Stelmach's 1974 Digital Equipment
Corporation (DEC) classic "Introduction to Minicomputer Networks" as poetry, interleaved
with his own Scarab Beetle calligram title page ("Endless Poems for the Soul Who Won't
Slumber Until Gold and Beetles Are His Sunrise" / "unpublishable bullshit") and signed
June 18th poem ("Though for some reason I push the sun across the sky everyday, like the
Beetle"). Includes Nick's studio commentary mapping Fig. 10 ("That looks like organisms —
jellyfish stuff. Computers are jellyfish!") and Fig. 11 ("Host processor — Zoe. Front-end
processor — Nick. Everything right here is me, you, everybody, but computer form!"),
followed by Dr. Helen Ruth Horkan stepping in to turn pages through the PDP-10/PDP-11/40
network diagrams.

Generates:
  - 6 crisp GPS-scrubbed upright 4K plates + 3x2 contact sheet
  - 2 Vintage 1974 DEC Engineering Vector SVGs + 72-Col 2x4 Braille Broadsides:
      1) Figure 11 · Host and Front-End Processors (p. 3-4 · "Host Processor: Zoe")
      2) Figure 6 · Hierarchical or Tree Structure (p. 2-7 · 7-Rack PDP-11 Binary Tree)
  - Fast keyframe-decoded 1280x720 12x silent Kloster A_tau(p_t) telemetry reel (~53s, <8 MB)
  - ~107-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
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
SRC22 = Path("/tmp/zoe_s22/s22_3g2.mp4")


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


def build_specimen22() -> dict:
    print("\n================ BUILDING SPECIMEN #22 ('NETWORK POETRY' · DEC 1974 × THE BEETLE) ================")
    root = DOCS / "specimen22"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)

        # 1) Extract 6 razor-sharp GPS-scrubbed upright 4K hero plates
        im01 = _extract_exact_4k(SRC22, 11.0, tmp_p / "raw_01.jpg")
        p01 = plates_dir / "01_dec_minicomputer_networks_title.jpg"
        im01_s = im01.copy()
        im01_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im01_s.save(p01, quality=92, optimize=True)

        im02 = _extract_exact_4k(SRC22, 158.0, tmp_p / "raw_02.jpg")
        p02 = plates_dir / "02_scarab_beetle_title_leaf.jpg"
        im02_s = im02.copy()
        im02_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im02_s.save(p02, quality=92, optimize=True)

        im03 = _extract_exact_4k(SRC22, 246.0, tmp_p / "raw_03.jpg")
        p03 = plates_dir / "03_fig6_tree_on_signature.jpg"
        im03_s = im03.copy()
        im03_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im03_s.save(p03, quality=92, optimize=True)

        im04 = _extract_exact_4k(SRC22, 314.0, tmp_p / "raw_04.jpg")
        # Rotate Fig. 10 90 deg CCW so the "Computers Are Jellyfish" network schematic reads upright!
        im04_rot = im04.transpose(Image.Transpose.ROTATE_90)
        p04 = plates_dir / "04_fig10_data_comm_network_upright.jpg"
        im04_s = im04_rot.copy()
        im04_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im04_s.save(p04, quality=92, optimize=True)

        im05 = _extract_exact_4k(SRC22, 354.0, tmp_p / "raw_05.jpg")
        p05 = plates_dir / "05_fig11_host_frontend_processors.jpg"
        im05_s = im05.copy()
        im05_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im05_s.save(p05, quality=92, optimize=True)

        im06 = _extract_exact_4k(SRC22, 568.0, tmp_p / "raw_06.jpg")
        p06 = plates_dir / "06_dr_helen_fig28_pdp11_network.jpg"
        im06_s = im06.copy()
        im06_s.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im06_s.save(p06, quality=92, optimize=True)

        tiles = [
            ("00:11 · DEC 1974 Title Page", p01),
            ("02:38 · Scarab Beetle Title Leaf", p02),
            ("04:06 · Fig. 6 Tree on Signature", p03),
            ("05:14 · Fig. 10 'Jellyfish' Net", p04),
            ("05:54 · Fig. 11 Host & Front-End", p05),
            ("09:28 · Dr. Helen & Fig. 28 PDP-11", p06),
        ]
        make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen22.jpg", cols=3, tile_w=420, tile_h=560)

        # 2) Two Vintage 1974 DEC Schematic Vector SVGs + 72-Col 2x4 Braille Broadsides!
        # SVG #1: Figure 11 · Host and Front-End Processors (DEC 1974 · p. 3-4)
        w5, h5 = im05.size
        arr5 = np.asarray(im05, dtype=np.uint8)
        p5_col = tuple(int(v) for v in np.median(arr5[int(h5 * 0.56):int(h5 * 0.68), int(w5 * 0.14):int(w5 * 0.34)].reshape(-1, 3), axis=0))
        poly5 = [
            (int(w5 * 0.105), int(h5 * 0.195)),
            (int(w5 * 0.855), int(h5 * 0.238)),
            (int(w5 * 0.922), int(h5 * 0.420)),
            (int(w5 * 0.916), int(h5 * 0.552)),
            (int(w5 * 0.785), int(h5 * 0.575)),
            (int(w5 * 0.760), int(h5 * 0.910)),
            (int(w5 * 0.105), int(h5 * 0.875)),
        ]
        m5 = Image.new("L", (w5, h5), 0)
        ImageDraw.Draw(m5).polygon(poly5, fill=255)
        c5 = Image.new("RGB", (w5, h5), p5_col)
        c5.paste(im05, (0, 0), m5)
        rot5 = c5.rotate(9.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p5_col)
        m5_rot = m5.rotate(9.5, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m5_rot.getbbox()
        pad = 24
        rw5, rh5 = rot5.size
        fig11_src = tmp_p / "fig11_clean.png"
        rot5.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw5, bx1 + pad), min(rh5, by1 + pad))).save(fig11_src)

        build_svg_and_braille(
            fig11_src,
            assets_dir,
            "dec1974_fig11_host_frontend",
            title='DEC 1974 · FIGURE 11: HOST & FRONT-END PROCESSORS ("ZOE")',
            subtitle="Edward V. Stelmach, Introduction to Minicomputer Networks (p. 3-4 · Specimen #22)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=26.0,
            paper_cutoff=0.935,
            ink_floor=0.35,
            gamma=1.18,
            levels=(0.11, 0.30, 1.2),
            braille_cols=72,
        )

        # SVG #2: Figure 6 · Hierarchical or Tree Structure (DEC 1974 · p. 2-7)
        w3, h3 = im03.size
        arr3 = np.asarray(im03, dtype=np.uint8)
        p3_col = tuple(int(v) for v in np.median(arr3[int(h3 * 0.15):int(h3 * 0.25), int(w3 * 0.68):int(w3 * 0.84)].reshape(-1, 3), axis=0))
        poly3 = [
            (int(w3 * 0.215), int(h3 * 0.100)),
            (int(w3 * 0.865), int(h3 * 0.105)),
            (int(w3 * 0.848), int(h3 * 0.835)),
            (int(w3 * 0.062), int(h3 * 0.822)),
            (int(w3 * 0.062), int(h3 * 0.228)),
            (int(w3 * 0.210), int(h3 * 0.225)),
        ]
        m3 = Image.new("L", (w3, h3), 0)
        ImageDraw.Draw(m3).polygon(poly3, fill=255)
        c3 = Image.new("RGB", (w3, h3), p3_col)
        c3.paste(im03, (0, 0), m3)
        rot3 = c3.rotate(1.5, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=p3_col)
        m3_rot = m3.rotate(1.5, resample=Image.Resampling.NEAREST, expand=True, fillcolor=0)
        bx0, by0, bx1, by1 = m3_rot.getbbox()
        rw3, rh3 = rot3.size
        fig6_src = tmp_p / "fig6_clean.png"
        rot3.crop((max(0, bx0 - pad), max(0, by0 - pad), min(rw3, bx1 + pad), min(rh3, by1 + pad))).save(fig6_src)

        build_svg_and_braille(
            fig6_src,
            assets_dir,
            "dec1974_fig6_hierarchical_tree",
            title="DEC 1974 · FIGURE 6: HIERARCHICAL OR TREE STRUCTURE",
            subtitle="Edward V. Stelmach, Introduction to Minicomputer Networks (p. 2-7 · Specimen #22)",
            crop_box=(0.01, 0.01, 0.99, 0.99),
            sigma=42.0,
            paper_cutoff=0.90,
            ink_floor=0.35,
            gamma=1.18,
            levels=(0.14, 0.36, 1.2),
            braille_cols=72,
        )

        # 3) Fast keyframe-decoded 12x silent portrait-native 1280x720 Kloster A_tau(p_t) telemetry reel (~53s)
        fps = 15
        target_frames = 795  # 53.0s out for 641.81s real (~12.11x)
        vw, vh = 406, 720
        real_dur = 641.81
        time_scale = real_dur / (target_frames / float(fps))

        print(f"Decoding keyframes from 10m 42s 4K portrait -> {target_frames} frames ({time_scale:.2f}x)...")
        raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-skip_frame", "nokey",
            "-i", str(SRC22),
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

        tl_mp4 = tmp_p / "network_poetry_tl.mp4"
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
            raise RuntimeError("Specimen #22 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 145:
                return "DEC 1974 · CH. 1–2", (94, 218, 238)
            if rsec < 230:
                return "SCARAB BEETLE POEMS", (242, 196, 92)
            if rsec < 335:
                return "JELLYFISH TOPOLOGY", (244, 106, 126)
            if rsec < 445:
                return "FIG 11 · HOST = ZOE", (195, 162, 255)
            if rsec < 530:
                return "RED COVER & SWITCH", (168, 226, 142)
            return "DR. HELEN · PDP-11", (242, 196, 92)

        out_mp4 = video_dir / "specimen22_network_poetry_overlay.mp4"
        poster_png = video_dir / "specimen22_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title='SPECIMEN #22 · "NETWORK POETRY" (DEC 1974 × THE BEETLE)',
            header_sub="Minicomputer Networks + Endless Poems + Dr. Helen Flip (12x Telemetry Reel)",
            phase_fn=phase_fn,
            nexus_band=(340.0, 380.0, 'NEXUS · "HOST PROCESSOR: ZOE"'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=354.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~107 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 354.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen22_network_poetry",
        title='SPECIMEN #22 · "NETWORK POETRY" (DEC 1974 × SCARAB BEETLE)',
        subtitle='10m 42s DEC Minicomputer Networks, "Computers Are Jellyfish" & Host Processor Zoe',
        nexus_label="FIG 11 HOST=ZOE (5:54)",
        footer_label='Fieldglass Specimen #22 · "Network Poetry" (DEC 1974) Telemetry',
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp22",
    )

    summary = {
        "specimen22": {
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
    build_specimen22()
