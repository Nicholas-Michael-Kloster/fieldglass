"""Plate extraction, perspective deskew, illumination cleaning, SVG tracing, and 2x4 Braille rendering."""

from __future__ import annotations

from collections.abc import Sequence as AbcSequence
import json
import math
import numbers
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

# Standard Unicode Braille (U+2800..U+28FF) bit weights for (row 0..3, col 0..1)
DOT_BITS: tuple[tuple[int, int], ...] = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

BAYER_4X4 = np.array(
    [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
    ],
    dtype=np.float32,
) / 16.0


def laplacian_sharpness(image: Image.Image) -> float:
    """Measure focus sharpness via variance of the discrete 2D Laplacian."""
    gray = image.convert("L")
    w, h = gray.size
    crop = gray.crop((int(w * 0.10), int(h * 0.12), int(w * 0.92), int(h * 0.88)))
    crop.thumbnail((720, 1280))
    arr = np.asarray(crop, dtype=np.float32)
    return float(ndimage.laplace(arr).var())


def extract_sharpest_frame(
    video_path: str | Path,
    out_png: str | Path,
    *,
    start_sec: float = 0.0,
    duration_sec: float = 2.0,
    sample_fps: int = 8,
) -> dict[str, Any]:
    """Scan [start_sec, start_sec + duration_sec] and extract the sharpest frame losslessly via ffmpeg."""
    src = Path(video_path).expanduser().resolve()
    dst = Path(out_png).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        cdir = Path(tmp)
        subprocess.run(
            [
                "ffmpeg", "-v", "error",
                "-ss", f"{start_sec:.3f}", "-t", f"{duration_sec:.3f}",
                "-i", str(src), "-vf", f"fps={sample_fps}", "-q:v", "2",
                str(cdir / "cand_%04d.jpg"),
            ],
            check=True,
        )
        cands = sorted(cdir.glob("cand_*.jpg"))
        if not cands:
            raise RuntimeError(f"No frames extracted from {src} at {start_sec}s+{duration_sec}s")
        scored = []
        for idx, p in enumerate(cands):
            with Image.open(p) as im:
                sc = laplacian_sharpness(im)
            scored.append((sc, start_sec + idx / float(sample_fps), p))
        best_sc, best_ts, _ = max(scored, key=lambda x: x[0])

    subprocess.run(
        [
            "ffmpeg", "-v", "error",
            "-ss", f"{best_ts:.3f}", "-i", str(src),
            "-frames:v", "1", "-y", str(dst),
        ],
        check=True,
    )
    with Image.open(dst) as final_im:
        size = list(final_im.size)
    return {
        "out_png": str(dst),
        "timestamp_sec": round(best_ts, 3),
        "sharpness": round(best_sc, 2),
        "size": size,
        "bytes": dst.stat().st_size,
    }


def _perspective_coeffs(
    dst_pts: Sequence[tuple[float, float]],
    src_pts: Sequence[tuple[float, float]],
) -> list[float]:
    matrix = []
    for (x, y), (u, v) in zip(dst_pts, src_pts):
        matrix.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        matrix.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
    A = np.asarray(matrix, dtype=np.float64)
    B = np.asarray([c for pt in src_pts for c in pt], dtype=np.float64)
    try:
        solved = np.linalg.solve(A, B)
    except np.linalg.LinAlgError as exc:
        raise ValueError("corners_norm must form a non-degenerate quadrilateral") from exc
    if not np.all(np.isfinite(solved)):
        raise ValueError("corners_norm must form a non-degenerate quadrilateral")
    return [float(c) for c in solved]


def _contains_bool(obj: Any) -> bool:
    """Return True if obj is or contains a Python bool or numpy.bool_."""
    if isinstance(obj, (bool, np.bool_)):
        return True
    if isinstance(obj, np.ndarray):
        if obj.dtype == np.bool_:
            return True
        if obj.dtype == object:
            return any(_contains_bool(x) for x in obj.flat)
        return False
    if isinstance(obj, AbcSequence) and not isinstance(obj, (str, bytes, bytearray)):
        return any(_contains_bool(x) for x in obj)
    return False


def _require_finite_coord(val: Any, name: str) -> float:
    if isinstance(val, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite real number, not bool")
    if isinstance(val, np.ndarray):
        cur: Any = val
        seen: set[int] = set()
        while isinstance(cur, np.ndarray):
            obj_id = id(cur)
            if obj_id in seen:
                raise ValueError(f"{name} must be a scalar finite real number")
            seen.add(obj_id)
            if cur.ndim != 0:
                raise ValueError(f"{name} must be a scalar finite real number")
            if cur.dtype == np.bool_:
                raise ValueError(f"{name} must be a finite real number, not bool")
            if cur.dtype == object:
                cur = cur.item()
            else:
                break
        if isinstance(cur, (bool, np.bool_)):
            raise ValueError(f"{name} must be a finite real number, not bool")
    try:
        num = float(val)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(num):
        raise ValueError(f"{name} must be finite")
    return num


def _require_positive_int_dim(val: Any, name: str) -> int:
    if isinstance(val, (bool, np.bool_)):
        raise ValueError(f"{name} must be a positive integer, not bool")
    if isinstance(val, np.ndarray):
        if val.ndim != 0:
            raise ValueError(f"{name} must be a scalar positive integer")
        if val.dtype == np.bool_:
            raise ValueError(f"{name} must be a positive integer, not bool")
        if val.dtype == object:
            cur: Any = val
            seen: set[int] = set()
            while isinstance(cur, np.ndarray):
                obj_id = id(cur)
                if obj_id in seen:
                    raise ValueError(f"{name} must be a scalar positive integer")
                seen.add(obj_id)
                if cur.ndim != 0:
                    raise ValueError(f"{name} must be a scalar positive integer")
                if cur.dtype == np.bool_:
                    raise ValueError(f"{name} must be a positive integer, not bool")
                if cur.dtype == object:
                    cur = cur.item()
                else:
                    break
            if isinstance(cur, (bool, np.bool_)):
                raise ValueError(f"{name} must be a positive integer, not bool")
            raise ValueError(f"{name} must be a positive integer")
        if not np.issubdtype(val.dtype, np.integer):
            raise ValueError(f"{name} must be a positive integer")
        iv = int(val)
    elif isinstance(val, numbers.Integral):
        iv = int(val)
    else:
        raise ValueError(f"{name} must be a positive integer")
    if iv <= 0:
        raise ValueError(f"{name} dimensions must be positive")
    return iv


def perspective_deskew(
    image: Image.Image,
    corners_norm: Sequence[tuple[float, float]],
    *,
    out_size: tuple[int, int] = (1500, 2250),
) -> Image.Image:
    """Warp a 4-corner quadrilateral (normalized 0..1 TL, TR, BR, BL) into a flat rectangular scan."""
    w, h = image.size
    if w <= 0 or h <= 0:
        raise ValueError("image dimensions must be positive")
    if (
        not isinstance(out_size, AbcSequence)
        or isinstance(out_size, (str, bytes, bytearray))
        or len(out_size) != 2
    ):
        raise ValueError("out_size must be a (width, height) pair")
    ow = _require_positive_int_dim(out_size[0], "out_size[0]")
    oh = _require_positive_int_dim(out_size[1], "out_size[1]")
    if len(corners_norm) != 4:
        raise ValueError("corners_norm must contain exactly 4 (x_frac, y_frac) points: TL, TR, BR, BL")
    src_pts: list[tuple[float, float]] = []
    for idx, corner in enumerate(corners_norm):
        if len(corner) != 2:
            raise ValueError(f"corners_norm[{idx}] must be an (x, y) pair")
        cx = _require_finite_coord(corner[0], f"corners_norm[{idx}][0]")
        cy = _require_finite_coord(corner[1], f"corners_norm[{idx}][1]")
        src_pts.append((cx * w, cy * h))
    dst_pts = [(0.0, 0.0), (float(ow), 0.0), (float(ow), float(oh)), (0.0, float(oh))]
    coeffs = _perspective_coeffs(dst_pts, src_pts)
    return image.transform((int(ow), int(oh)), Image.Transform.PERSPECTIVE, coeffs, resample=Image.Resampling.BICUBIC)


def clean_illumination(
    image: Image.Image,
    *,
    sigma: float = 45.0,
    paper_cutoff: float = 0.925,
    ink_floor: float = 0.36,
    gamma: float = 1.18,
) -> tuple[np.ndarray, Image.Image, Image.Image]:
    """Divide grayscale image by smooth Gaussian background to erase lamp shadows & isolate ink.

    Returns (ink_strength_0_to_1, archival_parchment_img, pure_bw_img).
    """
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    bg = ndimage.gaussian_filter(gray, sigma=sigma)
    norm = np.clip(gray / np.maximum(bg, 15.0), 0.0, 1.15)
    ink = np.clip((paper_cutoff - norm) / max(1e-3, paper_cutoff - ink_floor), 0.0, 1.0)
    ink = np.power(ink, gamma)

    paper_rgb = np.array([246.0, 241.0, 228.0], dtype=np.float32)
    ink_rgb = np.array([26.0, 24.0, 21.0], dtype=np.float32)
    archival = (paper_rgb * (1.0 - ink[..., None]) + ink_rgb * ink[..., None]).clip(0, 255).astype(np.uint8)
    bw = ((1.0 - ink) * 255.0).clip(0, 255).astype(np.uint8)
    return ink, Image.fromarray(archival), Image.fromarray(bw)


def _validate_ink_map_2d(ink_map: Any) -> np.ndarray:
    """Validate a non-empty, finite, non-boolean 2D numeric ink map."""
    if _contains_bool(ink_map):
        raise ValueError("ink_map must be a 2D finite numeric array, not bool")
    raw = np.asarray(ink_map)
    if raw.dtype == np.bool_ or (raw.dtype == object and any(_contains_bool(x) for x in raw.flat)):
        raise ValueError("ink_map must be a 2D finite numeric array, not bool")
    try:
        arr = np.asarray(raw, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise ValueError("ink_map must be a 2D finite numeric array") from exc
    if arr.ndim != 2 or arr.size == 0:
        raise ValueError("ink_map must be a non-empty 2D array")
    if not np.all(np.isfinite(arr)):
        raise ValueError("ink_map must contain only finite values")
    return arr


def trace_ink_to_svg(
    ink_map: np.ndarray,
    svg_path: str | Path,
    *,
    title: str = "FIELDGLASS SPECIMEN",
    subtitle: str = "Contour-traced botanical ink vector",
    vec_width: int = 680,
    levels: tuple[float, float, float] = (0.075, 0.21, 1.2),
) -> Path:
    """Trace a cleaned [0..1] ink field into a framed two-tone archival vector SVG."""
    arr = _validate_ink_map_2d(ink_map)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dst = Path(svg_path).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Remove tiny isolated dust specks (< 4 px)
    mask = arr > 0.16
    labeled, n_comp = ndimage.label(mask)
    if n_comp > 0:
        sizes = ndimage.sum(mask, labeled, range(1, n_comp + 1))
        keep = sizes >= 4
        cleaned = np.where(keep[labeled - 1] & mask, arr, 0.0)
    else:
        cleaned = arr

    ah, aw = cleaned.shape
    vec_h = max(16, int(round(ah * (vec_width / max(1, aw)))))
    small = np.asarray(
        Image.fromarray((cleaned * 255.0).clip(0, 255).astype(np.uint8)).resize(
            (vec_width, vec_h), Image.Resampling.BOX
        ),
        dtype=np.float32,
    ) / 255.0
    smooth = ndimage.gaussian_filter(small, sigma=0.55)

    fig = plt.figure(figsize=(8.0, 11.2), dpi=100, facecolor="#f6f1e4")
    ax = fig.add_axes([0.05, 0.10, 0.90, 0.85], facecolor="#f6f1e4")
    # Default origin="lower" + inverted ylim renders right-side-up in SVG coordinates!
    ax.contourf(smooth, levels=list(levels), colors=["#786f5f", "#1b1916"])
    ax.set_xlim(0, vec_width - 1)
    ax.set_ylim(vec_h - 1, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.patches.append(
        plt.Rectangle((0.028, 0.022), 0.944, 0.956, fill=False, edgecolor="#8c7f68", linewidth=1.2, transform=fig.transFigure)
    )
    fig.patches.append(
        plt.Rectangle((0.036, 0.029), 0.928, 0.942, fill=False, edgecolor="#c4b89f", linewidth=0.6, transform=fig.transFigure)
    )
    fig.text(0.5, 0.064, title, ha="center", va="center", fontsize=11.5, fontweight="bold", family="serif", color="#1b1916")
    fig.text(0.5, 0.042, subtitle, ha="center", va="center", fontsize=8.2, style="italic", family="serif", color="#524a3d")
    fig.savefig(dst, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)
    return dst


def ink_to_braille_lines(ink_map: np.ndarray, *, cols: int = 72) -> list[str]:
    """Convert a [0..1] ink strength array into crisp 2x4 Unicode Braille lines (U+2800..U+28FF)."""
    arr = _validate_ink_map_2d(ink_map)
    cols = max(16, min(120, int(cols)))
    ah, aw = arr.shape
    w_px = cols * 2
    h_px = max(8, (int(round(w_px * (ah / max(1, aw)))) // 4) * 4)

    boosted = ndimage.grey_dilation(arr, size=(3, 3))
    small = np.asarray(
        Image.fromarray((boosted * 255.0).clip(0, 255).astype(np.uint8)).resize(
            (w_px, h_px), Image.Resampling.BOX
        ),
        dtype=np.float32,
    ) / 255.0

    rows: list[str] = []
    for cy in range(0, h_px, 4):
        chars: list[str] = []
        for cx in range(0, w_px, 2):
            mask = 0
            for dy in range(4):
                for dx in range(2):
                    v = float(small[cy + dy, cx + dx])
                    on = (v > 0.24) or (v > 0.09 and v > 0.09 + 0.18 * BAYER_4X4[(cy + dy) & 3, (cx + dx) & 3])
                    if on:
                        mask |= DOT_BITS[dy][dx]
            chars.append(chr(0x2800 + mask))
        rows.append("".join(chars))
    return rows


def image_to_braille(image_path: str | Path, *, cols: int = 72, invert: bool = False) -> list[str]:
    """Convert any PNG/JPG image directly into 2x4 Unicode Braille lines."""
    with Image.open(Path(image_path).expanduser()) as im:
        ink, _, _ = clean_illumination(im)
        if invert:
            ink = 1.0 - ink
    return ink_to_braille_lines(ink, cols=cols)


def render_braille_preview_png(
    braille_lines: Sequence[str],
    out_png: str | Path,
    *,
    title: str = "FIELDGLASS — 2x4 UNICODE BRAILLE SPECIMEN",
    subtitle: str = "",
) -> Path:
    """Render Unicode Braille lines as crisp glowing dots on dark obsidian (zero font glyph gaps)."""
    dst = Path(out_png).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    cols = max((len(r) for r in braille_lines), default=40)

    def _font(size: int, bold: bool = False):
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        return ImageFont.truetype(p, size) if Path(p).is_file() else ImageFont.load_default()

    title_font = _font(16, bold=True)
    sub_font = _font(13, bold=False)

    dot_step = 4
    cell_w = dot_step * 2 + 2
    cell_h = dot_step * 4 + 3
    pad_x, pad_y = 36, 32
    header_h = 58
    img_w = max(800, cols * cell_w + pad_x * 2)
    img_h = len(braille_lines) * cell_h + header_h + pad_y * 2

    img = Image.new("RGB", (img_w, img_h), (11, 15, 23))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([12, 12, img_w - 12, img_h - 12], radius=12, fill=(14, 19, 29), outline=(72, 98, 132), width=2)
    d.text((pad_x, pad_y - 2), title, fill=(242, 196, 92), font=title_font)
    sub_text = subtitle or f"{cols}x{len(braille_lines)} Unicode Braille cells ({cols*2}x{len(braille_lines)*4} sub-pixels)"
    d.text((pad_x, pad_y + 22), sub_text, fill=(94, 218, 238), font=sub_font)

    ox0 = (img_w - cols * cell_w) // 2
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
                    if mask & DOT_BITS[dy][dx]:
                        px = cx + dx * dot_step + 1
                        py = cy + dy * dot_step + 1
                        d.ellipse([px, py, px + 2, py + 2], fill=(242, 236, 214))

    img.save(dst)
    return dst


def save_braille_bundle(
    braille_lines: Sequence[str],
    out_dir: str | Path,
    stem: str,
    *,
    title: str,
    subtitle: str = "",
) -> dict[str, str]:
    """Write .txt, .json, and dot-rendered preview PNG for a Braille specimen."""
    root = Path(out_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    cols = max((len(r) for r in braille_lines), default=0)

    txt_path = root / f"{stem}_braille.txt"
    txt_path.write_text(
        "\n".join([title, subtitle or f"2x4 Unicode Braille ({cols}x{len(braille_lines)} cells)", "", *braille_lines]) + "\n",
        encoding="utf-8",
    )
    json_path = root / f"{stem}_braille.json"
    json_path.write_text(
        json.dumps(
            {
                "id": stem,
                "title": title,
                "subtitle": subtitle,
                "cols": cols,
                "rows": len(braille_lines),
                "subpixels": [cols * 2, len(braille_lines) * 4],
                "lines": list(braille_lines),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    png_path = render_braille_preview_png(braille_lines, root / f"{stem}_braille_preview.png", title=title, subtitle=subtitle)
    return {"txt": str(txt_path), "json": str(json_path), "preview_png": str(png_path)}
