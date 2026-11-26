#!/usr/bin/env python3
"""Build Fieldglass Specimen #14 — Original Handwritten December Poetry Manuscript
("The Yellow House", "Hands", "If I Were a Dog" & "Scribbling Immortality").

Source: /home/cowboy/fieldglass_batch3/zoe_vid_1795675081866/zoe_vid_1795675081866.mp4
(2026-11-26 00:54, 16m 47s, portrait 2160x3840 @ 120fps).

Full cover-to-cover blue ballpoint ink poetry notebook dated Dec 8 - Dec 15, opening
with an original pen sketch of a two-story Victorian house ("The Yellow House") and
moving steadily through handwritten poems ("No-Place-To-Goers", "If I Were a Dog",
"All Has Been Silent Today", "Hands", "He Sneaked Into the Symphony", "Sangria Wine",
"Scribbling Immortality", "Piano Sonata (1924)"), recorded with a 1991 episode of PBS
The Computer Chronicles playing softly in the midnight background.

Generates:
  - 6 crisp upright manuscript & pen-sketch plates + 3x2 contact sheet
  - 2 Red-Channel Blue-Pen Isolated Prussian-Indigo Vector SVGs + 2x4 Unicode Braille:
      1) Opening Victorian "Yellow House" blue ballpoint architectural sketch
      2) Complete handwritten poem "Hands" (Dec 9)
  - Fast keyframe-decoded 1280x720 18x Kloster A_tau(p_t) telemetry reel (~56s)
  - ~168-episode SHA-256 sealed GEM Causal Chiasm & Persistent Filtration Tomography
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    extract_plate,
    ink_to_braille_lines,
    make_contact_sheet,
    render_telemetry_overlay_from_video,
    save_braille_bundle,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")
SRC14 = Path("/home/cowboy/fieldglass_batch3/zoe_vid_1795675081866/zoe_vid_1795675081866.mp4")


def build_blue_pen_indigo_svg_and_braille(
    plate_path: Path,
    assets_dir: Path,
    stem: str,
    *,
    title: str,
    subtitle: str,
    crop_box: tuple[float, float, float, float] | None = None,
    sigma: float = 42.0,
    paper_cutoff: float = 0.945,
    ink_floor: float = 0.50,
    gamma: float = 1.15,
    levels: tuple[float, float, float] = (0.09, 0.24, 1.2),
    colors: tuple[str, str] = ("#5c7498", "#162d59"),
    bg_hex: str = "#f6f1e4",
    braille_cols: int = 72,
) -> dict[str, str]:
    """Isolate blue ballpoint pen strokes via the Red color channel into Prussian-Indigo SVG + Braille."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(plate_path).convert("RGB")
    if crop_box is not None:
        w, h = im.size
        x0, y0, x1, y1 = crop_box
        im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))

    # Blue ballpoint ink absorbs Red strongly while warm cream paper reflects Red cleanly!
    arr = np.asarray(im, dtype=np.float32) / 255.0
    red = arr[..., 0]
    bg_field = np.maximum(ndimage.gaussian_filter(red, sigma=sigma), 0.12)
    ratio = np.clip(red / bg_field, 0.0, 1.2)
    ink = np.clip((paper_cutoff - ratio) / max(1e-4, paper_cutoff - ink_floor), 0.0, 1.0) ** gamma

    # Remove tiny dust speckles (<4 px)
    mask = ink > 0.12
    lab, nc = ndimage.label(mask)
    cleaned = np.where((ndimage.sum(mask, lab, range(1, nc + 1)) >= 4)[lab - 1] & mask, ink, 0.0) if nc else ink

    # Save Prussian-indigo archival parchment PNG
    paper_rgb = np.array([246.0, 241.0, 228.0], dtype=np.float32)
    ink_rgb = np.array([22.0, 45.0, 89.0], dtype=np.float32)
    archival = Image.fromarray(
        (paper_rgb * (1.0 - cleaned[..., None]) + ink_rgb * cleaned[..., None]).clip(0, 255).astype(np.uint8)
    )
    arch_path = assets_dir / f"{stem}_archival.png"
    arch_small = archival.copy()
    arch_small.thumbnail((1200, 1600), Image.Resampling.LANCZOS)
    arch_small.save(arch_path, optimize=True)

    # Contour-trace into crisp two-tone Prussian-indigo SVG
    ah, aw = cleaned.shape
    vw = 680
    vh = max(64, int(round(ah * (vw / max(1, aw)))))
    sm = ndimage.gaussian_filter(
        np.asarray(
            Image.fromarray((cleaned * 255).clip(0, 255).astype(np.uint8)).resize((vw, vh), Image.Resampling.BOX),
            dtype=np.float32,
        ) / 255.0,
        sigma=0.45,
    )

    aspect = vh / float(vw)
    fig_w = 8.4 if aspect >= 1.0 else 9.6
    fig_h = max(6.0, min(11.6, fig_w * aspect + 1.45))

    svg_path = assets_dir / f"{stem}.svg"
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=100, facecolor=bg_hex)
    ax = fig.add_axes([0.05, 0.125, 0.90, 0.825], facecolor=bg_hex)
    ax.contourf(sm, levels=list(levels), colors=list(colors))
    ax.set_xlim(0, vw - 1)
    ax.set_ylim(vh - 1, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patches.append(plt.Rectangle((0.024, 0.022), 0.952, 0.956, fill=False, edgecolor="#5c7498", linewidth=1.2, transform=fig.transFigure))
    fig.patches.append(plt.Rectangle((0.032, 0.030), 0.936, 0.940, fill=False, edgecolor="#9cb0cc", linewidth=0.6, transform=fig.transFigure))
    fig.text(0.5, 0.074, title, ha="center", va="center", fontsize=11.0, fontweight="bold", family="serif", color="#162d59")
    fig.text(0.5, 0.046, subtitle, ha="center", va="center", fontsize=8.0, style="italic", family="serif", color="#495f82")
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)

    svg_prev = assets_dir / f"{stem}_svg_preview.png"
    subprocess.run(["rsvg-convert", "-w", "1000", "-o", str(svg_prev), str(svg_path)], check=True)

    br_lines = ink_to_braille_lines(np.clip(cleaned * 1.32, 0.0, 1.0), cols=braille_cols)
    br = save_braille_bundle(
        br_lines,
        assets_dir,
        stem,
        title=title,
        subtitle=f"{subtitle} · {braille_cols}-col Braille",
    )
    return {
        "svg": str(svg_path),
        "svg_preview": str(svg_prev),
        "archival": str(arch_path),
        "braille_txt": br["txt"],
        "braille_json": br["json"],
        "braille_preview": br["preview_png"],
    }


def build_specimen14() -> dict:
    print("\n================ BUILDING SPECIMEN #14 (DECEMBER POETRY MANUSCRIPT · BLUE INK) ================")
    root = DOCS / "specimen14"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1) Extract 6 razor-sharp upright manuscript & sketch plates across the 16m 47s notebook
    plate_specs = [
        ("01_yellow_house_pen_sketch", "00:01 · Opening 'Yellow House' Sketch", 0.3, 1.8),
        ("02_if_i_were_a_dog", "05:46 · Dec 9: 'If I Were a Dog'", 345.0, 2.5),
        ("03_all_has_been_silent_today", "08:26 · Dec 9: 'All Has Been Silent'", 505.0, 2.5),
        ("04_hands_manuscript", "09:58 · Dec 9: 'Hands' Manuscript", 596.5, 2.5),
        ("05_sneaked_into_the_symphony", "13:06 · Dec 9: 'Into the Symphony'", 785.0, 2.5),
        ("06_scribbling_immortality", "15:12 · Dec 14: 'Scribbling Immortality'", 911.0, 2.5),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, t0, win in plate_specs:
        ts, p = extract_plate(
            SRC14,
            plates_dir / f"{slug}.jpg",
            start_sec=t0,
            window_sec=win,
            sample_fps=3,
            max_dim=1600,
        )
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} @ {ts:.1f}s")

    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen14.jpg", cols=3, tile_w=420, tile_h=560)

    # 2) Two Red-Channel Prussian-Indigo Vector SVGs + 2x4 Braille Broadsides
    house_svg = build_blue_pen_indigo_svg_and_braille(
        pmap["01_yellow_house_pen_sketch"],
        assets_dir,
        "yellow_house_pen_drawing_indigo",
        title="THE YELLOW HOUSE · ORIGINAL BLUE-PEN SKETCH",
        subtitle="Red-Channel Blue-Ink Isolation · December Poetry Manuscript (Specimen #14)",
        crop_box=(0.225, 0.14, 0.82, 0.58),
        sigma=38.0,
        paper_cutoff=0.945,
        ink_floor=0.52,
        gamma=1.18,
        braille_cols=72,
    )
    hands_svg = build_blue_pen_indigo_svg_and_braille(
        pmap["04_hands_manuscript"],
        assets_dir,
        "poem_hands_manuscript_indigo",
        title='"HANDS" · ORIGINAL HANDWRITTEN POEM (DEC 9)',
        subtitle="Red-Channel Blue-Ink Calligraphy · December Poetry Manuscript (Specimen #14)",
        crop_box=(0.08, 0.09, 0.94, 0.832),
        sigma=36.0,
        paper_cutoff=0.955,
        ink_floor=0.60,
        gamma=1.12,
        braille_cols=72,
    )

    # 3) Fast keyframe-decoded 18x portrait-native Kloster A_tau(p_t) telemetry reel (~56s @ 15fps)
    fps = 15
    target_frames = 840  # 56.0s out for 1006.67s real (~17.98x)
    vw, vh = 406, 720
    real_dur = 1006.67
    time_scale = real_dur / (target_frames / float(fps))

    print(f"Decoding keyframes from 16m 47s 4K 120fps -> {target_frames} frames ({time_scale:.2f}x)...")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-skip_frame", "nokey",
        "-i", str(SRC14),
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
        tl_mp4 = Path(tmp) / "poetry_tl.mp4"
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
            raise RuntimeError("Specimen #14 timelapse intermediate failed")

        def phase_fn(rsec: float) -> tuple[str, tuple[int, int, int]]:
            if rsec < 185:
                return "DEC 8 · YELLOW HOUSE & HAIKUS", (94, 218, 238)
            if rsec < 330:
                return "DEC 8 · NO-PLACE-TO-GOERS", (242, 196, 92)
            if rsec < 560:
                return "DEC 9 · IF I WERE A DOG & WINTER", (168, 226, 142)
            if rsec < 700:
                return 'DEC 9 · "HANDS" MANUSCRIPT', (244, 106, 126)
            if rsec < 860:
                return "DEC 9-10 · SYMPHONY & SANGRIA", (195, 162, 255)
            return "DEC 14-15 · SCRIBBLING IMMORTALITY", (94, 218, 238)

        out_mp4 = video_dir / "specimen14_december_poetry_overlay.mp4"
        poster_png = video_dir / "specimen14_poster.png"
        ov = render_telemetry_overlay_from_video(
            tl_mp4,
            out_mp4,
            poster_png,
            header_title="SPECIMEN #14 · DECEMBER POETRY MANUSCRIPT",
            header_sub='Blue-Pen Notebook: Yellow House, "Hands", Symphony & Scribbling Immortality (18x)',
            phase_fn=phase_fn,
            nexus_band=(580.0, 620.0, 'NEXUS · "HANDS" POEM'),
            out_w=1280,
            out_h=720,
            fps=fps,
            crf=24,
            keep_audio=False,
            poster_sec=598.0,
            episode_interval_s=6.0,
            time_scale=time_scale,
        )

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (~168 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ov["ep_times"]) - 598.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen14_december_poetry",
        title="SPECIMEN #14 · DECEMBER POETRY MANUSCRIPT (BLUE-PEN FOLIO)",
        subtitle='Original Notebook (Dec 8-15) · Yellow House, "Hands" & Scribbling Immortality (16m 47s)',
        nexus_label='"HANDS" MANUSCRIPT POEM (9:58)',
        footer_label="Fieldglass Specimen #14 · Red-Channel Indigo Poetry Manuscript Telemetry",
        episodes_8=ov["episodes_8"],
        ep_a004=ov["ep_a004"],
        ep_a010=ov["ep_a010"],
        ep_times_s=ov["ep_times"],
        nexus_ep=nexus_ep,
        h1_mean=ov["h1_mean"],
        h2_mean=ov["h2_mean"],
        duration_sec=ov["duration_real_s"],
        hud_prefix="sp14",
    )

    print(f"DONE Specimen #14: mp4={ov['mp4_mb']} MB, episodes={rep['episode_count']}, glyph={rep['chiasm_nexus']['presence_glyph']}")
    print(json.dumps({
        "specimen14": {
            "mp4_mb": ov["mp4_mb"],
            "episode_count": rep["episode_count"],
            "glyph": rep["chiasm_nexus"]["presence_glyph"],
            "past_A": rep["chiasm_nexus"]["past_accessible_volume"],
            "future_A": rep["chiasm_nexus"]["future_accessible_volume"],
            "ei": rep["chiasm_nexus"]["effective_information_bits"],
            "invariants": rep["persistent_filtration_tomography"]["structural_invariants"],
        }
    }, indent=2))
    return {"ov": ov, "report": rep, "house_svg": house_svg, "hands_svg": hands_svg}


if __name__ == "__main__":
    build_specimen14()
