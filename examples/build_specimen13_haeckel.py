#!/usr/bin/env python3
"""Build Fieldglass Specimen #13 — Ernst Haeckel: Kunstformen der Natur
(Art Forms in Nature · Copper-Plate Ecology & Radiolarian Geometry).

Source: /home/cowboy/fieldglass_ics/zoe_vid_1795668015763/zoe_vid_1795668015763.mp4
(22:58, 17m 54s, portrait 2160x3840 @ 120fps, Nick & Dr. Helen Ruth Horkan).

Dr. Helen Ruth Horkan's Linda Hall Library selection — Ernst Haeckel's folio plates
(Radiolaria, Phaeodaria, Siphonophora, Echinoidea, Gorgonida, Narcomedusae,
Nepenthaceae, Ctenophora) paired with her studio commentary on Haeckel's invention
of ecology, Cnidarian planktonic embryogenesis, and 19th-century multi-plate copper
engraving.

Generates:
  - 6 crisp upright Haeckel folio plates + 3x2 contact sheet
  - 2 publication-grade Vector SVGs + 2x4 Unicode Braille bundles:
      1) Tafel 1 · Phaeodaria (Rohrstrahlinge) starburst radiolarian plate
      2) Hexagonal & Pentagonal Radiolarian Honeycomb Tessellation
  - Fast keyframe-decoded 1280x720 18x Kloster A_tau(p_t) telemetry reel (~58s)
  - Complete 17m 54s studio audio companion MP3 (4.1 MB)
  - 180-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
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
SRC13 = Path("/home/cowboy/fieldglass_ics/zoe_vid_1795668015763/zoe_vid_1795668015763.mp4")
AUD13 = Path("/home/cowboy/fieldglass_ics/zoe_vid_1795668015763/audio.mp3")


def build_specimen13() -> dict:
    print("\n================ BUILDING SPECIMEN #13 (ERNST HAECKEL · KUNSTFORMEN DER NATUR) ================")
    root = DOCS / "specimen13"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    audio_dir = root / "audio"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir, audio_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Copy complete 17m 54s studio audio companion (4.1 MB)
    out_audio = audio_dir / "specimen13_haeckel_studio_dialogue.mp3"
    shutil.copy2(AUD13, out_audio)
    print(f"  Copied audio companion: {out_audio.stat().st_size / 1e6:.2f} MB")

    # 1) Extract 6 razor-sharp upright Ernst Haeckel plates across the 17m 54s folio flip
    plate_specs = [
        # (slug, label, start_sec, window_sec, rotate_ccw, crop_box)
        ("01_hexagonal_diatom_tessellation", "03:52 · Hexagonal Honeycomb Lattice", 231.5, 2.0, 0, None),
        ("02_phaeodaria_rohrstrahlinge", "07:14 · Tafel 1: Phaeodaria Starburst", 433.5, 2.0, 0, None),
        ("03_cyrtoidea_echinoidea_spread", "10:38 · Cyrtoidea & Echinoidea", 637.4, 1.5, 270, None),
        ("04_gorgonida_narcomedusae", "12:50 · Gorgonida & Narcomedusae", 769.5, 2.0, 270, None),
        ("05_nepenthaceae_pitcher_plants", "13:58 · Nepenthaceae & Radiolaria", 837.5, 2.0, 270, None),
        ("06_ctenophora_comb_jellies", "15:05 · Ctenophora & Lacertilia", 904.5, 2.0, 270, None),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win, rot, crop in plate_specs:
        ts, p = extract_plate(
            SRC13,
            plates_dir / f"{slug}.jpg",
            start_sec=t0,
            window_sec=win,
            sample_fps=3,
            rotate_ccw=rot,
            crop_box=crop,
            max_dim=1600,
        )
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s (rot={rot})")

    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen13.jpg", cols=3, tile_w=460, tile_h=460)

    # 2) Two museum-grade Vector SVGs + 2x4 Unicode Braille bundles from Haeckel's plates!
    phaeo_svg = build_svg_and_braille(
        pmap["02_phaeodaria_rohrstrahlinge"],
        assets_dir,
        "haeckel_phaeodaria_radiolaria",
        title="TAFEL 1 · PHAEODARIA (ROHRSTRAHLINGE)",
        subtitle="Ernst Haeckel · Kunstformen der Natur (Radiolaria Silica Geometry · Specimen #13)",
        crop_box=(0.04, 0.00, 0.99, 0.93),
        sigma=46.0,
        paper_cutoff=0.955,
        ink_floor=0.45,
        gamma=1.18,
        braille_cols=72,
    )
    hex_svg = build_svg_and_braille(
        pmap["01_hexagonal_diatom_tessellation"],
        assets_dir,
        "haeckel_hexagonal_tessellation",
        title="HEXAGONAL & PENTAGONAL RADIOLARIAN TESSELLATION",
        subtitle="Ernst Haeckel · Natural Honeycomb Geometry (Linda Hall Library Folio)",
        crop_box=(0.00, 0.085, 1.00, 0.675),
        sigma=40.0,
        paper_cutoff=0.95,
        ink_floor=0.46,
        gamma=1.16,
        braille_cols=72,
    )

    # 3) Fast keyframe-decoded 18x portrait-native timelapse intermediate (~58s @ 15fps)
    #    Decodes ~1,074 keyframes in ~14 seconds instead of decoding 129,000 4K 120fps frames!
    fps = 15
    target_frames = 870  # 58.0s out for 1074.26s real (~18.52x)
    vw, vh = 406, 720
    real_dur = 1074.26
    time_scale = real_dur / (target_frames / float(fps))

    print(f"Decoding keyframes from 17m 54s 4K 120fps -> {target_frames} frames ({time_scale:.2f}x)...")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-skip_frame", "nokey",
        "-i", str(SRC13),
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
        tl_mp4 = Path(tmp) / "haeckel_tl.mp4"
        enc = subprocess.Popen([
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{vw}x{vh}", "-r", str(fps), "-i", "-",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", str(tl_mp4),
        ], stdin=subprocess.PIPE)
        assert enc.stdin is not None
        enc.stdin.write(arr.tobytes())
        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError("Haeckel intermediate timelapse encode failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 210:
                return "RED SEA CORALS & BIOGRAPHY", (94, 218, 238)
            if rsec < 405:
                return "HEXAGONAL LATTICES & EMBRYOLOGY", (242, 196, 92)
            if rsec < 550:
                return "TAFEL 1 · PHAEODARIA RADIOLARIA", (244, 106, 126)
            if rsec < 760:
                return "SIPHONOPHORA & CYRTOIDEA PLATES", (195, 162, 255)
            if rsec < 960:
                return "MEDUSAE, PITCHERS & CTENOPHORA", (168, 226, 142)
            return "LIVE FIELDGLASS STUDIO & FOLIO", (94, 218, 238)

        out_mp4 = video_dir / "specimen13_haeckel_kunstformen_overlay.mp4"
        poster_png = video_dir / "specimen13_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title="SPECIMEN #13 · ERNST HAECKEL (KUNSTFORMEN DER NATUR)",
            header_sub="Dr. Helen's Linda Hall Folio · Radiolaria, Medusae & Copper-Plate Ecology (18.5x)",
            phase_fn=phase_fn,
            nexus_band=(420.0, 465.0, "NEXUS · PHAEODARIA PLATE"),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=435.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~179 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 434.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen13_haeckel_kunstformen",
        title="SPECIMEN #13 · ERNST HAECKEL (KUNSTFORMEN DER NATUR)",
        subtitle="Linda Hall Folio · Radiolaria, Siphonophora, Medusae & Ctenophora (17m 54s · 180 Ep.)",
        nexus_label="PHAEODARIA COPPER PLATES (7:14)",
        footer_label="Fieldglass Specimen #13 · Ernst Haeckel Folio & Dr. Helen Ecology Dialogue",
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp13",
    )

    print(f"DONE Specimen #13: mp4={ov['mp4_mb']} MB, episodes={rep['episode_count']}, glyph={rep['chiasm_nexus']['presence_glyph']}")
    print(json.dumps({
        "specimen13": {
            "mp4_mb": ov["mp4_mb"],
            "audio_mb": round(out_audio.stat().st_size / 1e6, 2),
            "episode_count": rep["episode_count"],
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }, indent=2))
    return {"ov": ov, "report": rep, "phaeo_svg": phaeo_svg, "hex_svg": hex_svg}


if __name__ == "__main__":
    build_specimen13()
