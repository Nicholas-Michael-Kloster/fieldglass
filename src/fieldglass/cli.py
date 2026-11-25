"""Fieldglass command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from PIL import Image

from . import __version__
from .overlay import render_telemetry_overlay
from .plate import (
    clean_illumination,
    extract_sharpest_frame,
    image_to_braille,
    perspective_deskew,
    save_braille_bundle,
    trace_ink_to_svg,
)
from .showcase import push_to_pixel_adb, serve_directory


def _parse_corners(raw: str) -> list[tuple[float, float]]:
    nums = [float(x) for x in raw.replace(";", ",").split(",") if x.strip()]
    if len(nums) != 8:
        raise argparse.ArgumentTypeError("corners must be 8 floats: x1,y1,x2,y2,x3,y3,x4,y4 (TL,TR,BR,BL in 0..1)")
    return [(nums[i], nums[i + 1]) for i in range(0, 8, 2)]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fieldglass",
        description="Fieldglass — Phone-to-telemetry & specimen field instrument (Kloster A_tau(p), SVG, 2x4 Braille, Chiasm).",
    )
    p.add_argument("--version", action="version", version=f"fieldglass {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_sharp = sub.add_parser("frame", help="Extract the sharpest frame in a video window via Laplacian variance")
    p_sharp.add_argument("video", help="Input video file")
    p_sharp.add_argument("-o", "--output", required=True, help="Output PNG path")
    p_sharp.add_argument("--start", type=float, default=0.0, help="Window start in seconds")
    p_sharp.add_argument("--duration", type=float, default=2.0, help="Window length in seconds")
    p_sharp.add_argument("--fps", type=int, default=8, help="Candidate sampling FPS")

    p_plate = sub.add_parser("plate", help="Deskew, clean lamp shadows, trace SVG, and generate 2x4 Braille from an image")
    p_plate.add_argument("image", help="Input photo/frame (PNG/JPG)")
    p_plate.add_argument("-o", "--out-dir", default="fieldglass_out", help="Output directory")
    p_plate.add_argument("--title", default="FIELDGLASS SPECIMEN", help="Botanical plate title")
    p_plate.add_argument("--subtitle", default="", help="Plate subtitle")
    p_plate.add_argument("--corners", type=_parse_corners, default=None, help="Optional 4 normalized corners (TL,TR,BR,BL)")
    p_plate.add_argument("--cols", type=int, default=72, help="Braille width in characters (default: 72)")

    p_br = sub.add_parser("braille", help="Print a crisp 2x4 Unicode Braille specimen straight to your terminal")
    p_br.add_argument("image", help="Input image path")
    p_br.add_argument("--cols", type=int, default=64, help="Terminal width in Braille columns")
    p_br.add_argument("--invert", action="store_true", help="Invert ink polarity")

    p_ov = sub.add_parser("overlay", help="Render real-time Kloster A_tau(p_t) telemetry overlay video + Causal Chiasm SVG")
    p_ov.add_argument("video", help="Input video file")
    p_ov.add_argument("-o", "--out-dir", default="fieldglass_out", help="Output directory")
    p_ov.add_argument("--title", default="FIELDGLASS · KLOSTER OPERATIONAL METACOGNITION")
    p_ov.add_argument("--subtitle", default="Live A_tau(p_t) Superlevel-Set Telemetry")
    p_ov.add_argument("--fps", type=int, default=24)
    p_ov.add_argument("--nexus", type=int, default=None, help="Nexus second for Causal Chiasm split")

    p_srv = sub.add_parser("serve", help="Serve a Fieldglass showcase over loopback HTTP (Range-capable for video)")
    p_srv.add_argument("directory", nargs="?", default=".", help="Showcase directory")
    p_srv.add_argument("--port", type=int, default=8776)

    p_push = sub.add_parser("push", help="Push a Fieldglass showcase bundle to an authorized Pixel/Android via USB ADB")
    p_push.add_argument("directory", help="Showcase directory")
    p_push.add_argument("--name", default="fieldglass", help="Folder name inside /sdcard/Download/")
    p_push.add_argument("--port", type=int, default=8776)
    p_push.add_argument("--no-open", action="store_true", help="Do not launch browser on phone")

    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "frame":
        res = extract_sharpest_frame(
            args.video, args.output, start_sec=args.start, duration_sec=args.duration, sample_fps=args.fps
        )
        print(json.dumps(res, indent=2))
        return 0

    if args.cmd == "plate":
        src = Path(args.image).expanduser().resolve()
        out = Path(args.out_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            work = perspective_deskew(im.convert("RGB"), args.corners) if args.corners else im.convert("RGB")
        ink, archival, bw = clean_illumination(work)
        stem = src.stem
        arch_path = out / f"{stem}_archival.png"
        bw_path = out / f"{stem}_ink_bw.png"
        archival.save(arch_path)
        bw.save(bw_path)
        svg_path = trace_ink_to_svg(ink, out / f"{stem}.svg", title=args.title, subtitle=args.subtitle)
        from .plate import ink_to_braille_lines
        lines = ink_to_braille_lines(ink, cols=args.cols)
        br = save_braille_bundle(lines, out, stem, title=args.title, subtitle=args.subtitle)
        print(json.dumps({"archival": str(arch_path), "ink_bw": str(bw_path), "svg": str(svg_path), "braille": br}, indent=2))
        return 0

    if args.cmd == "braille":
        for row in image_to_braille(args.image, cols=args.cols, invert=args.invert):
            print(row)
        return 0

    if args.cmd == "overlay":
        res = render_telemetry_overlay(
            args.video, args.out_dir, title=args.title, subtitle=args.subtitle, fps=args.fps, nexus_sec=args.nexus
        )
        print(json.dumps({k: v for k, v in res.items() if k != "report"}, indent=2))
        return 0

    if args.cmd == "serve":
        serve_directory(args.directory, port=args.port)
        return 0

    if args.cmd == "push":
        res = push_to_pixel_adb(args.directory, remote_name=args.name, port=args.port, open_browser=not args.no_open)
        print(json.dumps(res, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
