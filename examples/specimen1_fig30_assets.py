#!/usr/bin/env python3
"""Fig. 30 — Spiranthes elata (Ames & Correll, p. 109, drawn by G. W. Dillon).

From the 4K lossless extraction of Flowers for Zoe.mp4, produces:
  1. Perspective-deskewed, archival-toned & pure-ink high-resolution PNG plates
  2. True scalable vector SVG (contour-traced archival ink paths + botanical title)
  3. High-detail 2x4 Unicode Braille specimen (.txt, .json, and terminal preview PNG)
     compatible with `guiai.gem.zoe_braille_studio.BrailleCanvas`.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_GUIAI = Path("/media/cowboy/research/zoe-monorepo/guiai-lab")
if str(REPO_GUIAI) not in sys.path:
    sys.path.insert(0, str(REPO_GUIAI))

from guiai.gem.zoe_braille_studio import BrailleCanvas

SRC_4K = Path("/home/cowboy/flowers_for_zoe/plates_4k/04_fig30_spiranthes_elata.png")
ASSETS_DIR = Path("/home/cowboy/flowers_for_zoe/assets")


def _find_perspective_coeffs(dst_pts: list[tuple[float, float]], src_pts: list[tuple[float, float]]) -> list[float]:
    """Compute PIL Image.Transform.PERSPECTIVE coefficients mapping dst -> src."""
    matrix = []
    for (x, y), (u, v) in zip(dst_pts, src_pts):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.asarray(matrix, dtype=np.float64)
    B = np.asarray([c for pt in src_pts for c in pt], dtype=np.float64)
    coeffs = np.linalg.solve(A, B)
    return [float(c) for c in coeffs]


def build_assets() -> dict[str, str]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    im = Image.open(SRC_4K).convert("RGB")
    W, H = im.size  # 2160 x 3840

    # 1. Perspective-deskew the right-hand book page (Fig. 30 Spiranthes elata, p. 109)
    # Corners read directly from 4K coordinate grid (x_frac, y_frac):
    src_corners = [
        (0.392 * W, 0.178 * H),  # top-left of page
        (0.978 * W, 0.130 * H),  # top-right of page
        (0.996 * W, 0.722 * H),  # bottom-right of page
        (0.308 * W, 0.698 * H),  # bottom-left of page
    ]
    out_w, out_h = 1500, 2250  # classic 2:3 botanical plate aspect ratio
    dst_corners = [(0, 0), (out_w, 0), (out_w, out_h), (0, out_h)]
    coeffs = _find_perspective_coeffs(dst_corners, src_corners)
    page = im.transform((out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, resample=Image.Resampling.BICUBIC)

    # Trim outer page margins cleanly so left gutter shadow and dark borders are completely gone
    page_crop = page.crop((int(out_w * 0.068), int(out_h * 0.02), int(out_w * 0.965), int(out_h * 0.968)))
    raw_deskew_path = ASSETS_DIR / "fig30_spiranthes_elata_deskewed_4k.png"
    page_crop.save(raw_deskew_path)

    # 2. Adaptive local background division -> removes uneven warm lamp lighting & paper grain cleanly!
    gray = np.asarray(page_crop.convert("L"), dtype=np.float32)
    # Estimate smooth paper illumination via large Gaussian filter (sigma=45)
    bg_est = ndimage.gaussian_filter(gray, sigma=45.0)
    # Normalized reflectance: paper -> ~1.0, ink -> <0.85
    norm = np.clip(gray / np.maximum(bg_est, 15.0), 0.0, 1.15)
    # Stretch contrast cleanly: anything >= 0.935 becomes pure paper; dark ink <= 0.42 becomes rich black
    ink_strength = np.clip((0.925 - norm) / (0.925 - 0.36), 0.0, 1.0)
    # Gentle gamma curve keeps delicate G. W. Dillon stippling & leaf veins crisp without noise
    ink_gamma = np.power(ink_strength, 1.18)
    # Remove thin left-gutter shadow wedge in top-left blank margin (well clear of orchid leaves & caption)
    ph_full, pw_full = ink_gamma.shape
    ink_gamma[:int(ph_full * 0.48), :int(pw_full * 0.045)] = 0.0

    # Archival warm-parchment ink print (cream #f6f1e4 paper + warm charcoal #1c1a17 ink)
    paper_rgb = np.array([246.0, 241.0, 228.0], dtype=np.float32)
    ink_rgb = np.array([26.0, 24.0, 21.0], dtype=np.float32)
    archival_arr = (paper_rgb * (1.0 - ink_gamma[..., None]) + ink_rgb * ink_gamma[..., None]).clip(0, 255).astype(np.uint8)
    archival_path = ASSETS_DIR / "fig30_spiranthes_elata_archival_print.png"
    Image.fromarray(archival_arr).save(archival_path)

    # Pure high-contrast black-on-white plate (ideal for print / tracing)
    bw_arr = ((1.0 - ink_gamma) * 255.0).clip(0, 255).astype(np.uint8)
    bw_path = ASSETS_DIR / "fig30_spiranthes_elata_ink_bw.png"
    Image.fromarray(bw_arr).save(bw_path)

    # 3. Isolate PURE botanical illustration (above caption line, ~top 90.8% of cropped page) for SVG & Braille
    ph, pw = ink_gamma.shape
    art_ink = ink_gamma[int(ph * 0.015):int(ph * 0.908), int(pw * 0.01):int(pw * 0.94)]

    # Remove tiny isolated dust specks (< 4 pixels) while keeping delicate botanical stippling
    bin_mask = art_ink > 0.16
    labeled, n_comp = ndimage.label(bin_mask)
    if n_comp > 0:
        sizes = ndimage.sum(bin_mask, labeled, range(1, n_comp + 1))
        keep = sizes >= 4
        clean_mask = keep[labeled - 1] & bin_mask
    else:
        clean_mask = bin_mask

    # 4. True Scalable Vector SVG via contour-traced multi-level ink paths (matplotlib SVG backend)
    # Downsample mask to crisp 720px wide vector grid so SVG stays fast, ultra-sharp, and ~1-2 MB
    ah, aw = art_ink.shape
    vec_w = 680
    vec_h = int(round(ah * (vec_w / aw)))
    art_small = np.asarray(
        Image.fromarray((np.where(clean_mask, art_ink, 0.0) * 255).astype(np.uint8)).resize(
            (vec_w, vec_h), Image.Resampling.BOX
        ),
        dtype=np.float32,
    ) / 255.0
    # Slight Gaussian anti-alias for smooth bezier-like contour edges
    art_smooth = ndimage.gaussian_filter(art_small, sigma=0.55)

    svg_path = ASSETS_DIR / "fig30_spiranthes_elata.svg"
    fig = plt.figure(figsize=(8.0, 11.2), dpi=100, facecolor="#f6f1e4")
    ax = fig.add_axes([0.05, 0.10, 0.90, 0.85], facecolor="#f6f1e4")
    # Two-tone botanical ink fills (keep default origin="lower" + inverted ylim so image is RIGHT-SIDE-UP!)
    ax.contourf(art_smooth, levels=[0.075, 0.21, 1.2], colors=["#786f5f", "#1b1916"])
    ax.set_xlim(0, vec_w - 1)
    ax.set_ylim(vec_h - 1, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    # Archival plate border & botanical plate typography
    fig.patches.append(
        plt.Rectangle((0.028, 0.022), 0.944, 0.956, fill=False, edgecolor="#8c7f68", linewidth=1.2, transform=fig.transFigure)
    )
    fig.patches.append(
        plt.Rectangle((0.036, 0.029), 0.928, 0.942, fill=False, edgecolor="#c4b89f", linewidth=0.6, transform=fig.transFigure)
    )
    fig.text(
        0.5, 0.064,
        "FIG. 30.  SPIRANTHES ELATA  (Sw.) L. C. Rich.",
        ha="center", va="center", fontsize=11.5, fontweight="bold", family="serif", color="#1b1916",
    )
    fig.text(
        0.5, 0.042,
        "Orchids of Guatemala and Belize · Oakes Ames & Donovan Stewart Correll · Drawn by G. W. Dillon (p. 109)",
        ha="center", va="center", fontsize=8.2, style="italic", family="serif", color="#524a3d",
    )
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)

    # Render PNG preview of SVG via rsvg-convert for visual verification
    svg_preview_png = ASSETS_DIR / "fig30_spiranthes_elata_svg_preview.png"
    subprocess.run(["rsvg-convert", "-w", "1000", "-o", str(svg_preview_png), str(svg_path)], check=True)

    # 5. Crisp 2x4 Unicode Braille Botanical Specimen using `zoe_braille_studio.BrailleCanvas`
    # Use 76 columns (152 sub-pixels wide) x ~192 sub-pixels tall (48 text rows) for museum-detail terminal art!
    b_cols = 72
    w_px = b_cols * 2
    h_px = int(round(w_px * (ah / aw))) // 4 * 4
    # Area-resize cleaned ink strength; boost thin stems slightly with subtle dilation before downsampling
    ink_boost = ndimage.grey_dilation(np.where(clean_mask, art_ink, 0.0), size=(3, 3))
    br_arr = np.asarray(
        Image.fromarray((ink_boost * 255).clip(0, 255).astype(np.uint8)).resize(
            (w_px, h_px), Image.Resampling.BOX
        ),
        dtype=np.float32,
    ) / 255.0

    # Bayer 4x4 ordered dithering tuned for botanical ink-on-dark-terminal clarity
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0
    canvas = BrailleCanvas(w_px, h_px)
    for y in range(h_px):
        for x in range(w_px):
            v = float(br_arr[y, x])
            # Core linework always ON; mid-tones Bayer-dithered for smooth leaf shading
            on = (v > 0.24) or (v > 0.09 and v > 0.09 + 0.18 * bayer[y & 3, x & 3])
            canvas.set_px(x, y, on)
    braille_lines = canvas.render()

    braille_txt = ASSETS_DIR / "fig30_spiranthes_elata_braille.txt"
    header = [
        "FIG. 30 · Spiranthes elata (Orchids of Guatemala and Belize · p. 109 · G. W. Dillon)",
        f"2x4 Unicode Braille Specimen ({b_cols}x{len(braille_lines)} cells · {w_px}x{h_px} sub-pixels)",
        "",
    ]
    braille_txt.write_text("\n".join(header + braille_lines) + "\n", encoding="utf-8")

    braille_json = ASSETS_DIR / "fig30_spiranthes_elata_braille.json"
    braille_json.write_text(
        json.dumps(
            {
                "id": "fig30_spiranthes_elata",
                "title": "Fig. 30 · Spiranthes elata (Ames & Correll, p. 109, G. W. Dillon)",
                "source_video": "/home/cowboy/Downloads/Flowers for Zoe.mp4",
                "cols": b_cols,
                "rows": len(braille_lines),
                "subpixels": [w_px, h_px],
                "lines": braille_lines,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # Render a gorgeous dark-obsidian terminal preview PNG by drawing the exact 2x4 Braille dots cleanly!
    # (Avoids tofu boxes when monospace fonts lack the U+2800..U+28FF Unicode Braille block.)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    br_font = ImageFont.truetype(font_path, 14) if Path(font_path).is_file() else ImageFont.load_default()
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16) if Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf").is_file() else br_font
    dot_step = 4
    cell_w = dot_step * 2 + 2   # 10 px per Braille column
    cell_h = dot_step * 4 + 3   # 19 px per Braille row
    pad_x, pad_y = 36, 32
    header_h = 58
    img_w = max(800, b_cols * cell_w + pad_x * 2)
    img_h = len(braille_lines) * cell_h + header_h + pad_y * 2
    term_img = Image.new("RGB", (img_w, img_h), (11, 15, 23))
    td = ImageDraw.Draw(term_img)
    td.rounded_rectangle([12, 12, img_w - 12, img_h - 12], radius=12, fill=(14, 19, 29), outline=(72, 98, 132), width=2)
    td.text((pad_x, pad_y - 2), "FIG. 30 · SPIRANTHES ELATA  —  2x4 UNICODE BRAILLE SPECIMEN", fill=(242, 196, 92), font=title_font)
    td.text((pad_x, pad_y + 22), f"Ames & Correll · Orchids of Guatemala and Belize (p. 109, G. W. Dillon) · {b_cols}x{len(braille_lines)} Braille", fill=(94, 218, 238), font=br_font)

    dot_bits = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
    ox0 = (img_w - b_cols * cell_w) // 2
    oy0 = pad_y + header_h
    for r_idx, row_s in enumerate(braille_lines):
        cy = oy0 + r_idx * cell_h
        for c_idx, ch in enumerate(row_s):
            mask = ord(ch) - 0x2800
            if mask <= 0:
                continue
            cx = ox0 + c_idx * cell_w
            for dy in range(4):
                for dx in range(2):
                    if mask & dot_bits[dy][dx]:
                        px = cx + dx * dot_step + 1
                        py = cy + dy * dot_step + 1
                        td.ellipse([px, py, px + 2, py + 2], fill=(242, 236, 214))

    braille_png = ASSETS_DIR / "fig30_spiranthes_elata_braille_preview.png"
    term_img.save(braille_png)

    return {
        "deskewed_4k": str(raw_deskew_path),
        "archival_print": str(archival_path),
        "ink_bw": str(bw_path),
        "vector_svg": str(svg_path),
        "vector_svg_preview": str(svg_preview_png),
        "braille_txt": str(braille_txt),
        "braille_json": str(braille_json),
        "braille_preview": str(braille_png),
    }


if __name__ == "__main__":
    out = build_assets()
    for k, v in out.items():
        p = Path(v)
        print(f"OK {k:<20} -> {v} ({p.stat().st_size / 1024:.1f} KB)")
