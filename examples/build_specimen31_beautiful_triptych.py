#!/usr/bin/env python3
"""Build Fieldglass Specimen #31 — "Beautiful With a Capital B"
(Original Generative Triptych: Mughal Girih Geometry, Violet Meadow in Poplar Snow & Starship 6-DOF Catch).

100% original pure-math visuals, physics simulation, and additive-synthesis stereo audio
(zero third-party footage, zero copyrighted music, zero GPS metadata, zero cloud tokens).

Generates:
  - 6 crisp 1600x900 museum plates (2 per triptych chapter) + 3x2 contact sheet
  - 3 Archival Vector SVGs + 72-Col 2x4 Unicode Braille Broadsides:
      1) "Mughal Girih & Wazir Khan Star-Rosette" (Terracotta-Ink Engraving)
      2) "Violet Meadow in Drifting Poplar Snow" (Prussian-Violet Botanical)
      3) "Starship Flip Burn & Mechazilla Catch" (Aerospace Cobalt Blueprint)
  - 18.0s @ 24fps (432 frames) 1280x720 animated Kloster A_tau(p_t) telemetry film
    with original pure-math stereo soundtrack (GPS-scrubbed via -map_metadata -1)
  - 36-episode (0.50s cadence) SHA-256 sealed GEM Causal Chiasm & Filtration Tomography
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import (
    a_tau,
    build_svg_and_braille,
    load_font,
    lum_to_8state,
    make_contact_sheet,
    quartic_m4,
    renyi_h2,
    shannon_h1,
    write_chiasm_bundle,
)

DOCS = Path("/home/cowboy/fieldglass/docs")


# ==============================================================================
# CHAPTER I · MUGHAL GIRIH & PUNJAB DOME GEOMETRY (PURE TRIGONOMETRIC SYNTHESIS)
# ==============================================================================
def render_girih_frame(w: int, h: int, prog: float, mode: str = "rosette") -> Image.Image:
    """Render 10-fold decagonal Mughal Girih star-rosette or pointed dome geometry."""
    # Warm sandstone-to-ivory vertical architectural gradient
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    if mode == "rosette":
        top = np.array([22, 36, 68], dtype=np.float32)
        bot = np.array([62, 34, 34], dtype=np.float32)
    else:
        top = np.array([236, 198, 152], dtype=np.float32)
        bot = np.array([247, 236, 214], dtype=np.float32)
    grad = (top * (1.0 - yy) + bot * yy)
    arr = np.broadcast_to(grad[:, None, :], (h, w, 3)).astype(np.uint8).copy()
    im = Image.fromarray(arr, mode="RGB")
    d = ImageDraw.Draw(im, "RGBA")

    cx, cy = w * 0.5, h * 0.5
    s = min(w, h)

    if mode == "rosette":
        # Outer sandstone arch spandrels & tiled border
        pad = int(s * 0.04)
        d.rectangle([pad, pad, w - pad, h - pad], outline=(242, 196, 92, 220), width=max(2, s // 180))
        d.rectangle([pad + 10, pad + 10, w - pad - 10, h - pad - 10], outline=(196, 92, 62, 200), width=max(1, s // 260))

        # Background subtle square-grid girih tile lattice
        step = max(44, int(s * 0.14))
        for gx in range(int(cx % step), w, step):
            for gy in range(int(cy % step), h, step):
                r_bg = step * 0.36
                pts_bg = [
                    (gx + r_bg * math.cos(k * math.pi / 4.0), gy + r_bg * math.sin(k * math.pi / 4.0))
                    for k in range(8)
                ]
                d.polygon(pts_bg, outline=(242, 196, 92, 38))

        # Mughal pointed arch framing the rosette
        arch_w = s * 0.44
        arch_pts = []
        for k in range(41):
            u = k / 40.0
            ang = math.pi * (1.0 - u)
            x = cx + arch_w * math.cos(ang)
            y = cy + s * 0.42 - s * 0.62 * (math.sin(ang) ** 0.78)
            arch_pts.append((x, y))
        arch_pts.extend([(cx + arch_w, h - pad - 10), (cx - arch_w, h - pad - 10)])
        d.polygon(arch_pts, fill=(246, 236, 214, 242), outline=(180, 74, 52, 240))
        d.line(arch_pts[:41], fill=(242, 196, 92, 255), width=max(3, s // 140))

        # Concentric 10-fold decagonal Girih star-rosette blooming with prog
        n_fold = 10
        rot = 0.25 * prog
        rings = [
            (0.36, 0.26, (26, 56, 104, 235), (242, 196, 92, 255)),
            (0.28, 0.19, (186, 66, 52, 240), (250, 232, 190, 255)),
            (0.21, 0.13, (42, 148, 162, 238), (242, 196, 92, 255)),
            (0.14, 0.08, (238, 184, 78, 248), (112, 32, 32, 255)),
            (0.08, 0.04, (148, 36, 54, 250), (252, 240, 206, 255)),
        ]
        cy_r = cy + s * 0.04
        for idx, (r_out_f, r_in_f, fill_c, edge_c) in enumerate(rings):
            gate = max(0.0, min(1.0, (prog * 1.45) - idx * 0.12))
            if gate <= 0.01:
                continue
            r_out = s * r_out_f * (0.35 + 0.65 * gate)
            r_in = s * r_in_f * (0.35 + 0.65 * gate)
            phase = rot * (1.0 if idx % 2 == 0 else -1.0) + (idx * math.pi / n_fold)
            star_pts = []
            for k in range(n_fold * 2):
                a = phase + k * math.pi / n_fold
                rad = r_out if k % 2 == 0 else r_in
                star_pts.append((cx + rad * math.cos(a), cy_r + rad * math.sin(a)))
            d.polygon(star_pts, fill=fill_c, outline=edge_c)
            d.line(star_pts + [star_pts[0]], fill=edge_c, width=max(2, s // 220))

            # Kite-pentagon petals around each star vertex
            if idx < 3 and gate > 0.45:
                for k in range(n_fold):
                    a = phase + k * 2.0 * math.pi / n_fold
                    px = cx + r_out * 0.94 * math.cos(a)
                    py = cy_r + r_out * 0.94 * math.sin(a)
                    pr = s * 0.024 * gate
                    kite = [
                        (px + pr * 1.6 * math.cos(a), py + pr * 1.6 * math.sin(a)),
                        (px + pr * 0.7 * math.cos(a + 1.3), py + pr * 0.7 * math.sin(a + 1.3)),
                        (px - pr * 1.1 * math.cos(a), py - pr * 1.1 * math.sin(a)),
                        (px + pr * 0.7 * math.cos(a - 1.3), py + pr * 0.7 * math.sin(a - 1.3)),
                    ]
                    d.polygon(kite, fill=(248, 224, 152, 220), outline=(88, 34, 28, 235))

        # Center floral jewel
        rj = s * 0.032 * min(1.0, prog * 2.0)
        d.ellipse([cx - rj, cy_r - rj, cx + rj, cy_r + rj], fill=(252, 238, 198, 255), outline=(140, 42, 42, 255), width=max(2, s // 240))
    else:
        # Mode: Wazir Khan / Badshahi pointed dome & twin minarets with compass-straightedge geometry
        base_y = h * 0.78
        # Sun halo behind dome
        for rr, alpha in [(0.34, 40), (0.26, 65), (0.19, 100)]:
            r_sun = s * rr
            d.ellipse([cx - r_sun, h * 0.36 - r_sun, cx + r_sun, h * 0.36 + r_sun], fill=(255, 240, 200, alpha))

        # Compass construction circles (geometric drafting lines)
        for rr in (0.28, 0.20, 0.14):
            r_c = s * rr
            d.ellipse([cx - r_c, h * 0.44 - r_c, cx + r_c, h * 0.44 + r_c], outline=(120, 74, 52, 90), width=max(1, s // 420))
        d.line([(cx, h * 0.06), (cx, h * 0.94)], fill=(120, 74, 52, 95), width=max(1, s // 450))
        d.line([(w * 0.12, h * 0.44), (w * 0.88, h * 0.44)], fill=(120, 74, 52, 95), width=max(1, s // 450))

        # Main sandstone sanctuary facade
        fw = s * 0.62
        d.rectangle([cx - fw * 0.5, h * 0.54, cx + fw * 0.5, base_y], fill=(166, 64, 48, 255), outline=(92, 34, 26, 255), width=max(2, s // 260))

        # White marble bulbous Mughal dome (pointed ogee profile)
        dome_pts = []
        dome_h = s * 0.34
        dome_w = s * 0.24
        for k in range(61):
            u = k / 60.0  # 0 at base -> 1 at finial tip
            profile = math.sin(u * math.pi) ** 0.72 * (1.0 + 0.14 * math.sin(u * math.pi * 2.0))
            if u > 0.85:
                profile *= (1.0 - u) / 0.15
            dome_pts.append((cx + dome_w * profile, h * 0.54 - dome_h * u))
        for k in range(60, -1, -1):
            u = k / 60.0
            profile = math.sin(u * math.pi) ** 0.72 * (1.0 + 0.14 * math.sin(u * math.pi * 2.0))
            if u > 0.85:
                profile *= (1.0 - u) / 0.15
            dome_pts.append((cx - dome_w * profile, h * 0.54 - dome_h * u))
        d.polygon(dome_pts, fill=(246, 241, 230, 255), outline=(112, 74, 52, 255))
        # Ribbed dome flutes
        for fl in (-0.65, -0.32, 0.0, 0.32, 0.65):
            rib = [
                (cx + fl * dome_w * (math.sin((k / 30.0) * math.pi) ** 0.72), h * 0.54 - dome_h * (k / 30.0))
                for k in range(31)
            ]
            d.line(rib, fill=(198, 178, 150, 170), width=max(1, s // 380))
        # Golden finial spire
        tip_y = h * 0.54 - dome_h
        d.line([(cx, tip_y + 4), (cx, tip_y - s * 0.09)], fill=(214, 158, 42, 255), width=max(3, s // 210))
        for dy_f, r_f in [(0.02, 0.014), (0.048, 0.011), (0.072, 0.008)]:
            d.ellipse([cx - s * r_f, tip_y - s * dy_f - s * r_f, cx + s * r_f, tip_y - s * dy_f + s * r_f], fill=(242, 196, 92, 255), outline=(118, 72, 24, 255))

        # Twin flanking minarets
        for side in (-1, 1):
            mx = cx + side * s * 0.36
            mw = s * 0.044
            d.rectangle([mx - mw * 0.5, h * 0.28, mx + mw * 0.5, base_y], fill=(176, 74, 56, 255), outline=(92, 34, 26, 255), width=max(2, s // 300))
            for by_m in (0.42, 0.56):
                d.rectangle([mx - mw * 0.78, h * by_m, mx + mw * 0.78, h * by_m + s * 0.02], fill=(244, 232, 210, 255), outline=(104, 46, 36, 255))
            # Chhatri pavilion domelet
            d.pieslice([mx - mw * 0.65, h * 0.21, mx + mw * 0.65, h * 0.31], 180, 360, fill=(246, 241, 230, 255), outline=(104, 46, 36, 255))
            d.line([(mx, h * 0.21), (mx, h * 0.17)], fill=(214, 158, 42, 255), width=max(2, s // 300))

        # Central recessed iwan pointed arch + decorative floral panels
        iw = s * 0.19
        iwan = []
        for k in range(33):
            u = k / 32.0
            ang = math.pi * (1.0 - u)
            iwan.append((cx + iw * math.cos(ang), base_y - s * 0.19 * (math.sin(ang) ** 0.75)))
        iwan.extend([(cx + iw, base_y), (cx - iw, base_y)])
        d.polygon(iwan, fill=(28, 22, 28, 255), outline=(242, 196, 92, 255))
        # Courtyard reflecting pool below
        d.rectangle([0, base_y, w, h], fill=(212, 186, 152, 255))
        d.rectangle([cx - s * 0.28, base_y + s * 0.03, cx + s * 0.28, h - s * 0.03], fill=(46, 94, 128, 215), outline=(246, 236, 214, 240), width=max(2, s // 260))

    return im


# ==============================================================================
# CHAPTER II · VIOLET MEADOW IN DRIFTING POPLAR SNOW (PROCEDURAL BOTANICAL ART)
# ==============================================================================
def _build_meadow_seeds():
    rng = np.random.default_rng(3102026)
    trees = [(float(rng.uniform(0.03, 0.97)), float(rng.uniform(0.012, 0.038)), float(rng.uniform(0.35, 0.95))) for _ in range(18)]
    stems = [
        (
            float(rng.uniform(0.04, 0.96)),
            float(rng.uniform(0.30, 0.78)),
            float(rng.uniform(0.18, 0.44)),
            float(rng.uniform(0.0, 2.0 * math.pi)),
            int(rng.integers(4, 9)),
            (int(rng.integers(128, 178)), int(rng.integers(92, 146)), int(rng.integers(198, 238))),
        )
        for _ in range(44)
    ]
    fluff = [
        (
            float(rng.uniform(0.0, 1.0)),
            float(rng.uniform(0.0, 1.0)),
            float(rng.uniform(0.004, 0.022)),
            float(rng.uniform(0.08, 0.26)),
            float(rng.uniform(0.0, 2.0 * math.pi)),
            int(rng.integers(75, 205)),
        )
        for _ in range(360)
    ]
    return trees, stems, fluff


MEADOW_TREES, MEADOW_STEMS, MEADOW_FLUFF = _build_meadow_seeds()


def render_meadow_frame(w: int, h: int, t_local: float, show_streamlines: bool = False) -> Image.Image:
    """Render purple wildflowers swaying in misty woods and drifting white cottonwood snow."""
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    sky = np.array([218, 224, 230], dtype=np.float32)
    mid = np.array([152, 166, 152], dtype=np.float32)
    gnd = np.array([92, 108, 86], dtype=np.float32)
    grad = np.where(yy < 0.45, sky * (1.0 - yy / 0.45) + mid * (yy / 0.45), mid * (1.0 - (yy - 0.45) / 0.55) + gnd * ((yy - 0.45) / 0.55))
    arr = np.broadcast_to(grad[:, None, :], (h, w, 3)).astype(np.uint8).copy()
    im = Image.fromarray(arr, mode="RGB")
    d = ImageDraw.Draw(im, "RGBA")
    s = min(w, h)

    # Background woodland birch/ash trunks
    for tx, tw_f, depth in sorted(MEADOW_TREES, key=lambda r: r[2]):
        x0 = tx * w
        tw = tw_f * s
        shade = int(74 + 78 * (1.0 - depth))
        d.rectangle([x0 - tw * 0.5, 0, x0 + tw * 0.5, h * (0.68 + 0.16 * depth)], fill=(shade, shade - 4, shade - 8, int(130 + 95 * depth)))
        # Subtle branches
        for b_idx in range(2):
            by = h * (0.14 + 0.18 * b_idx + 0.05 * depth)
            dir_b = 1 if (b_idx + int(tx * 100)) % 2 == 0 else -1
            d.line([(x0, by), (x0 + dir_b * tw * 3.8, by - s * 0.11)], fill=(shade - 8, shade - 10, shade - 14, int(110 + 80 * depth)), width=max(1, int(tw * 0.22)))

    # Soft cottonwood snow-carpet haze along the meadow floor
    for band in range(6):
        y_b = h * (0.56 + band * 0.08)
        d.rectangle([0, y_b, w, h], fill=(246, 244, 248, 28 + band * 12))

    # Optional laminar curl-wind streamlines for plate 04
    if show_streamlines:
        for row in range(11):
            pts = []
            y_base = h * (0.12 + row * 0.075)
            for k in range(36):
                u = k / 35.0
                px = u * w
                py = y_base + s * 0.045 * math.sin(u * 5.0 + row * 0.7 + t_local * 0.8) + u * s * 0.08
                pts.append((px, py))
            d.line(pts, fill=(255, 252, 255, 115), width=max(1, s // 360))

    # Swaying violet wildflower stalks & blossoms
    for sx, base_y_f, height_f, phase, n_blooms, col in sorted(MEADOW_STEMS, key=lambda r: r[1]):
        x_base = sx * w
        y_base = h * (0.58 + 0.42 * base_y_f)
        sway = s * 0.032 * math.sin(t_local * 1.45 + phase)
        stem_h = s * height_f
        pts = []
        for k in range(8):
            u = k / 7.0
            px = x_base + sway * (u * u) + s * 0.015 * math.sin(phase + u * 2.5)
            py = y_base - stem_h * u
            pts.append((px, py))
        d.line(pts, fill=(58, 96, 62, 230), width=max(2, s // 300))

        # Lance leaves
        for lu, ldir in [(0.35, -1), (0.55, 1)]:
            lx = x_base + sway * (lu * lu)
            ly = y_base - stem_h * lu
            d.polygon([(lx, ly), (lx + ldir * s * 0.025, ly - s * 0.018), (lx + ldir * s * 0.008, ly - s * 0.004)], fill=(66, 112, 68, 215))

        # Violet flower clusters near stem top
        for b in range(n_blooms):
            u = 0.54 + 0.46 * (b / max(1, n_blooms - 1))
            bx = x_base + sway * (u * u) + (s * 0.022 * math.sin(phase + b * 2.1))
            by = y_base - stem_h * u
            pr = s * (0.012 + 0.006 * (1.0 - abs(u - 0.82)))
            for p_idx in range(5):
                ang = phase + b + p_idx * (2.0 * math.pi / 5.0)
                px = bx + pr * 0.85 * math.cos(ang)
                py = by + pr * 0.85 * math.sin(ang)
                d.ellipse([px - pr * 0.55, py - pr * 0.55, px + pr * 0.55, py + pr * 0.55], fill=(col[0], col[1], col[2], 235), outline=(88, 52, 134, 210))
            d.ellipse([bx - pr * 0.25, by - pr * 0.25, bx + pr * 0.25, by + pr * 0.25], fill=(252, 232, 146, 250))

    # Drifting white cottonwood / poplar snow tufts
    for fx, fy, fr_f, speed, phase, alpha in MEADOW_FLUFF:
        px = ((fx + speed * 0.22 * t_local + 0.025 * math.sin(t_local * 1.1 + phase)) % 1.06 - 0.03) * w
        py = ((fy + speed * 0.08 * t_local + 0.018 * math.cos(t_local * 0.9 + phase)) % 1.06 - 0.03) * h
        r = max(2.0, fr_f * s)
        d.ellipse([px - r * 1.5, py - r * 1.1, px + r * 1.5, py + r * 1.1], fill=(252, 250, 255, alpha // 2))
        d.ellipse([px - r * 0.7, py - r * 0.7, px + r * 0.7, py + r * 0.7], fill=(255, 255, 255, min(255, alpha + 40)))

    return im


# ==============================================================================
# CHAPTER III · STARSHIP 6-DOF FLIP BURN & MECHAZILLA TOWER CATCH
# ==============================================================================
def simulate_starship_landing(n_steps: int = 144, dt: float = 1.0 / 24.0) -> list[dict]:
    """Integrate simplified 2D/6-DOF Starship belly-flop -> Raptor flip -> tower catch."""
    states = []
    z = 420.0      # altitude (m)
    x = -130.0     # crossrange to Mechazilla tower at x=0 (m)
    vz = -64.0     # vertical velocity (m/s)
    vx = 28.0      # horizontal velocity (m/s)
    theta = 70.0   # pitch from vertical (deg): 70=belly-flop, 0=upright
    g = 9.81
    t_total = (n_steps - 1) * dt
    for k in range(n_steps):
        t = k * dt
        u = t / max(1e-6, t_total)
        # Target smooth guidance profile: belly-flop (0..0.24), flip burn (0.24..0.62), hover catch (0.62..1.0)
        if u < 0.24:
            throttle = 0.0
            theta_target = 68.0 - 8.0 * (u / 0.24)
            phase_name = "AERODYNAMIC BELLY-FLOP"
        elif u < 0.62:
            f = (u - 0.24) / 0.38
            throttle = 0.78 + 0.22 * math.sin(f * math.pi)
            theta_target = 60.0 * ((1.0 - f) ** 1.8)
            phase_name = "3-RAPTOR FLIP BURN"
        elif u < 0.92:
            f = (u - 0.62) / 0.30
            throttle = 0.62 * (1.0 - 0.35 * f)
            theta_target = 0.0
            phase_name = "MECHAZILLA HOVER APPROACH"
        else:
            throttle = 0.28 * max(0.0, 1.0 - (u - 0.92) / 0.08)
            theta_target = 0.0
            phase_name = "CHOPSTICK TOWER CATCH"

        theta += (theta_target - theta) * min(1.0, dt * 5.0)
        # Closed-loop PD guidance on altitude & crossrange so touchdown hits (0, 38m tower catch height)
        t_rem = max(0.35, t_total * 0.94 - t)
        z_goal = 40.0
        if u >= 0.92:
            z = z_goal
            x = 0.0
            vz = 0.0
            vx = 0.0
        else:
            # Aerodynamic drag + controlled Raptor retro-thrust
            az_cmd = 2.0 * (z_goal - z - vz * t_rem) / (t_rem * t_rem)
            ax_cmd = 2.0 * (0.0 - x - vx * t_rem) / (t_rem * t_rem)
            az = max(-12.0, min(32.0, az_cmd))
            ax = max(-18.0, min(18.0, ax_cmd))
            vz += az * dt
            vx += ax * dt
            z = max(z_goal, z + vz * dt)
            x += vx * dt

        states.append({
            "t": t, "u": u, "x": x, "z": z, "vx": vx, "vz": vz,
            "theta_deg": theta, "throttle": throttle, "phase": phase_name,
        })
    return states


STARSHIP_STATES = simulate_starship_landing(144, 1.0 / 24.0)


def render_starship_frame(w: int, h: int, st: dict, show_vectors: bool = True, blueprint: bool = False) -> Image.Image:
    """Render Starship flip maneuver, Mach-diamond methane exhaust, and Mechazilla catch tower."""
    if blueprint:
        im = Image.new("RGB", (w, h), (255, 255, 255))
        d = ImageDraw.Draw(im, "RGBA")
    else:
        yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        space = np.array([10, 18, 38], dtype=np.float32)
        horizon = np.array([56, 86, 128], dtype=np.float32)
        sunset = np.array([196, 138, 102], dtype=np.float32)
        ocean = np.array([18, 42, 66], dtype=np.float32)
        grad = np.where(
            yy < 0.62,
            space * (1.0 - yy / 0.62) + horizon * (yy / 0.62),
            np.where(yy < 0.74, horizon * (1.0 - (yy - 0.62) / 0.12) + sunset * ((yy - 0.62) / 0.12), ocean),
        )
        arr = np.broadcast_to(grad[:, None, :], (h, w, 3)).astype(np.uint8).copy()
        im = Image.fromarray(arr, mode="RGB")
        d = ImageDraw.Draw(im, "RGBA")
    s = min(w, h)

    # Stars in upper sky (skip in blueprint mode for razor-clean drafting paper)
    if not blueprint:
        rng = np.random.default_rng(77)
        for _ in range(70):
            sx = int(rng.integers(10, w - 10))
            sy = int(rng.integers(10, int(h * 0.48)))
            br = int(rng.integers(140, 255))
            d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(br, br, 255, 210))

    # Coastline & Boca Chica style launch pad ground
    gnd_y = int(h * 0.82)
    if blueprint:
        d.line([(int(w * 0.06), gnd_y), (int(w * 0.94), gnd_y)], fill=(18, 36, 62, 255), width=max(3, s // 220))
    else:
        d.rectangle([0, gnd_y, w, h], fill=(32, 42, 50, 255))
        d.line([(0, gnd_y), (w, gnd_y)], fill=(116, 146, 168, 220), width=2)

    # Coordinate mapping: tower at tx = 0.64*w, z=0 -> gnd_y, z=420 -> 0.14*h
    tx = w * 0.64
    def world_to_px(wx: float, wz: float) -> tuple[float, float]:
        px = tx + (wx / 220.0) * (w * 0.55)
        py = gnd_y - (wz / 450.0) * (h * 0.72)
        return px, py

    # Dotted planned descent trajectory arc
    traj_pts = [world_to_px(s0["x"], s0["z"]) for s0 in STARSHIP_STATES[::3]]
    for j in range(0, len(traj_pts) - 1, 2):
        d.line([traj_pts[j], traj_pts[j + 1]], fill=(18, 38, 68, 220) if blueprint else (94, 218, 238, 130), width=max(2, s // 300) if blueprint else max(1, s // 380))

    # Mechazilla Catch Tower (lattice truss + chopstick arms!)
    tw_w = s * 0.048
    tw_top = gnd_y - s * 0.34
    tw_x = tx + s * 0.068
    d.rectangle(
        [tw_x - tw_w * 0.5, tw_top, tw_x + tw_w * 0.5, gnd_y],
        fill=(255, 255, 255, 255) if blueprint else (26, 36, 48, 240),
        outline=(14, 28, 52, 255) if blueprint else (146, 168, 190, 240),
        width=max(3, s // 240) if blueprint else 2,
    )
    # Cross-bracing X-trusses
    n_bays = 7
    bay_h = (gnd_y - tw_top) / n_bays
    for b in range(n_bays):
        y0 = tw_top + b * bay_h
        y1 = y0 + bay_h
        tr_col = (24, 48, 84, 240) if blueprint else (120, 142, 166, 210)
        tr_w = max(2, s // 360) if blueprint else 1
        d.line([(tw_x - tw_w * 0.5, y0), (tw_x + tw_w * 0.5, y1)], fill=tr_col, width=tr_w)
        d.line([(tw_x + tw_w * 0.5, y0), (tw_x - tw_w * 0.5, y1)], fill=tr_col, width=tr_w)
        if blueprint:
            d.line([(tw_x - tw_w * 0.5, y0), (tw_x + tw_w * 0.5, y0)], fill=tr_col, width=tr_w)
    # Chopstick catch arms reaching left toward x=tx
    arm_y = world_to_px(0.0, 40.0)[1] - s * 0.045
    d.rectangle(
        [tx - s * 0.036, arm_y - 5, tw_x - tw_w * 0.5, arm_y + 5],
        fill=(24, 48, 84, 255) if blueprint else (224, 178, 86, 255),
        outline=(14, 28, 52, 255) if blueprint else (42, 34, 22, 255),
    )
    d.line([(tw_x - tw_w * 0.5, arm_y - s * 0.06), (tx - s * 0.02, arm_y)], fill=(18, 38, 68, 255) if blueprint else (196, 212, 226, 220), width=max(2, s // 300))

    # Starship vehicle transform at (ship_x, ship_y) with pitch angle theta
    ship_x, ship_y = world_to_px(st["x"], st["z"])
    th = math.radians(st["theta_deg"])
    def rot_pt(lx: float, ly: float) -> tuple[float, float]:
        rx = lx * math.cos(th) - ly * math.sin(th)
        ry = lx * math.sin(th) + ly * math.cos(th)
        return ship_x + rx, ship_y + ry

    ship_h = s * 0.21
    ship_r = s * 0.024

    # Raptor methane exhaust plume + Mach diamonds when throttle > 0.05!
    thr = st["throttle"]
    if thr > 0.05:
        plume_len = ship_h * (0.45 + 1.15 * thr)
        p_outer = [rot_pt(-ship_r * 0.85, ship_h * 0.48), rot_pt(ship_r * 0.85, ship_h * 0.48), rot_pt(ship_r * 1.45, ship_h * 0.48 + plume_len), rot_pt(-ship_r * 1.45, ship_h * 0.48 + plume_len)]
        if blueprint:
            d.polygon(p_outer, fill=(235, 240, 248, 255), outline=(36, 72, 118, 255))
            d.line(p_outer + [p_outer[0]], fill=(36, 72, 118, 255), width=max(2, s // 320))
        else:
            d.polygon(p_outer, fill=(248, 172, 92, int(130 * thr)))
        p_core = [rot_pt(-ship_r * 0.58, ship_h * 0.48), rot_pt(ship_r * 0.58, ship_h * 0.48), rot_pt(0.0, ship_h * 0.48 + plume_len * 0.92)]
        if blueprint:
            d.polygon(p_core, fill=(255, 255, 255, 255), outline=(14, 30, 56, 255))
            d.line(p_core + [p_core[0]], fill=(14, 30, 56, 255), width=max(2, s // 320))
        else:
            d.polygon(p_core, fill=(142, 168, 255, int(235 * thr)))
        for k_d in range(4):
            dy_d = ship_h * 0.54 + (k_d + 0.5) * (plume_len * 0.19)
            dw = ship_r * (0.46 - k_d * 0.08)
            dh = ship_r * 0.58
            dia = [rot_pt(0, dy_d - dh), rot_pt(dw, dy_d), rot_pt(0, dy_d + dh), rot_pt(-dw, dy_d)]
            if blueprint:
                d.polygon(dia, fill=(24, 52, 92, 230), outline=(10, 22, 40, 255))
            else:
                d.polygon(dia, fill=(255, 246, 224, int(240 * thr)))

        if not blueprint and st["z"] < 140.0:
            near = max(0.0, 1.0 - (st["z"] - 40.0) / 100.0)
            for j in range(9):
                vx_c = tx + (j - 4) * s * 0.055 * (0.6 + near)
                vy_c = gnd_y - s * 0.015 * (1 + (j % 3))
                rc = s * (0.032 + 0.038 * near)
                d.ellipse([vx_c - rc, vy_c - rc * 0.65, vx_c + rc, vy_c + rc * 0.65], fill=(242, 232, 220, int(95 * near * thr)))

    # Stainless-steel hull + dark heatshield windward edge + nosecone + flaps
    hull = [
        rot_pt(-ship_r, -ship_h * 0.22),
        rot_pt(-ship_r * 0.82, -ship_h * 0.38),
        rot_pt(0.0, -ship_h * 0.52),
        rot_pt(ship_r * 0.82, -ship_h * 0.38),
        rot_pt(ship_r, -ship_h * 0.22),
        rot_pt(ship_r, ship_h * 0.48),
        rot_pt(-ship_r, ship_h * 0.48),
    ]
    d.polygon(hull, fill=(255, 255, 255, 255) if blueprint else (214, 222, 232, 255), outline=(10, 22, 42, 255) if blueprint else (44, 58, 76, 255))
    if blueprint:
        d.line(hull + [hull[0]], fill=(10, 22, 42, 255), width=max(3, s // 240))
    tile_side = [rot_pt(ship_r * 0.25, -ship_h * 0.46), rot_pt(ship_r, -ship_h * 0.22), rot_pt(ship_r, ship_h * 0.48), rot_pt(ship_r * 0.25, ship_h * 0.48)]
    d.polygon(tile_side, fill=(20, 42, 74, 235) if blueprint else (36, 44, 58, 225))
    fwd_l = [rot_pt(-ship_r, -ship_h * 0.30), rot_pt(-ship_r * 2.1, -ship_h * 0.16), rot_pt(-ship_r, -ship_h * 0.14)]
    fwd_r = [rot_pt(ship_r, -ship_h * 0.30), rot_pt(ship_r * 2.1, -ship_h * 0.16), rot_pt(ship_r, -ship_h * 0.14)]
    aft_l = [rot_pt(-ship_r, ship_h * 0.18), rot_pt(-ship_r * 2.5, ship_h * 0.45), rot_pt(-ship_r, ship_h * 0.47)]
    aft_r = [rot_pt(ship_r, ship_h * 0.18), rot_pt(ship_r * 2.5, ship_h * 0.45), rot_pt(ship_r, ship_h * 0.47)]
    for fl in (fwd_l, fwd_r, aft_l, aft_r):
        d.polygon(fl, fill=(24, 50, 86, 240) if blueprint else (52, 64, 82, 255), outline=(10, 22, 42, 255) if blueprint else (170, 188, 206, 235))

    # Compact physics telemetry card in top-left (sized cleanly to font metrics)
    if show_vectors and not blueprint:
        f_sz = max(11, s // 34)
        f_sm = load_font(f_sz, bold=True)
        bx0, by0 = int(w * 0.03), int(h * 0.11)
        lh = int(f_sz * 1.42)
        box_h = lh * 3 + 22
        box_w = int(w * 0.36)
        d.rounded_rectangle([bx0, by0, bx0 + box_w, by0 + box_h], radius=8, fill=(10, 16, 28, 212), outline=(94, 218, 238, 225), width=2)
        d.text((bx0 + 12, by0 + 10), st["phase"], fill=(242, 196, 92, 255), font=f_sm)
        d.text((bx0 + 12, by0 + 10 + lh), f"ALT: {st['z']:6.1f} m   VZ: {st['vz']:+5.1f} m/s", fill=(94, 218, 238, 255), font=f_sm)
        d.text((bx0 + 12, by0 + 10 + lh * 2), f"PITCH: {st['theta_deg']:4.1f} deg  THR: {int(thr*100):3d}%", fill=(210, 224, 238, 255), font=f_sm)

    return im


# ==============================================================================
# ORIGINAL PURE-MATH STEREO SOUNDTRACK (44.1 kHz PCM WAV · ZERO COPYRIGHT)
# ==============================================================================
def synthesize_triptych_wav(out_wav: Path, duration_s: float = 18.0, sr: int = 44100) -> None:
    """Synthesize a gentle 3-chapter original stereo harmonic score in pure numpy."""
    n = int(round(duration_s * sr))
    t = np.arange(n, dtype=np.float64) / sr
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    def add_plucked(t0: float, dur: float, freq: float, amp: float, pan: float = 0.0) -> None:
        i0 = int(t0 * sr)
        i1 = min(n, int((t0 + dur) * sr))
        if i1 <= i0:
            return
        lt = np.arange(i1 - i0, dtype=np.float64) / sr
        env = np.minimum(1.0, lt / 0.015) * np.exp(-lt * (3.2 / max(0.3, dur)))
        sig = (
            np.sin(2.0 * math.pi * freq * lt)
            + 0.32 * np.sin(2.0 * math.pi * freq * 2.0 * lt) * np.exp(-lt * 4.0)
            + 0.14 * np.sin(2.0 * math.pi * freq * 3.0 * lt) * np.exp(-lt * 6.0)
        ) * env * amp
        gl = math.sqrt(0.5 * (1.0 - pan))
        gr = math.sqrt(0.5 * (1.0 + pan))
        left[i0:i1] += sig * gl
        right[i0:i1] += sig * gr

    def add_pad(t0: float, dur: float, freqs: list[float], amp: float) -> None:
        i0 = int(t0 * sr)
        i1 = min(n, int((t0 + dur) * sr))
        if i1 <= i0:
            return
        lt = np.arange(i1 - i0, dtype=np.float64) / sr
        env = np.sin(math.pi * np.clip(lt / dur, 0.0, 1.0)) ** 1.2
        for idx, f in enumerate(freqs):
            det = 1.0 + (idx - 1) * 0.0022
            left[i0:i1] += np.sin(2.0 * math.pi * f * lt) * env * amp
            right[i0:i1] += np.sin(2.0 * math.pi * f * det * lt) * env * amp

    # Chapter I (0..6s): Mughal geometric harmonic chimes (D Hijaz flavor)
    add_pad(0.0, 6.4, [146.83, 220.0, 293.66], 0.09)
    ch1_notes = [293.66, 311.13, 369.99, 392.00, 440.00, 466.16, 587.33, 440.00, 392.00, 369.99, 311.13, 293.66]
    for idx, f in enumerate(ch1_notes):
        add_plucked(0.25 + idx * 0.45, 1.4, f, 0.14, pan=0.45 * math.sin(idx * 0.9))

    # Chapter II (6..12s): Airy Violet Meadow Lydian glass bells + soft breeze
    add_pad(5.8, 6.4, [185.00, 277.18, 369.99, 440.00], 0.075)
    ch2_notes = [369.99, 440.00, 554.37, 659.25, 830.61, 659.25, 554.37, 440.00, 493.88, 554.37]
    for idx, f in enumerate(ch2_notes):
        add_plucked(6.15 + idx * 0.56, 2.0, f, 0.11, pan=-0.5 * math.cos(idx * 0.8))

    # Chapter III (12..18s): Deep Raptor harmonic swell -> triumphant Major-9th tower catch!
    add_pad(11.8, 3.8, [73.42, 110.0, 146.83, 220.0], 0.11)
    add_pad(14.8, 3.2, [146.83, 220.0, 293.66, 369.99, 440.0, 493.88], 0.095)
    for idx, f in enumerate([293.66, 369.99, 440.0, 587.33, 659.25, 739.99]):
        add_plucked(15.2 + idx * 0.36, 2.1, f, 0.12, pan=0.35 * ((idx % 2) * 2 - 1))

    # Gentle master envelope & normalization
    fade = np.minimum(1.0, t / 0.25) * np.minimum(1.0, (duration_s - t) / 0.5)
    left *= fade
    right *= fade
    peak = max(1e-6, float(max(np.max(np.abs(left)), np.max(np.abs(right)))))
    scale = 0.82 / peak
    stereo = np.stack([left * scale, right * scale], axis=-1)
    pcm = np.clip(np.round(stereo * 32767.0), -32768, 32767).astype("<i2")

    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


# ==============================================================================
# MAIN SPECIMEN #31 BUILDER
# ==============================================================================
def build_specimen31() -> dict:
    print("\n================ BUILDING SPECIMEN #31 ('BEAUTIFUL WITH A CAPITAL B' · ORIGINAL TRIPTYCH) ================")
    root = DOCS / "specimen31"
    plates_dir = root / "plates"
    assets_dir = root / "assets"
    chiasm_dir = root / "chiasm"
    video_dir = root / "video"
    for d in (plates_dir, assets_dir, chiasm_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1) Render 6 high-resolution 1600x900 pure-math museum plates + contact sheet
    plate_defs = [
        ("01_mughal_girih_rosette", "I · 10-Fold Mughal Girih Star-Rosette", lambda: render_girih_frame(1600, 900, 1.0, "rosette")),
        ("02_wazir_khan_dome_geometry", "I · Pointed Ogee Dome & Compass Lines", lambda: render_girih_frame(1600, 900, 1.0, "dome")),
        ("03_violet_meadow_poplar_snow", "II · Violet Meadow in Poplar Snow", lambda: render_meadow_frame(1600, 900, 2.4, False)),
        ("04_botanical_wind_streamlines", "II · Botanical Curl-Wind Streamlines", lambda: render_meadow_frame(1600, 900, 4.2, True)),
        ("05_starship_bellyflop_flip", "III · Starship 3-Raptor Flip Burn", lambda: render_starship_frame(1600, 900, STARSHIP_STATES[62], True)),
        ("06_mechazilla_tower_catch", "III · Mechazilla Chopstick Tower Catch", lambda: render_starship_frame(1600, 900, STARSHIP_STATES[132], True)),
    ]
    tiles = []
    pmap: dict[str, Path] = {}
    for slug, label, fn in plate_defs:
        p = plates_dir / f"{slug}.jpg"
        im = fn()
        im.save(p, quality=93, optimize=True)
        pmap[slug] = p
        tiles.append((label, p))
        print(f"  Plate {slug} rendered ({im.size[0]}x{im.size[1]})")

    make_contact_sheet(tiles, plates_dir / "contact_sheet_specimen31.jpg", cols=3, tile_w=460, tile_h=280)

    # 2) THREE Archival Vector SVGs + 72-Col 2x4 Unicode Braille Broadsides
    build_svg_and_braille(
        pmap["01_mughal_girih_rosette"],
        assets_dir,
        "punjab_girih_rosette",
        title='"BEAUTIFUL WITH A CAPITAL B" — MUGHAL 10-FOLD GIRIH ROSETTE',
        subtitle="Compass-and-Straightedge Islamic Star Tessellation SVG & 72-Col Braille · Specimen #31",
        crop_box=(0.14, 0.03, 0.86, 0.97),
        levels=(0.24, 0.42, 1.2),
        colors=("#8b3a2e", "#1c1412"),
        braille_cols=72,
        edge_hybrid=True,
    )
    build_svg_and_braille(
        pmap["03_violet_meadow_poplar_snow"],
        assets_dir,
        "violet_meadow_poplar_snow",
        title="VIOLET MEADOW IN DRIFTING POPLAR SNOW — BOTANICAL STUDY",
        subtitle="Procedural Wildflower & Curl-Wind Fluff Vector SVG & 72-Col Braille · Specimen #31",
        crop_box=(0.06, 0.04, 0.94, 0.96),
        levels=(0.25, 0.44, 1.2),
        colors=("#52387d", "#1a122b"),
        braille_cols=72,
        edge_hybrid=True,
    )
    starship_bp = Path("/tmp/specimen31_starship_blueprint.png")
    render_starship_frame(1600, 900, STARSHIP_STATES[62], show_vectors=False, blueprint=True).save(starship_bp)
    build_svg_and_braille(
        starship_bp,
        assets_dir,
        "starship_flip_and_catch",
        title="STARSHIP 3-RAPTOR FLIP BURN & MECHAZILLA TOWER CATCH",
        subtitle="6-DOF Retro-Propulsive Landing Schematic SVG & 72-Col Braille · Specimen #31",
        crop_box=(0.24, 0.08, 0.80, 0.90),
        levels=(0.50, 0.72, 0.9),
        colors=("#1f4d7a", "#0e1a2b"),
        braille_cols=72,
        edge_hybrid=False,
    )
    starship_bp.unlink(missing_ok=True)

    # 3) 18.0s @ 24fps (432 frames) live animated triptych + Kloster A_tau(p_t) HUD + original stereo audio
    fps = 24
    n_frames = 18 * fps  # 432 frames
    out_w, out_h = 1280, 720
    vw, vh = 768, 432
    total_real_s = n_frames / float(fps)

    print(f"Synthesizing {n_frames} original animated triptych frames ({total_real_s:.1f}s @ {fps}fps)...")
    frames = np.zeros((n_frames, vh, vw, 3), dtype=np.uint8)
    for i in range(n_frames):
        sec = i / float(fps)
        if sec < 6.0:
            prog = sec / 6.0
            if sec < 3.6:
                im_f = render_girih_frame(vw, vh, min(1.0, sec / 3.0), "rosette")
            else:
                # Smooth crossfade from star-rosette into sunlit dome geometry
                alpha = min(1.0, (sec - 3.6) / 1.2)
                a_im = render_girih_frame(vw, vh, 1.0, "rosette")
                b_im = render_girih_frame(vw, vh, 1.0, "dome")
                im_f = Image.blend(a_im, b_im, alpha)
        elif sec < 12.0:
            t_loc = sec - 6.0
            im_f = render_meadow_frame(vw, vh, t_loc, show_streamlines=(t_loc > 3.5))
            if t_loc < 0.5:
                prev_im = render_girih_frame(vw, vh, 1.0, "dome")
                im_f = Image.blend(prev_im, im_f, t_loc / 0.5)
        else:
            idx_s = min(len(STARSHIP_STATES) - 1, i - 12 * fps)
            im_f = render_starship_frame(vw, vh, STARSHIP_STATES[idx_s], show_vectors=True)
            if sec < 12.5:
                prev_im = render_meadow_frame(vw, vh, 6.0, show_streamlines=True)
                im_f = Image.blend(prev_im, im_f, (sec - 12.0) / 0.5)
        frames[i] = np.asarray(im_f, dtype=np.uint8)

    # Compute genuine Kloster A_tau(p_t), Shannon H1, Renyi H2, Quartic M4, and 36 Chiasm episodes
    a004 = np.zeros(n_frames, dtype=np.int32)
    a010 = np.zeros(n_frames, dtype=np.int32)
    a020 = np.zeros(n_frames, dtype=np.int32)
    h1_arr = np.zeros(n_frames, dtype=np.float32)
    h2_arr = np.zeros(n_frames, dtype=np.float32)
    m4_arr = np.zeros(n_frames, dtype=np.float32)
    hists = np.zeros((n_frames, 256), dtype=np.float32)

    episodes_8, ep_a004, ep_a010, ep_times = [], [], [], []
    ep_step = max(1, int(round(0.50 * fps)))  # 0.50s cadence -> 36 episodes!
    for i in range(n_frames):
        sub = frames[i, ::3, ::3, :]
        lum = (0.299 * sub[..., 0] + 0.587 * sub[..., 1] + 0.114 * sub[..., 2]).astype(np.uint8)
        counts = np.bincount(lum.ravel(), minlength=256).astype(np.float64)
        p = counts / counts.sum()
        hists[i] = p
        a004[i] = a_tau(p, 0.004)
        a010[i] = a_tau(p, 0.010)
        a020[i] = a_tau(p, 0.020)
        h1_arr[i] = shannon_h1(p)
        h2_arr[i] = renyi_h2(p)
        m4_arr[i] = quartic_m4(p)
        if i % ep_step == 0:
            episodes_8.append(lum_to_8state(p))
            ep_a004.append(int(a004[i]))
            ep_a010.append(int(a010[i]))
            ep_times.append(i / float(fps))

    # Synthesize original stereo WAV
    tmp_wav = Path("/tmp/specimen31_score.wav")
    synthesize_triptych_wav(tmp_wav, duration_s=total_real_s, sr=44100)

    # Render HUD background template
    f_title = load_font(15, bold=True)
    f_eq = load_font(12, bold=True)
    f_big = load_font(22, bold=True)
    f_med = load_font(15, bold=True)
    f_sm = load_font(11, bold=False)
    f_sm_b = load_font(11, bold=True)

    bg = Image.new("RGB", (out_w, out_h), (10, 14, 22))
    dr = ImageDraw.Draw(bg)
    rx0, rx1 = vw + 14, out_w - 14

    dr.rounded_rectangle([rx0, 10, rx1, 96], radius=10, fill=(16, 23, 35), outline=(242, 196, 92), width=2)
    dr.text((rx0 + 14, 18), 'SPECIMEN #31 · "BEAUTIFUL WITH A CAPITAL B"', fill=(242, 196, 92), font=f_title)
    dr.text((rx0 + 14, 44), "A_tau(p) = sum_x 1[p(x) > tau]", fill=(94, 218, 238), font=f_eq)
    dr.text((rx0 + 14, 68), "Girih Geometry · Poplar Snow · Starship 6-DOF", fill=(150, 168, 190), font=f_sm)

    kpi_meta = [
        ("A_0.004(p)  BROAD", (94, 218, 238)),
        ("A_0.010(p)  CORE", (242, 196, 92)),
        ("M_0.01  MOMENTUM", (244, 106, 126)),
        ("H1 / H2  ENTROPY", (168, 226, 142)),
        ("M4^(1/4)  PURITY", (195, 162, 255)),
    ]
    kpi_boxes = []
    for idx, (lbl, col) in enumerate(kpi_meta):
        by0 = 108 + idx * 65
        by1 = by0 + 57
        kpi_boxes.append((rx0, by0, rx1, by1))
        dr.rounded_rectangle([rx0, by0, rx1, by1], radius=8, fill=(16, 23, 35), outline=(44, 62, 86), width=1)
        dr.text((rx0 + 14, by0 + 18), lbl, fill=col, font=f_sm_b)

    tx0, ty0, tx1, ty1 = 12, vh + 12, vw, out_h - 12
    dr.rounded_rectangle([tx0, ty0, tx1, ty1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((tx0 + 14, ty0 + 8), "TRIPTYCH PHASE TRAJECTORY A_tau(p_t)  (I: Girih · II: Poplar Snow · III: Starship)", fill=(205, 218, 232), font=f_sm_b)
    px0, py0, px1, py1 = tx0 + 44, ty0 + 32, tx1 - 14, ty1 - 26
    dr.rectangle([px0, py0, px1, py1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)

    # Shade 3 triptych chapters cleanly
    c1_x = int(round(px0 + (6.0 / total_real_s) * (px1 - px0)))
    c2_x = int(round(px0 + (12.0 / total_real_s) * (px1 - px0)))
    dr.rectangle([px0 + 1, py0 + 1, c1_x, py1 - 1], fill=(32, 22, 20))
    dr.rectangle([c1_x + 1, py0 + 1, c2_x, py1 - 1], fill=(24, 20, 36))
    dr.rectangle([c2_x + 1, py0 + 1, px1 - 1, py1 - 1], fill=(14, 24, 38))
    dr.text((px0 + 8, py0 + 6), "I · GIRIH GEOMETRY", fill=(242, 196, 92), font=f_sm_b)
    dr.text((c1_x + 8, py0 + 6), "II · POPLAR SNOW", fill=(195, 162, 255), font=f_sm_b)
    dr.text((c2_x + 8, py0 + 6), "III · STARSHIP CATCH", fill=(94, 218, 238), font=f_sm_b)

    for val in (0, 20, 40, 60):
        gy = int(round(py1 - (val / 65.0) * (py1 - py0 - 8) - 4))
        dr.line([(px0, gy), (px1, gy)], fill=(26, 38, 54), width=1)
        dr.text((tx0 + 10, gy - 6), f"{val:>2d}", fill=(128, 146, 168), font=f_sm)
    for k in range(7):
        st_sec = total_real_s * (k / 6.0)
        gx = int(round(px0 + (k / 6.0) * (px1 - px0)))
        dr.line([(gx, py0), (gx, py1)], fill=(22, 33, 47), width=1)
        dr.text((gx - 12, py1 + 6), f"{st_sec:.0f}s", fill=(128, 146, 168), font=f_sm)

    def build_pts(vals: np.ndarray, ymax: float, end_idx: int):
        return [
            (
                int(round(px0 + (k / max(1, n_frames - 1)) * (px1 - px0))),
                int(round(py1 - min(1.0, float(vals[k]) / ymax) * (py1 - py0 - 8) - 4)),
            )
            for k in range(0, end_idx + 1)
        ]

    dr.line(build_pts(a004, 210.0, n_frames - 1), fill=(24, 62, 74), width=1)
    dr.line(build_pts(a010, 65.0, n_frames - 1), fill=(78, 64, 30), width=1)

    hx0, hy0, hx1, hy1 = rx0, vh + 12, rx1, out_h - 12
    dr.rounded_rectangle([hx0, hy0, hx1, hy1], radius=10, fill=(14, 20, 31), outline=(44, 62, 86), width=1)
    dr.text((hx0 + 14, hy0 + 8), "LIVE LUMINANCE p_t(x) · Gold: > 0.010", fill=(205, 218, 232), font=f_sm_b)
    hpx0, hpy0, hpx1, hpy1 = hx0 + 44, hy0 + 32, hx1 - 14, hy1 - 26
    dr.rectangle([hpx0, hpy0, hpx1, hpy1], fill=(9, 13, 21), outline=(38, 54, 76), width=1)
    p_ymax = 0.030
    tau_y = int(round(hpy1 - (0.010 / p_ymax) * (hpy1 - hpy0 - 8) - 4))
    bar_w = (hpx1 - hpx0) / 256.0
    for pv in (0.00, 0.01, 0.02, 0.03):
        gy = int(round(hpy1 - (pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
        dr.line([(hpx0, gy), (hpx1, gy)], fill=(22, 33, 47), width=1)
        dr.text((hx0 + 6, gy - 6), f"{pv:.2f}", fill=(128, 146, 168), font=f_sm)

    out_mp4 = video_dir / "specimen31_beautiful_triptych_overlay.mp4"
    poster_png = video_dir / "specimen31_poster.png"
    enc = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
        "-i", str(tmp_wav), "-map", "0:v:0", "-map", "1:a:0",
        "-map_metadata", "-1",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k", "-shortest",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ], stdin=subprocess.PIPE)
    assert enc.stdin is not None

    poster_idx = int(round(2.8 * fps))  # Luminous 10-fold Girih star-rosette peak!

    for i in range(n_frames):
        rsec = i / float(fps)
        canvas = bg.copy()
        canvas.paste(Image.fromarray(frames[i]), (0, 0))
        d = ImageDraw.Draw(canvas)

        if rsec < 3.6:
            plbl, pcol = "I · MUGHAL GIRIH ROSETTE", (242, 196, 92)
        elif rsec < 6.0:
            plbl, pcol = "I · PUNJAB DOME GEOMETRY", (242, 196, 92)
        elif rsec < 12.0:
            plbl, pcol = "II · VIOLET MEADOW & SNOW", (195, 162, 255)
        elif rsec < 15.8:
            plbl, pcol = "III · STARSHIP FLIP BURN", (94, 218, 238)
        else:
            plbl, pcol = "III · MECHAZILLA CATCH!", (168, 226, 142)

        d.rounded_rectangle([12, 10, 328, 42], radius=8, fill=(10, 14, 22), outline=pcol, width=2)
        d.text((22, 19), f"{rsec:04.2f}s  ·  {plbl}", fill=pcol, font=f_sm_b)

        mom = int(a010[i] - a010[max(0, i - max(1, fps // 4))])
        vals = [
            (f"{a004[i]:>3d}", (94, 218, 238)),
            (f"{a010[i]:>3d}", (242, 196, 92)),
            (f"{mom:+3d}", (244, 106, 126) if mom >= 0 else (94, 218, 238)),
            (f"{h1_arr[i]:.2f} / {h2_arr[i]:.2f} b", (168, 226, 142)),
            (f"{m4_arr[i]:.4f}", (195, 162, 255)),
        ]
        for (bx0, by0, bx1, _), (val_s, col) in zip(kpi_boxes, vals):
            d.text((bx1 - 180, by0 + 15), val_s, fill=col, font=f_big if len(val_s) <= 7 else f_med)

        if i >= 1:
            d.line(build_pts(a004, 210.0, i), fill=(86, 212, 232), width=2)
            d.line(build_pts(a010, 65.0, i), fill=(242, 196, 92), width=3)
            d.line(build_pts(a020, 65.0, i), fill=(244, 106, 126), width=2)
        cur_x = int(round(px0 + (i / max(1, n_frames - 1)) * (px1 - px0)))
        d.line([(cur_x, py0), (cur_x, py1)], fill=(255, 255, 255), width=2)

        p_now = hists[i]
        for b in range(0, 256, 2):
            pv = float(max(p_now[b], p_now[b + 1]))
            if pv <= 0.0003:
                continue
            bx0 = int(hpx0 + b * bar_w)
            bx1 = max(bx0 + 1, int(hpx0 + (b + 2) * bar_w))
            bh_y = int(round(hpy1 - min(1.0, pv / p_ymax) * (hpy1 - hpy0 - 8) - 4))
            bar_col = (242, 196, 92) if pv > 0.010 else ((86, 198, 224) if pv > 0.004 else (58, 78, 102))
            d.rectangle([bx0, bh_y, bx1, hpy1 - 2], fill=bar_col)
        for dx in range(hpx0, hpx1, 10):
            d.line([(dx, tau_y), (min(hpx1, dx + 5), tau_y)], fill=(244, 106, 126), width=2)
        d.text((hpx1 - 150, tau_y - 16), f"tau=0.010 A={a010[i]}", fill=(244, 106, 126), font=f_sm_b)

        if i == poster_idx:
            canvas.save(poster_png, optimize=True)
        enc.stdin.write(canvas.tobytes())

    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("Specimen #31 ffmpeg encode failed")
    tmp_wav.unlink(missing_ok=True)

    # 4) SHA-256 Sealed GEM Causal Chiasm & Persistent Filtration Tomography (36 episodes)
    nexus_ep = int(np.argmin(np.abs(np.array(ep_times) - 12.0)))
    rep = write_chiasm_bundle(
        chiasm_dir,
        "specimen31_beautiful_triptych",
        title='SPECIMEN #31 · "BEAUTIFUL WITH A CAPITAL B" (ORIGINAL TRIPTYCH)',
        subtitle="Mughal Girih Geometry, Violet Poplar Snow & Starship 6-DOF Catch (18.0s · Original Score · 36 Ep)",
        nexus_label="FLIGHT IGNITION (0:12)",
        footer_label="Fieldglass Specimen #31 · 100% Original Pure-Math Architecture, Botanical & Aerospace Triptych",
        episodes_8=episodes_8,
        ep_a004=ep_a004,
        ep_a010=ep_a010,
        ep_times_s=ep_times,
        nexus_ep=nexus_ep,
        h1_mean=float(np.mean(h1_arr)),
        h2_mean=float(np.mean(h2_arr)),
        duration_sec=total_real_s,
        hud_prefix="sp31",
    )

    mp4_mb = round(out_mp4.stat().st_size / 1e6, 2)
    summary = {
        "specimen31": {
            "mp4_mb": mp4_mb,
            "duration_real_s": round(total_real_s, 2),
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
    build_specimen31()
