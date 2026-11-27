"""Deterministic builder for Milestone M1 Fieldglass Observatory R1 modules.

Generates self-contained interactive deliverables under:
  - docs/msdos/        (slug: msdos)
  - docs/flight-sim/   (slug: flight_sim)
  - docs/medical-sim/  (slug: medical_sim)  [STRICTLY SIMULATED / NON-CLINICAL]
  - docs/software/     (slug: software)

Run:
  PYTHONPATH=src /usr/bin/python3 examples/build_r1_observatory.py
"""

from __future__ import annotations

import hashlib
import html
import io
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fieldglass.observatory_r1 import (  # noqa: E402
    DISCLAIMER,
    EQUATION,
    FAT12_GEOMETRY,
    MSDOS8086Model,
    MSDOS_MEMORY_REGIONS,
    MSDOS_VIRTUAL_FILES,
    NON_CLINICAL_FLAGS,
    OBSERVATORY_PALETTE,
    SUMMARY_CONTRACT,
    FlightSim6DOF,
    MedicalSandboxModel,
    SoftwareObservatoryModel,
    seal_chiasm_report,
    strip_png_metadata,
)
from fieldglass.overlay import write_chiasm_svg  # noqa: E402
from fieldglass.plate import ink_to_braille_lines, save_braille_bundle  # noqa: E402


DOCS_DIR = ROOT / "docs"

# RGB palette tuples for crisp 1600x900 PIL preview cards
C_BG = (11, 15, 23)
C_PANEL = (18, 25, 38)
C_PANEL2 = (14, 20, 32)
C_BORDER = (42, 60, 85)
C_GOLD = (242, 196, 92)
C_CYAN = (94, 218, 240)
C_RUBY = (244, 106, 126)
C_GREEN = (140, 224, 148)
C_TEXT = (234, 239, 245)
C_MUTED = (147, 166, 190)


def _font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if mono:
        cands = (
            ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
            if bold
            else ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
        )
    else:
        cands = (
            ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
            if bold
            else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        )
    for p in cands:
        if Path(p).is_file():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _rasterize_svg_to_ink(svg_path: Path, width: int = 960) -> np.ndarray:
    """Rasterize an archival SVG via rsvg-convert stdout (zero temp files) into [0..1] ink strength."""
    raw_png = subprocess.check_output(
        ["rsvg-convert", "-w", str(width), "-f", "png", str(svg_path)]
    )
    with Image.open(io.BytesIO(raw_png)) as im:
        gray = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    # Archival parchment is ~0.95 luminance, ink is ~0.10..0.45
    ink = np.clip((0.93 - gray) / 0.72, 0.0, 1.0)
    return ink


def _save_braille_from_plate(plate_svg: Path, out_dir: Path, slug: str, title: str, subtitle: str) -> dict[str, str]:
    ink_map = _rasterize_svg_to_ink(plate_svg, width=960)
    lines = ink_to_braille_lines(ink_map, cols=64)
    bundle = save_braille_bundle(lines, out_dir, slug, title=title, subtitle=subtitle)
    strip_png_metadata(Path(bundle["preview_png"]))
    return bundle


# ---------------------------------------------------------------------------
# Archival Parchment Technical Plate SVGs (<slug>_plate.svg)
# ---------------------------------------------------------------------------

def _plate_svg_wrapper(title: str, subtitle: str, body_elems: list[str], footer_extra: str = "") -> str:
    esc = html.escape
    w, h = 1000, 720
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        '<rect x="0" y="0" width="1000" height="720" fill="#f6f1e4"/>',
        '<rect x="20" y="18" width="960" height="684" fill="none" stroke="#8c7f68" stroke-width="2"/>',
        '<rect x="28" y="26" width="944" height="668" fill="none" stroke="#c4b89f" stroke-width="1"/>',
        f'<text x="500" y="64" text-anchor="middle" font-family="serif" font-size="22" font-weight="bold" fill="#1b1916">{esc(title)}</text>',
        f'<text x="500" y="88" text-anchor="middle" font-family="serif" font-size="13" font-style="italic" fill="#524a3d">{esc(subtitle)}</text>',
        '<line x1="60" y1="104" x2="940" y2="104" stroke="#8c7f68" stroke-width="1.2"/>',
        *body_elems,
        '<line x1="60" y1="648" x2="940" y2="648" stroke="#8c7f68" stroke-width="1.2"/>',
        f'<text x="500" y="672" text-anchor="middle" font-family="monospace" font-size="12" fill="#1b1916">{esc(footer_extra or "FIELDGLASS ARCHIVAL TECHNICAL PLATE · 0 CLOUD TOKENS · executed=False")}</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def write_msdos_plate_svg(out_path: Path) -> Path:
    esc = html.escape
    elems: list[str] = [
        '<text x="64" y="136" font-family="monospace" font-size="15" font-weight="bold" fill="#1b1916">8086 REAL-MODE 1 MB + HMA MEMORY MAP (640 KB CONVENTIONAL = 655,360 B)</text>',
    ]
    # Proportional memory map bars
    y0 = 152
    for idx, reg in enumerate(MSDOS_MEMORY_REGIONS):
        by = y0 + idx * 36
        bar_w = max(24, int(round((reg["bytes"] / 614_400) * 320)))
        fill = "#1b1916" if reg["area"] == "Conventional" else ("#524a3d" if reg["area"] == "UMA" else "#786f5f")
        elems.append(f'<text x="64" y="{by + 18}" font-family="monospace" font-size="12" fill="#1b1916">{reg["start"]:05X}..{reg["end"]:05X}  {esc(reg["region"]):<18s}</text>')
        elems.append(f'<rect x="330" y="{by + 4}" width="{bar_w}" height="20" fill="{fill}" stroke="#1b1916" stroke-width="1"/>')
        elems.append(f'<text x="{342 + bar_w}" y="{by + 18}" font-family="monospace" font-size="12" fill="#1b1916">{reg["bytes"]:>7,d} B ({esc(reg["area"])})</text>')

    # FAT12 layout strip
    elems.extend([
        '<text x="64" y="544" font-family="monospace" font-size="15" font-weight="bold" fill="#1b1916">1.44 MB FAT12 DISK GEOMETRY (2,880 SECTORS x 512 B = 1,474,560 B)</text>',
        '<rect x="64" y="560" width="90" height="44" fill="#d9cfba" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="109" y="586" text-anchor="middle" font-family="monospace" font-size="11" fill="#1b1916">BOOT (1)</text>',
        '<rect x="154" y="560" width="140" height="44" fill="#c4b89f" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="224" y="586" text-anchor="middle" font-family="monospace" font-size="11" fill="#1b1916">FAT1 + FAT2 (18)</text>',
        '<rect x="294" y="560" width="140" height="44" fill="#d9cfba" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="364" y="586" text-anchor="middle" font-family="monospace" font-size="11" fill="#1b1916">ROOT DIR (14)</text>',
        '<rect x="434" y="560" width="500" height="44" fill="#1b1916" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="684" y="586" text-anchor="middle" font-family="monospace" font-size="12" fill="#f6f1e4">DATA CLUSTERS 2..2848 (2,847 SECTORS = 1,457,664 B)</text>',
    ])
    svg = _plate_svg_wrapper("MS-DOS 6.22 / 8086 ARCHITECTURE PLATE", "16-bit Real-Mode Registers, 640 KB TPA &amp; FAT12 Cluster Geometry", elems)
    out_path.write_text(svg, encoding="utf-8")
    return out_path


def write_flight_plate_svg(out_path: Path) -> Path:
    elems: list[str] = []
    # Draw six-pack circle schematics on archival parchment
    centers = [(210, 250), (490, 250), (770, 250), (210, 485), (490, 485), (770, 485)]
    labels = ["AIRSPEED (KT)", "ATTITUDE HORIZON", "ALTIMETER (FT)", "TURN / SLIP", "HEADING GYRO", "VSI (FPM)"]
    for (cx, cy), lbl in zip(centers, labels):
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="88" fill="#efe7d4" stroke="#1b1916" stroke-width="3"/>')
        elems.append(f'<circle cx="{cx}" cy="{cy}" r="76" fill="none" stroke="#786f5f" stroke-width="1.2"/>')
        elems.append(f'<text x="{cx}" y="{cy + 110}" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#1b1916">{lbl}</text>')
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            x1, y1 = cx + 66 * math.cos(rad), cy + 66 * math.sin(rad)
            x2, y2 = cx + 76 * math.cos(rad), cy + 76 * math.sin(rad)
            elems.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#1b1916" stroke-width="2"/>')
    # Attitude pitch bars inside center top gauge
    elems.extend([
        '<line x1="422" y1="250" x2="558" y2="250" stroke="#1b1916" stroke-width="3"/>',
        '<line x1="455" y1="224" x2="525" y2="224" stroke="#524a3d" stroke-width="2"/>',
        '<line x1="455" y1="276" x2="525" y2="276" stroke="#524a3d" stroke-width="2"/>',
        '<polyline points="462,250 482,250 490,260 498,250 518,250" fill="none" stroke="#1b1916" stroke-width="3"/>',
        # Needles on other 5 gauges
        '<line x1="210" y1="250" x2="262" y2="208" stroke="#1b1916" stroke-width="3.5"/>',
        '<line x1="770" y1="250" x2="770" y2="188" stroke="#1b1916" stroke-width="3.5"/>',
        '<line x1="210" y1="485" x2="255" y2="448" stroke="#1b1916" stroke-width="3.5"/>',
        '<polygon points="490,420 506,485 490,542 474,485" fill="none" stroke="#1b1916" stroke-width="2.5"/>',
        '<line x1="770" y1="485" x2="828" y2="452" stroke="#1b1916" stroke-width="3.5"/>',
    ])
    svg = _plate_svg_wrapper("6-DOF FLIGHT DYNAMICS &amp; SIX-PACK HUD PLATE", "ISA Atmosphere, Lift/Drag/Stall Model &amp; Bank-to-Turn Kinematics", elems)
    out_path.write_text(svg, encoding="utf-8")
    return out_path


def write_medical_plate_svg(out_path: Path) -> Path:
    elems: list[str] = [
        '<rect x="64" y="116" width="872" height="40" fill="#1b1916" rx="4"/>',
        '<text x="500" y="141" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold" fill="#f6f1e4">SIMULATED / EDUCATIONAL SANDBOX ONLY — NOT FOR CLINICAL, DIAGNOSTIC, OR PATIENT-CARE USE</text>',
    ]
    # 1. Synthetic ECG PQRST trace
    ecg_pts = []
    for i in range(220):
        t = i * 2.2 / 220.0
        v = MedicalSandboxModel.ecg_pqrst(t, hr_bpm=72.0)
        x = 74 + (i / 219.0) * 400
        y = 290 - v * 90.0
        ecg_pts.append(f"{x:.1f},{y:.1f}")
    elems.extend([
        '<rect x="64" y="172" width="424" height="196" fill="#efe7d4" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="78" y="194" font-family="monospace" font-size="13" font-weight="bold" fill="#1b1916">SYNTHETIC ECG (P-QRS-T GAUSSIAN SUM)</text>',
        f'<polyline points="{" ".join(ecg_pts)}" fill="none" stroke="#1b1916" stroke-width="2.8"/>',
    ])
    # 2. Beer-Lambert Pleth trace
    ppg_pts = []
    for i in range(220):
        t = i * 2.2 / 220.0
        d = MedicalSandboxModel.spo2_beer_lambert(0.55, t_sec=t, hr_bpm=72.0)
        x = 524 + (i / 219.0) * 400
        y = 330 - d["pleth_norm"] * 105.0
        ppg_pts.append(f"{x:.1f},{y:.1f}")
    elems.extend([
        '<rect x="512" y="172" width="424" height="196" fill="#efe7d4" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="526" y="194" font-family="monospace" font-size="13" font-weight="bold" fill="#1b1916">BEER-LAMBERT 660/940nm PLETH (SIMULATED)</text>',
        f'<polyline points="{" ".join(ppg_pts)}" fill="none" stroke="#1b1916" stroke-width="2.8"/>',
    ])
    # 3. Capnography waveform
    cap_pts = []
    for i in range(220):
        t = i * 8.5 / 220.0
        c = MedicalSandboxModel.capnography_waveform(t, rr_bpm=14.0, etco2_mmhg=38.0)
        x = 74 + (i / 219.0) * 400
        y = 580 - (c / 45.0) * 140.0
        cap_pts.append(f"{x:.1f},{y:.1f}")
    elems.extend([
        '<rect x="64" y="388" width="424" height="224" fill="#efe7d4" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="78" y="410" font-family="monospace" font-size="13" font-weight="bold" fill="#1b1916">SYNTHETIC CAPNOGRAPHY (4-PHASE CO2)</text>',
        f'<polyline points="{" ".join(cap_pts)}" fill="none" stroke="#1b1916" stroke-width="2.8"/>',
    ])
    # 4. Ventilator P-V loop
    pv = MedicalSandboxModel.ventilator_pv_loop(compliance_ml_cmh2o=50.0, resistance_cmh2o_l_s=8.0, vt_ml=480.0, peep_cmh2o=5.0)
    pv_pts = [
        f"{544 + (pt['pressure_cmh2o'] / 24.0) * 350:.1f},{585 - (pt['volume_ml'] / 540.0) * 150:.1f}"
        for pt in pv["points"]
    ]
    elems.extend([
        '<rect x="512" y="388" width="424" height="224" fill="#efe7d4" stroke="#1b1916" stroke-width="1.5"/>',
        '<text x="526" y="410" font-family="monospace" font-size="13" font-weight="bold" fill="#1b1916">VENTILATOR P-V LOOP (P = PEEP + V/C + R*F)</text>',
        f'<polygon points="{" ".join(pv_pts)}" fill="none" stroke="#1b1916" stroke-width="2.8"/>',
    ])
    svg = _plate_svg_wrapper(
        "BIOMEDICAL PHYSICS &amp; OPTICS SANDBOX PLATE",
        "Synthetic Waveforms &amp; Beer-Lambert Attenuation (Educational Only)",
        elems,
        footer_extra="clinical_use=false | educational_simulation_only=true | clinical_certification_claimed=false",
    )
    out_path.write_text(svg, encoding="utf-8")
    return out_path


def write_software_plate_svg(out_path: Path) -> Path:
    esc = html.escape
    elems: list[str] = [
        '<text x="64" y="138" font-family="monospace" font-size="15" font-weight="bold" fill="#1b1916">FIELDGLASS 6-STAGE DETERMINISTIC PIPELINE &amp; WIN7-TO-MODERN BOUNDARY</text>',
    ]
    for idx, st in enumerate(SoftwareObservatoryModel.PIPELINE_STAGES):
        col = idx % 2
        row = idx // 2
        x = 64 + col * 448
        y = 160 + row * 94
        elems.extend([
            f'<rect x="{x}" y="{y}" width="424" height="74" fill="#efe7d4" stroke="#1b1916" stroke-width="2" rx="4"/>',
            f'<text x="{x + 14}" y="{y + 24}" font-family="monospace" font-size="13" font-weight="bold" fill="#1b1916">{esc(st["stage"])}</text>',
            f'<text x="{x + 14}" y="{y + 44}" font-family="monospace" font-size="11" fill="#524a3d">{esc(st["module"])}</text>',
            f'<text x="{x + 14}" y="{y + 62}" font-family="monospace" font-size="11" fill="#1b1916">{esc(st["contract"])}</text>',
        ])
    elems.extend([
        '<rect x="64" y="458" width="872" height="164" fill="#1b1916" rx="4"/>',
        '<text x="84" y="490" font-family="monospace" font-size="14" font-weight="bold" fill="#f6f1e4">KLOSTER SUPERLEVEL-SET &amp; SHA-256 INTEGRITY CONTRACT</text>',
        '<text x="84" y="520" font-family="monospace" font-size="13" fill="#f6f1e4">A_tau(p) = |{x in X : p(x) &gt; tau}| = sum_{x in X} 1[p(x) &gt; tau]  (strict inequality: p == tau excluded)</text>',
        '<text x="84" y="550" font-family="monospace" font-size="12" fill="#d9cfba">Win7 Target: ES5 + IE8-IE11/HTA + Python 3.7/3.8 stdlib-only loopback (127.0.0.1)</text>',
        '<text x="84" y="576" font-family="monospace" font-size="12" fill="#d9cfba">Modern Target: Python 3.14 + NumPy/PIL/Matplotlib + HTML5 Canvas + pure-JS/WebCrypto SHA-256</text>',
        '<text x="84" y="602" font-family="monospace" font-size="12" fill="#f6f1e4">Invariants: executed=false | sentience_claimed=false | tokens_used=0 | zero external CDNs</text>',
    ])
    svg = _plate_svg_wrapper("SOFTWARE SYSTEMS &amp; OBSERVATORY ARCHITECTURE PLATE", "Deterministic Pipeline, Kloster A_tau(p) &amp; Win7-Era Compatibility Matrix", elems)
    out_path.write_text(svg, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Crisp 1600x900 Slide-Ready Preview PNGs (zero GPS/EXIF metadata)
# ---------------------------------------------------------------------------

def _new_preview_canvas(title: str, subtitle: str, badge: str, *, accent: tuple[int, int, int] = C_CYAN) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (1600, 900), C_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([24, 20, 1576, 118], radius=14, fill=C_PANEL, outline=accent, width=2)
    d.text((48, 34), title, fill=C_GOLD, font=_font(30, bold=True))
    d.text((48, 76), subtitle, fill=C_MUTED, font=_font(18))
    d.rounded_rectangle([1210, 36, 1552, 98], radius=10, fill=C_PANEL2, outline=C_RUBY, width=2)
    d.text((1230, 56), badge, fill=C_CYAN, font=_font(17, bold=True, mono=True))
    d.text((48, 864), f"Fieldglass Observatory R1  |  {EQUATION}  |  tokens_used=0  |  executed=False", fill=C_MUTED, font=_font(14, mono=True))
    return img, d


def render_msdos_preview(out_png: Path, msdos: MSDOS8086Model, telem: dict[str, Any]) -> Path:
    img, d = _new_preview_canvas(
        "MS-DOS 6.22 & 8086 REAL-MODE EDUCATIONAL SIMULATOR",
        "16-bit Registers, 640 KB Conventional RAM, 1.44 MB FAT12 Geometry & COMMAND.COM",
        f"A_0.10 = {telem['chiasm_nexus']['future_accessible_volume']} | {telem['chiasm_nexus']['presence_glyph']}",
        accent=C_CYAN,
    )
    # Left panel: COMMAND.COM terminal
    preview_dos = MSDOS8086Model()
    step0 = preview_dos.step_instruction()
    regs = step0["registers"]
    d.rounded_rectangle([24, 140, 820, 844], radius=12, fill=(7, 10, 16), outline=C_BORDER, width=2)
    d.text((48, 158), "C:\\> COMMAND.COM — VIRTUAL SESSION", fill=C_GOLD, font=_font(18, bold=True, mono=True))
    term_lines = [
        "C:\\> VER",
        "MS-DOS Version 6.22 (8086 Educational Real-Mode Model)",
        "",
        "C:\\> MEM",
        "Memory Type        Total       Used       Free",
        "Conventional         640K        40K       600K  (614,400 bytes)",
        "Upper                384K       192K       192K  (393,216 bytes UMA)",
        "Extended (HMA)        64K        47K        17K  (65,520 bytes HMA)",
        "",
        "C:\\> CHKDSK",
        "  1,474,560 bytes total disk space (FAT12 2880 sectors x 512 B)",
        "     78,912 bytes in 2 hidden files (IO.SYS, MSDOS.SYS)",
        "     84,765 bytes in 6 user files",
        "  1,310,883 bytes available on disk",
        "",
        "C:\\> STEP",
        f"STEP #{step0['step_index']}: {step0['instruction']}  (CS:IP={regs['CS']:04X}:{regs['IP']:04X}  phys={step0['phys_cs_ip']})",
        f"AX={regs['AX']:04X}  BX={regs['BX']:04X}  CX={regs['CX']:04X}  DX={regs['DX']:04X}  SP={regs['SP']:04X}  FLAGS={regs['FLAGS']:04X} [IF={step0['flags']['IF']}]",
    ]
    for i, ln in enumerate(term_lines):
        col = C_CYAN if ln.startswith("C:\\>") else (C_GREEN if "600K" in ln or "available" in ln else C_TEXT)
        d.text((48, 200 + i * 32), ln, fill=col, font=_font(16, mono=True))

    # Right top: 8086 registers
    d.rounded_rectangle([844, 140, 1576, 440], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((868, 158), "8086 16-BIT REGISTER & FLAG STATE", fill=C_CYAN, font=_font(18, bold=True, mono=True))
    reg_pairs = [
        ("AX", regs["AX"]), ("BX", regs["BX"]), ("CX", regs["CX"]), ("DX", regs["DX"]),
        ("SI", regs["SI"]), ("DI", regs["DI"]), ("BP", regs["BP"]), ("SP", regs["SP"]),
        ("CS", regs["CS"]), ("DS", regs["DS"]), ("ES", regs["ES"]), ("SS", regs["SS"]),
        ("IP", regs["IP"]), ("FLAGS", regs["FLAGS"]),
    ]
    for idx, (rk, rv) in enumerate(reg_pairs):
        col_i = idx % 4
        row_i = idx // 4
        rx = 868 + col_i * 172
        ry = 204 + row_i * 52
        d.rounded_rectangle([rx, ry, rx + 158, ry + 40], radius=6, fill=C_PANEL2, outline=C_BORDER, width=1)
        d.text((rx + 10, ry + 10), f"{rk:<5s} {rv:04X}h", fill=C_GOLD if rk in ("AX", "IP", "FLAGS") else C_TEXT, font=_font(15, bold=True, mono=True))

    # Right bottom: 640 KB Memory Map
    d.rounded_rectangle([844, 462, 1576, 844], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((868, 480), "640 KB CONVENTIONAL + UMA + HMA MEMORY MAP", fill=C_CYAN, font=_font(18, bold=True, mono=True))
    for i, reg in enumerate(MSDOS_MEMORY_REGIONS[:8]):
        ry = 522 + i * 38
        bw = max(24, int(round((reg["bytes"] / 614_400) * 260)))
        col = C_CYAN if reg["area"] == "Conventional" else C_GOLD
        d.text((868, ry + 4), f"{reg['start']:05X} {reg['region']:<16s}", fill=C_TEXT, font=_font(15, mono=True))
        d.rectangle([1148, ry + 4, 1148 + bw, ry + 24], fill=col)
        d.text((1420, ry + 4), f"{reg['bytes']:>7,d} B", fill=C_MUTED, font=_font(14, mono=True))

    img.save(out_png, format="PNG", optimize=True)
    return strip_png_metadata(out_png)


def render_flight_preview(out_png: Path, telem: dict[str, Any]) -> Path:
    img, d = _new_preview_canvas(
        "6-DOF FLIGHT DYNAMICS & KLOSTER TELEMETRY HUD",
        "ISA Atmosphere, Stall-Bounded Lift/Drag, Bank-to-Turn Kinematics & Six-Pack Gauges",
        f"A_0.10 = {telem['chiasm_nexus']['future_accessible_volume']} | {telem['chiasm_nexus']['presence_glyph']}",
        accent=C_GOLD,
    )
    # Left: Artificial Horizon
    d.rounded_rectangle([24, 140, 760, 844], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((48, 158), "ARTIFICIAL HORIZON & SIX-PACK READOUT", fill=C_CYAN, font=_font(18, bold=True, mono=True))
    cx, cy, rad = 392, 440, 220
    # Sky & ground half-circles
    d.pieslice([cx - rad, cy - rad, cx + rad, cy + rad], 180, 360, fill=(32, 92, 156))
    d.pieslice([cx - rad, cy - rad, cx + rad, cy + rad], 0, 180, fill=(108, 72, 44))
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=C_GOLD, width=4)
    d.line([(cx - rad, cy), (cx + rad, cy)], fill=C_TEXT, width=3)
    d.line([(cx - 75, cy - 38), (cx + 75, cy - 38)], fill=C_TEXT, width=2)
    d.line([(cx - 75, cy + 38), (cx + 75, cy + 38)], fill=C_TEXT, width=2)
    d.line([(cx - 80, cy), (cx - 24, cy), (cx, cy + 18), (cx + 24, cy), (cx + 80, cy)], fill=C_GOLD, width=5)

    hud_kpis = [
        ("AIRSPEED", "108.9 kt"),
        ("ALTITUDE", "4,921 ft"),
        ("VSI", "+410 fpm"),
        ("HEADING", "090 deg"),
        ("PITCH / ROLL", "+3.0 / +0.0"),
        ("G-LOAD / AoA", "1.00g / 1.8°"),
    ]
    for idx, (k, v) in enumerate(hud_kpis):
        bx = 48 + (idx % 3) * 234
        by = 696 + (idx // 3) * 68
        d.rounded_rectangle([bx, by, bx + 220, by + 56], radius=8, fill=C_PANEL2, outline=C_BORDER, width=1)
        d.text((bx + 12, by + 8), k, fill=C_MUTED, font=_font(12, mono=True))
        d.text((bx + 12, by + 26), v, fill=C_GOLD, font=_font(18, bold=True, mono=True))

    # Right: Sortie Trajectory & Kloster A_tau
    d.rounded_rectangle([784, 140, 1576, 844], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((808, 158), "16-EPISODE SORTIE TRAJECTORY & KLOSTER A_tau(p_t)", fill=C_CYAN, font=_font(18, bold=True, mono=True))
    traj = telem["trajectory"]
    gx0, gy0, gx1, gy1 = 830, 220, 1536, 520
    d.rectangle([gx0, gy0, gx1, gy1], fill=C_PANEL2, outline=C_BORDER, width=1)
    alts = [pt["alt_ft"] for pt in traj]
    min_a, max_a = min(alts) - 100.0, max(alts) + 100.0
    alt_pts = [
        (int(gx0 + (i / 15.0) * (gx1 - gx0)), int(gy1 - ((a - min_a) / max(1.0, max_a - min_a)) * (gy1 - gy0 - 30) - 15))
        for i, a in enumerate(alts)
    ]
    d.line(alt_pts, fill=C_CYAN, width=4)
    d.text((gx0 + 14, gy0 + 12), f"Altitude Profile ({min(alts):.0f} ft .. {max(alts):.0f} ft)", fill=C_CYAN, font=_font(15, mono=True))

    tx0, ty0, tx1, ty1 = 830, 560, 1536, 810
    d.rectangle([tx0, ty0, tx1, ty1], fill=C_PANEL2, outline=C_BORDER, width=1)
    a010 = telem["per_ep_a010"]
    a_pts = [
        (int(tx0 + (i / 15.0) * (tx1 - tx0)), int(ty1 - (v / 8.0) * (ty1 - ty0 - 30) - 15))
        for i, v in enumerate(a010)
    ]
    d.line(a_pts, fill=C_GOLD, width=4)
    d.text((tx0 + 14, ty0 + 12), f"Kloster A_0.10(p_t) | EI={telem['chiasm_nexus']['effective_information_bits']:.4f} bits", fill=C_GOLD, font=_font(15, mono=True))

    img.save(out_png, format="PNG", optimize=True)
    return strip_png_metadata(out_png)


def render_medical_preview(out_png: Path, telem: dict[str, Any]) -> Path:
    img, d = _new_preview_canvas(
        "MEDICAL EQUIPMENT PHYSICS & OPTICS SANDBOX",
        "Synthetic ECG, Beer-Lambert SpO2, Capnography, Ventilator P-V & Infusion Math",
        "NON-CLINICAL SIM",
        accent=C_RUBY,
    )
    # Prominent top non-clinical banner
    d.rounded_rectangle([24, 130, 1576, 184], radius=10, fill=(108, 22, 34), outline=C_RUBY, width=3)
    d.text(
        (56, 146),
        "SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL USE   (clinical_use=false | clinical_certification_claimed=false)",
        fill=(255, 232, 232),
        font=_font(20, bold=True, mono=True),
    )

    # 4 waveform panels
    panels = [
        (24, 202, 788, 512, "SYNTHETIC ECG P-QRS-T (72 BPM, LEAD II mV)"),
        (812, 202, 1576, 512, "BEER-LAMBERT 660/940nm SpO2 PLETH (R=0.55 -> 96.2%)"),
        (24, 530, 788, 844, "SYNTHETIC CAPNOGRAPHY (4-PHASE, EtCO2=38 mmHg)"),
        (812, 530, 1576, 844, "VENTILATOR P-V LOOP (C=50 mL/cmH2O, PEEP=5)"),
    ]
    for x0, y0, x1, y1, title in panels:
        d.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
        d.text((x0 + 20, y0 + 16), title, fill=C_CYAN, font=_font(16, bold=True, mono=True))

    # ECG points
    ecg_pts = []
    for i in range(260):
        t = i * 2.2 / 260.0
        v = MedicalSandboxModel.ecg_pqrst(t, hr_bpm=72.0)
        ecg_pts.append((int(48 + (i / 259.0) * 710), int(410 - v * 120.0)))
    d.line(ecg_pts, fill=C_GREEN, width=3)

    # Pleth points
    ppg_pts = []
    for i in range(260):
        t = i * 2.2 / 260.0
        v = MedicalSandboxModel.spo2_beer_lambert(0.55, t_sec=t, hr_bpm=72.0)["pleth_norm"]
        ppg_pts.append((int(836 + (i / 259.0) * 710), int(460 - v * 165.0)))
    d.line(ppg_pts, fill=C_CYAN, width=3)

    # Capno points
    cap_pts = []
    for i in range(260):
        t = i * 8.5 / 260.0
        v = MedicalSandboxModel.capnography_waveform(t, rr_bpm=14.0, etco2_mmhg=38.0)
        cap_pts.append((int(48 + (i / 259.0) * 710), int(800 - (v / 45.0) * 190.0)))
    d.line(cap_pts, fill=C_GOLD, width=3)

    # P-V loop
    pv = MedicalSandboxModel.ventilator_pv_loop()
    pv_pts = [
        (int(880 + (pt["pressure_cmh2o"] / 24.0) * 560), int(800 - (pt["volume_ml"] / 540.0) * 200.0))
        for pt in pv["points"]
    ]
    pv_pts.append(pv_pts[0])
    d.line(pv_pts, fill=C_RUBY, width=3)

    img.save(out_png, format="PNG", optimize=True)
    return strip_png_metadata(out_png)


def render_software_preview(out_png: Path, telem: dict[str, Any]) -> Path:
    img, d = _new_preview_canvas(
        "SOFTWARE SYSTEMS & FIELDGLASS ARCHITECTURE OBSERVATORY",
        "6-Stage Pipeline, Strict A_tau(p) > tau Superlevel Sets, SHA-256 Seals & Win7 Matrix",
        f"A_0.10 = {telem['chiasm_nexus']['future_accessible_volume']} | SHA-256",
        accent=C_CYAN,
    )
    # Left: 6-stage pipeline cards
    d.rounded_rectangle([24, 140, 810, 844], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((48, 158), "FIELDGLASS 6-STAGE DETERMINISTIC PIPELINE", fill=C_GOLD, font=_font(18, bold=True, mono=True))
    for idx, st in enumerate(SoftwareObservatoryModel.PIPELINE_STAGES):
        by = 204 + idx * 102
        d.rounded_rectangle([48, by, 786, by + 86], radius=8, fill=C_PANEL2, outline=C_BORDER, width=1)
        d.text((64, by + 12), st["stage"], fill=C_CYAN, font=_font(16, bold=True, mono=True))
        d.text((64, by + 38), st["module"], fill=C_GOLD, font=_font(14, mono=True))
        d.text((64, by + 60), st["contract"], fill=C_TEXT, font=_font(14))

    # Right: Win7 vs Modern + Tomography scores
    d.rounded_rectangle([834, 140, 1576, 510], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((858, 158), "WIN7-ERA VS. MODERN OBSERVATORY MATRIX", fill=C_CYAN, font=_font(18, bold=True, mono=True))
    for idx, row in enumerate(SoftwareObservatoryModel.WIN7_MODERN_MATRIX):
        ry = 204 + idx * 48
        d.text((858, ry), f"{row['layer']}: {row['win7_target']}", fill=C_GOLD, font=_font(12, mono=True))
        d.text((858, ry + 18), f"  Modern -> {row['modern_observatory']}", fill=C_MUTED, font=_font(12, mono=True))

    d.rounded_rectangle([834, 532, 1576, 844], radius=12, fill=C_PANEL, outline=C_BORDER, width=2)
    d.text((858, 550), "PERSISTENT FILTRATION PERSISTENCE P(x)", fill=C_CYAN, font=_font(18, bold=True, mono=True))
    scores = sorted(telem["persistent_filtration_tomography"]["persistence_scores"].items(), key=lambda kv: -kv[1])
    for idx, (st_name, sc) in enumerate(scores):
        ry = 592 + idx * 29
        bw = max(12, int(min(1.0, sc / 0.30) * 320))
        d.text((858, ry), f"{st_name:<14s}", fill=C_TEXT, font=_font(14, mono=True))
        d.rectangle([1018, ry + 2, 1018 + bw, ry + 18], fill=C_RUBY if sc >= 0.14 else C_CYAN)
        d.text((1350, ry), f"P={sc:.3f}", fill=C_GOLD, font=_font(14, mono=True))

    img.save(out_png, format="PNG", optimize=True)
    return strip_png_metadata(out_png)


# ---------------------------------------------------------------------------
# Self-Contained Interactive HTML5 Pages (Zero External CDNs)
# ---------------------------------------------------------------------------

_BASE_CSS = """
  :root {
    --bg: #0b0f17;
    --panel: #121926;
    --panel2: #0e1420;
    --border: #2a3c55;
    --gold: #f2c45c;
    --cyan: #5edaf0;
    --ruby: #f46a7e;
    --green: #8ce094;
    --text: #eaeff5;
    --muted: #93a6be;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
    padding: 18px 14px 64px;
  }
  .wrap { max-width: 1140px; margin: 0 auto; }
  header {
    background: linear-gradient(145deg, #162133, #0f1622);
    border: 1.5px solid var(--ruby);
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 18px;
  }
  .kicker {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.76rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ruby);
    margin-bottom: 4px;
  }
  h1 { margin: 0 0 6px; font-size: clamp(1.35rem, 3vw, 1.95rem); color: var(--gold); }
  .sub { font-size: 0.9rem; color: var(--muted); margin: 0 0 12px; }
  .eq {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.86rem;
    color: var(--cyan);
    background: #0a101a;
    border: 1px solid #243852;
    border-radius: 8px;
    padding: 7px 12px;
    display: inline-block;
    margin: 4px 0 10px;
  }
  .nav-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
  a.btn, button.btn {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 8px;
    border: 1px solid #385070;
    background: #172233;
    color: var(--text);
    text-decoration: none;
    font-size: 0.82rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    cursor: pointer;
  }
  a.btn:hover, button.btn:hover { border-color: var(--cyan); color: var(--cyan); }
  button.btn.accent, a.btn.accent { border-color: var(--gold); color: var(--gold); }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 18px;
  }
  .card h2, .card h3 {
    margin: 0 0 8px;
    color: var(--cyan);
    font-size: 1.05rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  .badge {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 999px;
    background: #1c293d;
    color: var(--gold);
    border: 1px solid #354c6b;
  }
  .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
  .grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
  th, td { border-bottom: 1px solid #223248; padding: 6px 8px; text-align: left; }
  th { color: var(--gold); font-family: ui-monospace, monospace; font-size: 0.78rem; }
  canvas, img.resp { width: 100%; height: auto; border-radius: 10px; border: 1px solid #223248; background: #070a10; display: block; }
  input[type="range"], input[type="text"], input[type="number"], textarea {
    background: #0a101a;
    color: var(--text);
    border: 1px solid #354c6b;
    border-radius: 6px;
    padding: 6px 9px;
    font-family: ui-monospace, monospace;
  }
  .kpi {
    background: var(--panel2);
    border: 1px solid #243852;
    border-radius: 10px;
    padding: 10px 12px;
  }
  .kpi .lbl { font-size: 0.72rem; color: var(--muted); font-family: ui-monospace, monospace; text-transform: uppercase; }
  .kpi .val { font-size: 1.18rem; color: var(--gold); font-family: ui-monospace, monospace; font-weight: 700; }
  .disclaimer-banner {
    background: linear-gradient(90deg, #5c1320, #3a121b);
    border: 2px solid var(--ruby);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: #ffe8ea;
    font-weight: 700;
  }
  footer { margin-top: 24px; color: var(--muted); font-size: 0.8rem; font-family: ui-monospace, monospace; text-align: center; }
"""


def _html_shell(title: str, kicker: str, subtitle: str, slug: str, extra_head: str, body_html: str, script_js: str) -> str:
    esc = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," />
<title>{esc(title)} · Fieldglass Observatory</title>
<style>
{_BASE_CSS}
{extra_head}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kicker">{esc(kicker)}</div>
    <h1>{esc(title)}</h1>
    <p class="sub">{esc(subtitle)}</p>
    <div class="eq">{esc(EQUATION)}</div>
    <div class="nav-links">
      <a class="btn" href="../index.html">Observatory Home</a>
      <a class="btn" href="./{slug}_chiasm.svg">Causal Chiasm SVG</a>
      <a class="btn" href="./{slug}_plate.svg">Archival Plate SVG</a>
      <a class="btn" href="./{slug}_braille_preview.png">2x4 Braille PNG</a>
      <a class="btn" href="./chiasm_report.json">Chiasm JSON</a>
      <a class="btn" href="./summary.json">Summary JSON</a>
    </div>
  </header>
  {body_html}
  <footer>Fieldglass Observatory R1 · 0 cloud tokens ($0.00) · executed=false · sentience_claimed=false</footer>
</div>
<script>
{script_js}
</script>
</body>
</html>
"""


def build_msdos_html(telem: dict[str, Any]) -> str:
    data_blob = json.dumps(
        {
            "memory": MSDOS_MEMORY_REGIONS,
            "fat12": FAT12_GEOMETRY,
            "files": MSDOS_VIRTUAL_FILES,
            "episodes": telem["per_episode"],
            "chiasm": telem["chiasm_nexus"],
        }
    )
    body = """
<div class="grid2">
  <div class="card">
    <h3>COMMAND.COM Interactive Shell <span class="badge">MS-DOS 6.22 · 8086</span></h3>
    <pre id="dosTerm" class="mono" style="background:#06090f;border:1px solid #243852;border-radius:10px;padding:12px;height:320px;overflow:auto;font-size:0.82rem;margin:0 0 10px;color:#d6e4f2;"></pre>
    <div style="display:flex;gap:8px;margin-bottom:10px;">
      <span class="mono" style="padding:7px 4px;color:var(--gold);">C:\\&gt;</span>
      <input id="dosInput" type="text" value="HELP" style="flex:1;" aria-label="MS-DOS Command" />
      <button id="dosRunBtn" class="btn accent" type="button">Run</button>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:6px;">
      <button class="btn dos-quick" data-cmd="DIR" type="button">DIR</button>
      <button class="btn dos-quick" data-cmd="MEM" type="button">MEM</button>
      <button class="btn dos-quick" data-cmd="CHKDSK" type="button">CHKDSK</button>
      <button class="btn dos-quick" data-cmd="TYPE CONFIG.SYS" type="button">TYPE CONFIG.SYS</button>
      <button class="btn dos-quick" data-cmd="TYPE FIELDGLS.TXT" type="button">TYPE FIELDGLS.TXT</button>
      <button class="btn dos-quick" data-cmd="AUTOEXEC.BAT" type="button">AUTOEXEC.BAT</button>
      <button class="btn dos-quick" data-cmd="STEP" type="button">STEP 8086</button>
      <button class="btn dos-quick" data-cmd="VER" type="button">VER</button>
      <button class="btn dos-quick" data-cmd="CLS" type="button">CLS</button>
    </div>
  </div>
  <div class="card">
    <h3>16-Bit 8086 Registers &amp; Physical Address <span class="badge" id="a20Badge">A20: ON</span></h3>
    <div id="regGrid" class="grid3" style="margin-bottom:10px;"></div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px;">
      <button id="stepBtn" class="btn accent" type="button">Step Micro-Program</button>
      <button id="a20Btn" class="btn" type="button">Toggle A20 Gate</button>
      <span id="physReadout" class="mono" style="font-size:0.82rem;color:var(--cyan);">CS:IP phys = 0x08100</span>
    </div>
    <div id="flagsReadout" class="mono" style="font-size:0.8rem;color:var(--gold);background:#0a101a;padding:8px 10px;border-radius:8px;border:1px solid #243852;"></div>
  </div>
</div>

<div class="grid2">
  <div class="card">
    <h3>640 KB Conventional + UMA + HMA Memory Map <span class="badge">1,048,576 B Real Mode</span></h3>
    <div id="memBars"></div>
  </div>
  <div class="card">
    <h3>1.44 MB FAT12 Geometry &amp; Kloster Telemetry <span class="badge" id="dosAtauBadge">A_0.10</span></h3>
    <div id="fat12Box" class="mono" style="font-size:0.82rem;margin-bottom:10px;"></div>
    <canvas id="dosTelemCanvas" width="520" height="190"></canvas>
  </div>
</div>
"""
    script = f"""
(function() {{
  var DATA = {data_blob};
  var state = {{
    a20: true,
    pc: 0,
    regs: {{AX:0x0000,BX:0x0000,CX:0x00FF,DX:0x0000,SI:0x0100,DI:0x0200,BP:0x0000,SP:0xFFFE,CS:0x0800,DS:0x0800,ES:0x0800,SS:0x0800,IP:0x0100,FLAGS:0x0202}}
  }};
  var prog = [
    ["MOV AX, 0900h", 3],
    ["MOV DX, 0140h", 3],
    ["INT 21h", 2],
    ["ADD AX, 002Ah", 3],
    ["CMP AX, 092Ah", 3],
    ["NOP", 1]
  ];
  function hex4(v) {{ return (v & 0xFFFF).toString(16).toUpperCase().padStart(4, "0"); }}
  function physAddr(seg, off) {{
    var raw = ((seg & 0xFFFF) << 4) + (off & 0xFFFF);
    return state.a20 ? raw : (raw & 0xFFFFF);
  }}
  function renderRegs() {{
    var grid = document.getElementById("regGrid");
    grid.innerHTML = "";
    Object.keys(state.regs).forEach(function(k) {{
      var d = document.createElement("div");
      d.className = "kpi";
      d.innerHTML = '<div class="lbl">' + k + '</div><div class="val">' + hex4(state.regs[k]) + 'h</div>';
      grid.appendChild(d);
    }});
    var f = state.regs.FLAGS;
    var masks = [["CF",1],["PF",4],["AF",16],["ZF",64],["SF",128],["TF",256],["IF",512],["DF",1024],["OF",2048]];
    document.getElementById("flagsReadout").textContent = "FLAGS: " + masks.map(function(m) {{ return m[0] + "=" + ((f & m[1]) ? 1 : 0); }}).join("  ");
    var p = physAddr(state.regs.CS, state.regs.IP);
    document.getElementById("physReadout").textContent = "CS:IP phys = 0x" + p.toString(16).toUpperCase().padStart(5, "0") + " | FFFF:0020 = 0x" + physAddr(0xFFFF, 0x0020).toString(16).toUpperCase().padStart(5, "0");
    document.getElementById("a20Badge").textContent = "A20: " + (state.a20 ? "ON" : "OFF");
  }}
  function updateArithFlags(result16, carry, overflow) {{
    var val = result16 & 0xFFFF;
    var flags = state.regs.FLAGS & ~0x08C5;
    if (carry) flags |= 0x0001;
    if (val === 0) flags |= 0x0040;
    if (val & 0x8000) flags |= 0x0080;
    var low = val & 0xFF;
    var ones = 0;
    for (var b = 0; b < 8; b++) {{ if ((low >> b) & 1) ones++; }}
    if (ones % 2 === 0) flags |= 0x0004;
    if (overflow) flags |= 0x0800;
    state.regs.FLAGS = flags & 0xFFFF;
  }}
  function stepCpu() {{
    var idx = state.pc % prog.length;
    if (idx === 0) state.regs.AX = 0x0900;
    else if (idx === 1) state.regs.DX = 0x0140;
    else if (idx === 2) state.regs.AX = (state.regs.AX & 0xFF00) | 0x0024;
    else if (idx === 3) {{
      var a = state.regs.AX;
      var r = a + 0x002A;
      state.regs.AX = r & 0xFFFF;
      updateArithFlags(r, r > 0xFFFF, false);
    }} else if (idx === 4) {{
      var a2 = state.regs.AX;
      var diff = (a2 - 0x092A) & 0xFFFF;
      updateArithFlags(diff, a2 < 0x092A, false);
    }}
    var ipOff = 0;
    for (var i = 0; i <= idx; i++) ipOff += prog[i][1];
    state.regs.IP = (0x0100 + ipOff) & 0xFFFF;
    state.pc += 1;
    renderRegs();
    return "STEP #" + idx + ": " + prog[idx][0] + " -> AX=" + hex4(state.regs.AX) + "h IP=" + hex4(state.regs.IP) + "h";
  }}
  var term = document.getElementById("dosTerm");
  function appendTerm(lines) {{
    term.textContent += (term.textContent ? "\\n" : "") + lines.join("\\n");
    term.scrollTop = term.scrollHeight;
  }}
  function runCmd(raw) {{
    var line = (raw || "").trim();
    if (!line) return;
    var parts = line.split(/\\s+/);
    var verb = parts[0].toUpperCase();
    var arg = (parts[1] || "").toUpperCase();
    if (verb === "CLS") {{ term.textContent = ""; return; }}
    appendTerm(["C:\\\\>" + line]);
    if (verb === "VER") appendTerm(["MS-DOS Version 6.22 (8086 Educational Real-Mode Model)"]);
    else if (verb === "HELP") appendTerm(["Commands: DIR, MEM, CHKDSK, TYPE <FILE>, VER, AUTOEXEC.BAT, STEP, REGS, CLS, HELP"]);
    else if (verb === "DIR") {{
      var vis = DATA.files.filter(function(f) {{ return !f.hidden; }});
      var total = DATA.files.reduce(function(s, f) {{ return s + f.bytes; }}, 0);
      var out = [" Volume in drive C is FIELDGLS622", " Directory of C:\\\\"];
      vis.forEach(function(f) {{ out.push("  " + f.name.padEnd(14, " ") + String(f.bytes).padStart(9, " ") + "  " + f.date + "  [" + f.attr + "]"); }});
      out.push("  " + vis.length + " file(s) visible, " + (DATA.fat12.total_bytes - total).toLocaleString() + " bytes free");
      appendTerm(out);
    }} else if (verb === "MEM") {{
      appendTerm([
        "Memory Type        Total       Used       Free",
        "Conventional         640K        40K       600K  (614,400 bytes)",
        "Upper                384K       192K       192K  (393,216 bytes UMA)",
        "Extended (XMS/HMA)    64K        47K        17K  (65,520 bytes HMA)"
      ]);
    }} else if (verb === "CHKDSK") {{
      appendTerm([
        "Volume Serial Number is 1994-0622",
        "  1,474,560 bytes total disk space (2880 sectors x 512 B)",
        "     78,912 bytes in 2 hidden files",
        "     84,765 bytes in 6 user files",
        "  1,310,883 bytes available on disk",
        "    655,360 total bytes memory / 614,400 bytes free"
      ]);
    }} else if (verb === "TYPE") {{
      var m = DATA.files.find(function(f) {{ return f.name === arg; }});
      if (!m) appendTerm(["File not found - " + (arg || "(missing)")]);
      else if (!m.content) appendTerm([m.name + " is a binary system image (" + m.bytes + " bytes)."]);
      else appendTerm(m.content.split("\\n"));
    }} else if (verb === "AUTOEXEC.BAT") {{
      state.regs.AX = 0x0900; state.regs.DX = 0x0140; renderRegs();
      appendTerm(["@ECHO OFF", "PROMPT $P$G", "PATH C:\\\\DOS;C:\\\\FIELDGLS", "Fieldglass 8086 Observatory Ready."]);
    }} else if (verb === "STEP") {{
      appendTerm([stepCpu()]);
    }} else if (verb === "REGS") {{
      appendTerm(["AX=" + hex4(state.regs.AX) + " BX=" + hex4(state.regs.BX) + " CX=" + hex4(state.regs.CX) + " DX=" + hex4(state.regs.DX) + " CS:IP=" + hex4(state.regs.CS) + ":" + hex4(state.regs.IP)]);
    }} else {{
      appendTerm(["Bad command or file name - " + verb]);
    }}
  }}

  // Render Memory Map
  var mb = document.getElementById("memBars");
  DATA.memory.forEach(function(r) {{
    var pct = Math.max(4, Math.min(100, (r.bytes / 614400) * 100));
    var col = r.area === "Conventional" ? "#5edaf0" : (r.area === "UMA" ? "#f2c45c" : "#f46a7e");
    var row = document.createElement("div");
    row.style.marginBottom = "7px";
    row.innerHTML = '<div class="mono" style="font-size:0.78rem;display:flex;justify-content:space-between;"><span>' + r.region + ' (' + r.area + ')</span><span>' + r.bytes.toLocaleString() + ' B</span></div>'
      + '<div style="background:#0a101a;border:1px solid #243852;height:12px;border-radius:4px;overflow:hidden;"><div style="width:' + pct.toFixed(1) + '%;height:100%;background:' + col + ';"></div></div>';
    mb.appendChild(row);
  }});
  document.getElementById("fat12Box").textContent = "FAT12 1.44 MB: " + DATA.fat12.total_sectors + " sectors x " + DATA.fat12.bytes_per_sector + " B = " + DATA.fat12.total_bytes.toLocaleString() + " B | Data Clusters: " + DATA.fat12.data_clusters;
  document.getElementById("dosAtauBadge").textContent = "Future A_0.10=" + DATA.chiasm.future_accessible_volume + " · " + DATA.chiasm.presence_glyph;

  // Draw Kloster telemetry canvas
  var cv = document.getElementById("dosTelemCanvas");
  var ctx = cv.getContext("2d");
  ctx.fillStyle = "#080c14"; ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.strokeStyle = "#5edaf0"; ctx.lineWidth = 2.5; ctx.beginPath();
  DATA.episodes.forEach(function(ep, i) {{
    var x = 24 + (i / (DATA.episodes.length - 1)) * (cv.width - 48);
    var y = cv.height - 24 - (ep.a_010 / 8.0) * (cv.height - 52);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.stroke();
  ctx.fillStyle = "#f2c45c"; ctx.font = "12px monospace";
  ctx.fillText("12-Episode Boot-to-Shell A_0.10(p_t)  |  EI=" + DATA.chiasm.effective_information_bits + " bits", 18, 22);

  document.getElementById("dosRunBtn").addEventListener("click", function() {{
    var inp = document.getElementById("dosInput");
    runCmd(inp.value);
  }});
  document.getElementById("dosInput").addEventListener("keydown", function(ev) {{
    if (ev.key === "Enter") runCmd(ev.target.value);
  }});
  document.querySelectorAll(".dos-quick").forEach(function(btn) {{
    btn.addEventListener("click", function() {{ runCmd(btn.getAttribute("data-cmd")); }});
  }});
  document.getElementById("stepBtn").addEventListener("click", function() {{ appendTerm([stepCpu()]); }});
  document.getElementById("a20Btn").addEventListener("click", function() {{ state.a20 = !state.a20; renderRegs(); }});

  renderRegs();
  appendTerm(["MS-DOS 6.22 Educational Shell Ready. Type HELP or click a command."]);
  runCmd("MEM");
}})();
"""
    return _html_shell(
        "MS-DOS 6.22 & 8086 Real-Mode Simulator",
        "R1 Domain 01 · Deterministic 16-Bit Systems",
        "Interactive COMMAND.COM shell, 8086 registers & flags, 640 KB conventional memory map, FAT12 geometry, and Kloster A_tau(p) telemetry.",
        "msdos",
        "",
        body,
        script,
    )


def build_flight_html(telem: dict[str, Any]) -> str:
    data_blob = json.dumps({"chiasm": telem["chiasm_nexus"], "episodes": telem["per_episode"]})
    body = """
<div class="grid2">
  <div class="card">
    <h3>6-DOF Artificial Horizon &amp; Six-Pack HUD <span class="badge" id="flightPhaseBadge">CRUISE</span></h3>
    <canvas id="hudCanvas" width="540" height="360"></canvas>
    <div id="sixPackGrid" class="grid3" style="margin-top:12px;"></div>
  </div>
  <div class="card">
    <h3>Flight Controls &amp; Deterministic Integrator <span class="badge" id="flightAtauBadge">A_0.10</span></h3>
    <div style="display:grid;gap:10px;margin-bottom:12px;">
      <label class="mono" style="font-size:0.82rem;">Throttle: <span id="thrVal">72%</span>
        <input id="thrSlider" type="range" min="0" max="100" value="72" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.82rem;">Pitch Cmd: <span id="pitVal">0.00</span>
        <input id="pitSlider" type="range" min="-100" max="100" value="0" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.82rem;">Roll Cmd: <span id="rolVal">0.00</span>
        <input id="rolSlider" type="range" min="-100" max="100" value="0" style="width:100%;" />
      </label>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
      <button class="btn accent preset-btn" data-preset="cruise" type="button">Cruise</button>
      <button class="btn preset-btn" data-preset="climb" type="button">Climb</button>
      <button class="btn preset-btn" data-preset="turn30" type="button">30° Turn</button>
      <button class="btn preset-btn" data-preset="approach" type="button">Approach</button>
      <button id="stepFlightBtn" class="btn" type="button">Step +0.5s</button>
      <button id="toggleRunBtn" class="btn" type="button">Pause Sim</button>
    </div>
    <canvas id="flightTelemCanvas" width="520" height="170"></canvas>
  </div>
</div>
"""
    script = f"""
(function() {{
  var TELEM = {data_blob};
  var sim = {{ u:56.0, v:0.0, w:1.6, p:0.0, q:0.0, r:0.0, phi:0.0, theta:0.048, psi:Math.PI/2, alt:1500.0, thr:0.72, running:true, hist:[] }};
  function isaRho(h) {{ return 1.225 * Math.pow(Math.max(0.1, 1.0 - 2.25577e-5 * Math.max(0, h)), 4.25588); }}
  function stepSim(dt) {{
    var pcmd = Number(document.getElementById("pitSlider").value) / 100.0;
    var rcmd = Number(document.getElementById("rolSlider").value) / 100.0;
    sim.thr = Number(document.getElementById("thrSlider").value) / 100.0;
    var va = Math.max(12.0, Math.hypot(sim.u, sim.v, sim.w));
    var alpha = Math.atan2(sim.w, Math.max(5.0, sim.u));
    var rho = isaRho(sim.alt);
    var qbar = 0.5 * rho * va * va;
    var stallRad = 15.0 * Math.PI / 180.0;
    var cl;
    if (Math.abs(alpha) <= stallRad) {{
      cl = 0.28 + 4.41 * alpha;
    }} else {{
      var excess = Math.abs(alpha) - stallRad;
      var signA = alpha >= 0 ? 1.0 : -1.0;
      var clPeak = 0.28 + 4.41 * signA * stallRad;
      cl = clPeak * Math.exp(-3.5 * excess);
    }}
    var cd = 0.027 + 0.054 * cl * cl;
    var lift = qbar * 16.2 * cl;
    var drag = qbar * 16.2 * cd;
    var thrust = sim.thr * 2400.0 * Math.pow(rho / 1.225, 0.7);
    var ca = Math.cos(alpha), sa = Math.sin(alpha);
    var fx = -drag * ca + lift * sa + thrust - 1043.0 * 9.80665 * Math.sin(sim.theta);
    var fz = -drag * sa - lift * ca + 1043.0 * 9.80665 * Math.cos(sim.theta) * Math.cos(sim.phi);
    sim.u = Math.max(15.0, Math.min(115.0, sim.u + (fx / 1043.0 - sim.q * sim.w) * dt));
    sim.w = Math.max(-18.0, Math.min(22.0, sim.w + (fz / 1043.0 + sim.q * sim.u) * dt));
    sim.p += (3.2 * (rcmd * 0.73 - sim.phi) - 2.6 * sim.p) * dt;
    sim.q += (2.4 * (0.05 + pcmd * 0.28 - sim.theta) - 2.8 * sim.q) * dt;
    var turnR = (9.80665 / va) * Math.tan(Math.max(-1.0, Math.min(1.0, sim.phi)));
    sim.r += 2.2 * (turnR - sim.r) * dt;
    sim.phi = Math.max(-1.1, Math.min(1.1, sim.phi + sim.p * dt));
    sim.theta = Math.max(-0.6, Math.min(0.6, sim.theta + sim.q * dt));
    sim.psi = (sim.psi + sim.r * dt + Math.PI * 2) % (Math.PI * 2);
    var vz = sim.u * Math.sin(sim.theta) - sim.w * Math.cos(sim.phi) * Math.cos(sim.theta);
    sim.alt = Math.max(0.0, sim.alt + vz * dt);
    var ias = va * 1.943844;
    var vsi = vz * 196.8504;
    var degPhi = sim.phi * 180 / Math.PI;
    var degTheta = sim.theta * 180 / Math.PI;
    var degHdg = (sim.psi * 180 / Math.PI) % 360;
    var vec = [
      Math.max(0.04, ias / 450), Math.max(0.03, 0.12 + vsi / 5000),
      Math.max(0.03, 0.08 + Math.abs(degPhi) / 160), Math.max(0.04, 0.18 - Math.abs(degTheta) / 120),
      Math.max(0.03, 0.22 - Math.abs(alpha * 180 / Math.PI) / 80), Math.max(0.04, 0.06 + sim.thr * 0.2),
      Math.max(0.03, 0.07 + Math.abs(sim.r * 180 / Math.PI) / 30), 0.14
    ];
    var sum = vec.reduce(function(a,b){{return a+b;}},0);
    var norm = vec.map(function(v){{return v/sum;}});
    var a010 = norm.filter(function(p){{return p > 0.10;}}).length;
    sim.hist.push(a010);
    if (sim.hist.length > 48) sim.hist.shift();
    document.getElementById("flightAtauBadge").textContent = "Live A_0.10(p)=" + a010;
    return {{ ias:ias, altFt:sim.alt*3.28084, vsi:vsi, hdg:degHdg, pitch:degTheta, roll:degPhi, aoa:alpha*180/Math.PI, turn:sim.r*180/Math.PI }};
  }}
  function drawHud(h) {{
    var cv = document.getElementById("hudCanvas");
    var ctx = cv.getContext("2d");
    var w = cv.width, ht = cv.height, cx = w / 2, cy = ht / 2;
    ctx.fillStyle = "#080c14"; ctx.fillRect(0, 0, w, ht);
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, cy, 140, 0, Math.PI * 2); ctx.clip();
    ctx.translate(cx, cy);
    ctx.rotate(-sim.phi);
    var pitchPx = h.pitch * 4.5;
    ctx.fillStyle = "#1f5a96"; ctx.fillRect(-260, -260 + pitchPx, 520, 260);
    ctx.fillStyle = "#6c482c"; ctx.fillRect(-260, pitchPx, 520, 260);
    ctx.strokeStyle = "#eaeff5"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(-220, pitchPx); ctx.lineTo(220, pitchPx); ctx.stroke();
    ctx.restore();
    ctx.strokeStyle = "#f2c45c"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(cx, cy, 140, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx - 46, cy); ctx.lineTo(cx - 14, cy); ctx.lineTo(cx, cy + 12); ctx.lineTo(cx + 14, cy); ctx.lineTo(cx + 46, cy); ctx.stroke();

    var grid = document.getElementById("sixPackGrid");
    var cards = [
      ["Airspeed", h.ias.toFixed(1) + " kt"],
      ["Altitude", h.altFt.toFixed(0) + " ft"],
      ["VSI", (h.vsi >= 0 ? "+" : "") + h.vsi.toFixed(0) + " fpm"],
      ["Heading", h.hdg.toFixed(0) + "°"],
      ["Pitch / Roll", h.pitch.toFixed(1) + "° / " + h.roll.toFixed(1) + "°"],
      ["AoA / Turn", h.aoa.toFixed(1) + "° / " + h.turn.toFixed(1) + "°/s"]
    ];
    grid.innerHTML = cards.map(function(c) {{
      return '<div class="kpi"><div class="lbl">' + c[0] + '</div><div class="val">' + c[1] + '</div></div>';
    }}).join("");

    var tc = document.getElementById("flightTelemCanvas");
    var tctx = tc.getContext("2d");
    tctx.fillStyle = "#080c14"; tctx.fillRect(0, 0, tc.width, tc.height);
    tctx.strokeStyle = "#5edaf0"; tctx.lineWidth = 2.5; tctx.beginPath();
    sim.hist.forEach(function(v, i) {{
      var x = 20 + (i / Math.max(1, sim.hist.length - 1)) * (tc.width - 40);
      var y = tc.height - 20 - (v / 8.0) * (tc.height - 48);
      if (i === 0) tctx.moveTo(x, y); else tctx.lineTo(x, y);
    }});
    tctx.stroke();
    tctx.fillStyle = "#f2c45c"; tctx.font = "12px monospace";
    tctx.fillText("Live Kloster A_0.10(p_t)  |  Sortie EI=" + TELEM.chiasm.effective_information_bits + " bits", 14, 20);
  }}
  function setPreset(name) {{
    document.getElementById("flightPhaseBadge").textContent = name.toUpperCase();
    if (name === "cruise") {{ sim.u=56; sim.w=1.6; sim.phi=0; sim.theta=0.048; sim.alt=1500; document.getElementById("thrSlider").value=72; document.getElementById("pitSlider").value=0; document.getElementById("rolSlider").value=0; }}
    if (name === "climb") {{ sim.u=46; sim.w=3.4; sim.phi=0; sim.theta=0.18; sim.alt=900; document.getElementById("thrSlider").value=95; document.getElementById("pitSlider").value=35; document.getElementById("rolSlider").value=0; }}
    if (name === "turn30") {{ sim.u=54; sim.w=2.4; sim.phi=0.52; sim.theta=0.07; sim.alt=1500; document.getElementById("thrSlider").value=78; document.getElementById("pitSlider").value=5; document.getElementById("rolSlider").value=72; }}
    if (name === "approach") {{ sim.u=38; sim.w=1.9; sim.phi=0; sim.theta=-0.04; sim.alt=450; document.getElementById("thrSlider").value=38; document.getElementById("pitSlider").value=-25; document.getElementById("rolSlider").value=0; }}
    syncLabels();
    drawHud(stepSim(0.05));
  }}
  function syncLabels() {{
    document.getElementById("thrVal").textContent = document.getElementById("thrSlider").value + "%";
    document.getElementById("pitVal").textContent = (Number(document.getElementById("pitSlider").value)/100).toFixed(2);
    document.getElementById("rolVal").textContent = (Number(document.getElementById("rolSlider").value)/100).toFixed(2);
  }}
  ["thrSlider","pitSlider","rolSlider"].forEach(function(id) {{
    document.getElementById(id).addEventListener("input", syncLabels);
  }});
  document.querySelectorAll(".preset-btn").forEach(function(b) {{
    b.addEventListener("click", function() {{ setPreset(b.getAttribute("data-preset")); }});
  }});
  document.getElementById("stepFlightBtn").addEventListener("click", function() {{
    for (var k = 0; k < 10; k++) drawHud(stepSim(0.05));
  }});
  document.getElementById("toggleRunBtn").addEventListener("click", function(ev) {{
    sim.running = !sim.running;
    ev.target.textContent = sim.running ? "Pause Sim" : "Resume Sim";
  }});
  setPreset("cruise");
  setInterval(function() {{ if (sim.running) drawHud(stepSim(0.05)); }}, 100);
}})();
"""
    return _html_shell(
        "6-DOF Flight Dynamics & Telemetry HUD",
        "R1 Domain 02 · Aerodynamics & Attitude Kinematics",
        "Interactive 6-DOF artificial horizon, six-pack flight instruments, stall/bank physics, and live Kloster A_tau(p_t) telemetry.",
        "flight_sim",
        "",
        body,
        script,
    )


def build_medical_html(telem: dict[str, Any]) -> str:
    data_blob = json.dumps({"flags": NON_CLINICAL_FLAGS, "chiasm": telem["chiasm_nexus"]})
    body = f"""
<div class="disclaimer-banner" role="alert">
  {html.escape(DISCLAIMER)}<br/>
  <span class="mono" style="font-size:0.78rem;font-weight:400;">
    clinical_use: false · educational_simulation_only: true · clinical_certification_claimed: false · executed: false · tokens_used: 0
  </span>
</div>

<div class="grid2">
  <div class="card">
    <h3>Multiparameter Synthetic Waveform Scope <span class="badge">SIMULATED ONLY</span></h3>
    <canvas id="medScopeCanvas" width="540" height="340"></canvas>
    <div id="medKpis" class="grid3" style="margin-top:12px;"></div>
  </div>
  <div class="card">
    <h3>Ventilator P-V Loop &amp; Educational Controls <span class="badge" id="medAtauBadge">NON-CLINICAL</span></h3>
    <canvas id="pvCanvas" width="520" height="210" style="margin-bottom:10px;"></canvas>
    <div class="grid2" style="gap:10px;">
      <label class="mono" style="font-size:0.8rem;">Sim HR (bpm): <span id="hrLbl">72</span>
        <input id="hrSlider" type="range" min="40" max="160" value="72" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.8rem;">Beer-Lambert R-Ratio: <span id="rLbl">0.55</span>
        <input id="rSlider" type="range" min="40" max="160" value="55" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.8rem;">Sim RR (bpm): <span id="rrLbl">14</span>
        <input id="rrSlider" type="range" min="8" max="30" value="14" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.8rem;">Compliance (mL/cmH2O): <span id="cLbl">50</span>
        <input id="cSlider" type="range" min="20" max="90" value="50" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.8rem;">Tidal Vol Vt (mL): <span id="vtLbl">480</span>
        <input id="vtSlider" type="range" min="250" max="750" value="480" style="width:100%;" />
      </label>
      <label class="mono" style="font-size:0.8rem;">PEEP (cmH2O): <span id="peepLbl">5</span>
        <input id="peepSlider" type="range" min="0" max="15" value="5" style="width:100%;" />
      </label>
    </div>
  </div>
</div>

<div class="card">
  <h3>Educational Dimensional-Analysis Infusion Calculator <span class="badge">MATH SANDBOX ONLY</span></h3>
  <div class="grid3">
    <label class="mono" style="font-size:0.8rem;">Dose (mcg/kg/min)
      <input id="infDose" type="number" step="0.5" value="5.0" style="width:100%;margin-top:4px;" />
    </label>
    <label class="mono" style="font-size:0.8rem;">Sim Mass (kg)
      <input id="infWeight" type="number" step="1" value="70" style="width:100%;margin-top:4px;" />
    </label>
    <label class="mono" style="font-size:0.8rem;">Conc (mcg/mL)
      <input id="infConc" type="number" step="50" value="1000" style="width:100%;margin-top:4px;" />
    </label>
  </div>
  <div id="infOut" class="mono" style="margin-top:10px;padding:10px 12px;background:#0a101a;border:1px solid #243852;border-radius:8px;color:var(--gold);"></div>
</div>
"""
    script = f"""
(function() {{
  var META = {data_blob};
  function ecgPqrst(t, hr) {{
    var phi = (t * (hr / 60.0)) % 1.0;
    var w = [[0.16,0.15,0.032],[0.36,-0.14,0.012],[0.40,1.15,0.013],[0.44,-0.26,0.013],[0.64,0.32,0.048]];
    var v = 0;
    for (var i=0;i<w.length;i++) {{ var d = phi - w[i][0]; v += w[i][1] * Math.exp(-0.5 * (d/w[i][2])*(d/w[i][2])); }}
    return v;
  }}
  function spo2Model(rRatio, t, hr) {{
    var spo2 = Math.max(70, Math.min(100, 110.0 - 25.0 * rRatio));
    var phi = (t * (hr / 60.0)) % 1.0;
    var pleth = Math.exp(-0.5 * Math.pow((phi-0.22)/0.09, 2)) + 0.42 * Math.exp(-0.5 * Math.pow((phi-0.44)/0.10, 2));
    return {{ spo2: spo2, pleth: pleth }};
  }}
  function capno(t, rr, etco2) {{
    var phi = (t * (rr / 60.0)) % 1.0;
    if (phi < 0.28) return 0;
    if (phi < 0.40) {{ var u = (phi-0.28)/0.12; return etco2*0.90*(0.5 - 0.5*Math.cos(Math.PI*u)); }}
    if (phi < 0.72) {{ var u2 = (phi-0.40)/0.32; return etco2*(0.90 + 0.10*u2); }}
    if (phi < 0.80) {{ var u3 = (phi-0.72)/0.08; return etco2*(1.0 - 0.5*(1 - Math.cos(Math.PI*u3))); }}
    return 0;
  }}
  function renderAll() {{
    var hr = Number(document.getElementById("hrSlider").value);
    var rRatio = Number(document.getElementById("rSlider").value) / 100.0;
    var rr = Number(document.getElementById("rrSlider").value);
    var comp = Number(document.getElementById("cSlider").value);
    var vt = Number(document.getElementById("vtSlider").value);
    var peep = Number(document.getElementById("peepSlider").value);
    document.getElementById("hrLbl").textContent = hr;
    document.getElementById("rLbl").textContent = rRatio.toFixed(2);
    document.getElementById("rrLbl").textContent = rr;
    document.getElementById("cLbl").textContent = comp;
    document.getElementById("vtLbl").textContent = vt;
    document.getElementById("peepLbl").textContent = peep;

    var cv = document.getElementById("medScopeCanvas");
    var ctx = cv.getContext("2d");
    ctx.fillStyle = "#070a10"; ctx.fillRect(0, 0, cv.width, cv.height);

    // ECG trace
    ctx.strokeStyle = "#8ce094"; ctx.lineWidth = 2; ctx.beginPath();
    for (var i=0;i<240;i++) {{
      var x = 16 + (i/239)*(cv.width-32);
      var y = 84 - ecgPqrst(i*2.4/240, hr)*50;
      if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }}
    ctx.stroke();

    // Pleth trace
    ctx.strokeStyle = "#5edaf0"; ctx.lineWidth = 2; ctx.beginPath();
    for (var j=0;j<240;j++) {{
      var x2 = 16 + (j/239)*(cv.width-32);
      var y2 = 200 - spo2Model(rRatio, j*2.4/240, hr).pleth*60;
      if (j===0) ctx.moveTo(x2,y2); else ctx.lineTo(x2,y2);
    }}
    ctx.stroke();

    // Capno trace
    ctx.strokeStyle = "#f2c45c"; ctx.lineWidth = 2; ctx.beginPath();
    for (var k=0;k<240;k++) {{
      var x3 = 16 + (k/239)*(cv.width-32);
      var y3 = 315 - (capno(k*9.0/240, rr, 38.0)/45.0)*72;
      if (k===0) ctx.moveTo(x3,y3); else ctx.lineTo(x3,y3);
    }}
    ctx.stroke();
    ctx.fillStyle = "#93a6be"; ctx.font = "11px monospace";
    ctx.fillText("SIMULATED ECG (mV)", 16, 20);
    ctx.fillText("SIMULATED BEER-LAMBERT PLETH (660/940nm)", 16, 134);
    ctx.fillText("SIMULATED CAPNOGRAPHY (mmHg)", 16, 240);

    // P-V Loop
    var pvc = document.getElementById("pvCanvas");
    var pctx = pvc.getContext("2d");
    pctx.fillStyle = "#070a10"; pctx.fillRect(0, 0, pvc.width, pvc.height);
    pctx.strokeStyle = "#f46a7e"; pctx.lineWidth = 2.5; pctx.beginPath();
    var pPeak = 0;
    for (var m=0;m<=80;m++) {{
      var th = 2*Math.PI*(m/80);
      var v = 0.5*vt*(1 - Math.cos(th));
      var flow = 0.55*Math.sin(th);
      var p = peep + v/comp + 8.0*flow;
      if (p > pPeak) pPeak = p;
      var px = 30 + (p/38.0)*(pvc.width-60);
      var py = pvc.height - 20 - (v/800.0)*(pvc.height-42);
      if (m===0) pctx.moveTo(px,py); else pctx.lineTo(px,py);
    }}
    pctx.stroke();
    pctx.fillStyle = "#f2c45c"; pctx.font = "12px monospace";
    pctx.fillText("Simulated P-V Loop (P_peak = " + pPeak.toFixed(1) + " cmH2O)", 16, 20);

    var spo2Val = spo2Model(rRatio, 0.22, hr).spo2;
    document.getElementById("medKpis").innerHTML = [
      ["Sim HR", hr + " bpm"],
      ["Sim SpO2 (Beer-Lambert)", spo2Val.toFixed(1) + " %"],
      ["Sim Peak Pressure", pPeak.toFixed(1) + " cmH2O"]
    ].map(function(c) {{ return '<div class="kpi"><div class="lbl">' + c[0] + '</div><div class="val">' + c[1] + '</div></div>'; }}).join("");
    document.getElementById("medAtauBadge").textContent = "A_0.10=" + META.chiasm.future_accessible_volume + " · NON-CLINICAL";

    var rawDose = document.getElementById("infDose").value.trim();
    var rawWt = document.getElementById("infWeight").value.trim();
    var rawConc = document.getElementById("infConc").value.trim();
    var dose = rawDose === "" ? NaN : Number(rawDose);
    var wt = rawWt === "" ? NaN : Number(rawWt);
    var conc = rawConc === "" ? NaN : Number(rawConc);
    var infOut = document.getElementById("infOut");
    if (!Number.isFinite(dose) || !Number.isFinite(wt) || !Number.isFinite(conc) || dose < 0 || wt <= 0) {{
      infOut.style.color = "var(--ruby)";
      infOut.textContent = "Validation error: Enter finite positive values (Dose >= 0, Mass > 0, Concentration > 0) — STRICTLY SIMULATED / NON-CLINICAL";
    }} else if (conc <= 0) {{
      infOut.style.color = "var(--ruby)";
      infOut.textContent = "Validation error: Concentration must be > 0 — STRICTLY SIMULATED / NON-CLINICAL";
    }} else {{
      var mlHr = (dose * wt * 60.0) / conc;
      var gttMin = (mlHr * 20) / 60.0;
      if (!Number.isFinite(mlHr) || !Number.isFinite(gttMin)) {{
        infOut.style.color = "var(--ruby)";
        infOut.textContent = "Validation error: Calculated rate exceeds finite bounds — STRICTLY SIMULATED / NON-CLINICAL";
      }} else {{
        infOut.style.color = "var(--gold)";
        infOut.textContent = "Educational Formula Rate: " + mlHr.toFixed(2) + " mL/hr (" + gttMin.toFixed(2) + " gtt/min @ 20 gtt/mL) — STRICTLY SIMULATED / NON-CLINICAL";
      }}
    }}
  }}
  ["hrSlider","rSlider","rrSlider","cSlider","vtSlider","peepSlider","infDose","infWeight","infConc"].forEach(function(id) {{
    document.getElementById(id).addEventListener("input", renderAll);
  }});
  renderAll();
}})();
"""
    return _html_shell(
        "Simulated Medical Equipment Physics & Optics Sandbox",
        "R1 Domain 03 · Strictly Simulated / Educational / Non-Clinical",
        "Educational Beer-Lambert pulse oximetry, synthetic P-QRS-T, capnography, ventilator P-V loop, and dimensional-analysis infusion math.",
        "medical_sim",
        "",
        body,
        script,
    )


def build_software_html(telem: dict[str, Any], sealed_report: dict[str, Any]) -> str:
    data_blob = json.dumps(
        {
            "stages": list(SoftwareObservatoryModel.PIPELINE_STAGES),
            "matrix": list(SoftwareObservatoryModel.WIN7_MODERN_MATRIX),
            "report": sealed_report,
            "default_dist": telem["episodes"][-1],
        }
    )
    body = """
<div class="grid2">
  <div class="card">
    <h3>Live Kloster A_tau(p) Repertoire Calculator <span class="badge" id="swAtauBadge">strict p &gt; tau</span></h3>
    <div style="margin-bottom:10px;">
      <label class="mono" style="font-size:0.84rem;">Threshold tau: <strong id="tauReadout" style="color:var(--gold);">0.10</strong>
        <input id="tauSlider" type="range" min="1" max="45" value="10" style="width:100%;" />
      </label>
    </div>
    <div id="vecSliders" class="grid2" style="gap:8px;margin-bottom:10px;"></div>
    <div id="swMetrics" class="grid3" style="margin-bottom:10px;"></div>
    <canvas id="swAtauCanvas" width="520" height="190"></canvas>
  </div>
  <div class="card">
    <h3>Causal Chiasm &amp; Pure-JS SHA-256 Verifier <span class="badge" id="shaBadge">VERIFIED</span></h3>
    <p class="sub" style="margin-bottom:8px;">Canonical SHA-256 verification runs synchronously in pure JS FIPS 180-4 (works offline over both <code>http://</code> and <code>file://</code>). Note: JavaScript <code>JSON.parse</code> + <code>JSON.stringify</code> normalizes JS <code>Number</code> formatting (e.g. <code>1.0</code> &rarr; <code>1</code>, <code>1e-05</code> &rarr; <code>0.00001</code>), whereas Python <code>json.dumps</code> preserves float notation.</p>
    <textarea id="reportJsonBox" rows="12" style="width:100%;font-size:0.78rem;margin-bottom:8px;"></textarea>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
      <button id="verifyShaBtn" class="btn accent" type="button">Verify SHA-256 Seal</button>
      <button id="resetJsonBtn" class="btn" type="button">Reset Sealed Report</button>
      <span id="shaStatusText" class="mono" style="font-size:0.8rem;color:var(--green);"></span>
    </div>
  </div>
</div>

<div class="grid2">
  <div class="card">
    <h3>6-Stage Fieldglass Pipeline Inspector <span class="badge">src/fieldglass/</span></h3>
    <div id="pipelineList"></div>
  </div>
  <div class="card">
    <h3>Win7-Era to Modern Systems Engineering Matrix <span class="badge">6 Layers</span></h3>
    <table>
      <thead><tr><th>Layer</th><th>Win7 / IE8-11 / Py3.7</th><th>Modern Observatory</th></tr></thead>
      <tbody id="matrixBody"></tbody>
    </table>
  </div>
</div>
"""
    script = f"""
(function() {{
  var DATA = {data_blob};

  // Compact pure-JS synchronous SHA-256 (FIPS 180-4) so file:// never throws on crypto.subtle
  function sha256Hex(str) {{
    var utf8 = unescape(encodeURIComponent(str));
    var words = [];
    for (var i = 0; i < utf8.length; i++) {{
      words[i >> 2] |= (utf8.charCodeAt(i) & 0xff) << (24 - (i % 4) * 8);
    }}
    var bitLen = utf8.length * 8;
    words[bitLen >> 5] |= 0x80 << (24 - (bitLen % 32));
    words[(((bitLen + 64) >> 9) << 4) + 15] = bitLen;
    var K = [
      0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    ];
    var H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    function rotr(n, x) {{ return (x >>> n) | (x << (32 - n)); }}
    for (var b = 0; b < words.length; b += 16) {{
      var w = new Array(64);
      for (var t = 0; t < 16; t++) w[t] = words[b + t] | 0;
      for (var t2 = 16; t2 < 64; t2++) {{
        var s0 = rotr(7, w[t2-15]) ^ rotr(18, w[t2-15]) ^ (w[t2-15] >>> 3);
        var s1 = rotr(17, w[t2-2]) ^ rotr(19, w[t2-2]) ^ (w[t2-2] >>> 10);
        w[t2] = (w[t2-16] + s0 + w[t2-7] + s1) | 0;
      }}
      var a=H[0],bb=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];
      for (var t3 = 0; t3 < 64; t3++) {{
        var S1 = rotr(6,e) ^ rotr(11,e) ^ rotr(25,e);
        var ch = (e & f) ^ ((~e) & g);
        var temp1 = (h + S1 + ch + K[t3] + w[t3]) | 0;
        var S0 = rotr(2,a) ^ rotr(13,a) ^ rotr(22,a);
        var maj = (a & bb) ^ (a & c) ^ (bb & c);
        var temp2 = (S0 + maj) | 0;
        h=g; g=f; f=e; e=(d+temp1)|0; d=c; c=bb; bb=a; a=(temp1+temp2)|0;
      }}
      H[0]=(H[0]+a)|0; H[1]=(H[1]+bb)|0; H[2]=(H[2]+c)|0; H[3]=(H[3]+d)|0;
      H[4]=(H[4]+e)|0; H[5]=(H[5]+f)|0; H[6]=(H[6]+g)|0; H[7]=(H[7]+h)|0;
    }}
    return H.map(function(v) {{ return (v >>> 0).toString(16).padStart(8, "0"); }}).join("");
  }}

  function sortKeysDeep(val) {{
    if (Array.isArray(val)) return val.map(sortKeysDeep);
    if (val && typeof val === "object") {{
      var out = {{}};
      Object.keys(val).sort().forEach(function(k) {{ out[k] = sortKeysDeep(val[k]); }});
      return out;
    }}
    return val;
  }}

  var weights = Object.assign({{}}, DATA.default_dist);
  var keys = Object.keys(weights);
  var vs = document.getElementById("vecSliders");
  keys.forEach(function(k) {{
    var lbl = document.createElement("label");
    lbl.className = "mono";
    lbl.style.fontSize = "0.78rem";
    lbl.innerHTML = k + ': <span id="w_' + k + '">' + weights[k].toFixed(3) + '</span>'
      + '<input type="range" min="1" max="50" value="' + Math.round(weights[k]*100) + '" data-key="' + k + '" style="width:100%;" />';
    vs.appendChild(lbl);
  }});

  function updateKloster() {{
    var tau = Number(document.getElementById("tauSlider").value) / 100.0;
    document.getElementById("tauReadout").textContent = tau.toFixed(2);
    var total = keys.reduce(function(s, k) {{ return s + weights[k]; }}, 0);
    var probs = keys.map(function(k) {{ return weights[k] / total; }});
    var aTau = probs.filter(function(p) {{ return p > tau; }}).length;
    var h1 = -probs.reduce(function(s, p) {{ return p > 0 ? s + p * Math.log2(p) : s; }}, 0);
    var h2 = -Math.log2(Math.max(1e-12, probs.reduce(function(s, p) {{ return s + p*p; }}, 0)));
    var m4 = Math.pow(probs.reduce(function(s, p) {{ return s + Math.pow(p, 4); }}, 0), 0.25);

    document.getElementById("swAtauBadge").textContent = "A_" + tau.toFixed(2) + "(p) = " + aTau + " / " + probs.length;
    document.getElementById("swMetrics").innerHTML = [
      ["A_tau(p)", aTau + " states"],
      ["H1 / H2", h1.toFixed(2) + " / " + h2.toFixed(2) + " b"],
      ["M4^(1/4)", m4.toFixed(4)]
    ].map(function(c) {{ return '<div class="kpi"><div class="lbl">' + c[0] + '</div><div class="val">' + c[1] + '</div></div>'; }}).join("");

    var cv = document.getElementById("swAtauCanvas");
    var ctx = cv.getContext("2d");
    ctx.fillStyle = "#080c14"; ctx.fillRect(0, 0, cv.width, cv.height);
    var bw = (cv.width - 48) / probs.length;
    var ymax = 0.45;
    probs.forEach(function(p, idx) {{
      var bh = Math.min(1.0, p / ymax) * (cv.height - 46);
      ctx.fillStyle = p > tau ? "#f2c45c" : "#385070";
      ctx.fillRect(24 + idx * bw + 6, cv.height - 26 - bh, bw - 12, bh);
    }});
    var ty = cv.height - 26 - Math.min(1.0, tau / ymax) * (cv.height - 46);
    ctx.strokeStyle = "#f46a7e"; ctx.lineWidth = 2; ctx.setLineDash([6,4]);
    ctx.beginPath(); ctx.moveTo(16, ty); ctx.lineTo(cv.width - 16, ty); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#f46a7e"; ctx.font = "12px monospace";
    ctx.fillText("tau = " + tau.toFixed(2) + " (strict p > tau)", 22, Math.max(16, ty - 6));
  }}

  vs.querySelectorAll("input").forEach(function(inp) {{
    inp.addEventListener("input", function(ev) {{
      var k = ev.target.getAttribute("data-key");
      weights[k] = Number(ev.target.value) / 100.0;
      document.getElementById("w_" + k).textContent = weights[k].toFixed(3);
      updateKloster();
    }});
  }});
  document.getElementById("tauSlider").addEventListener("input", updateKloster);

  function verifyBox() {{
    var box = document.getElementById("reportJsonBox");
    var badge = document.getElementById("shaBadge");
    var txt = document.getElementById("shaStatusText");
    try {{
      var obj = JSON.parse(box.value);
      if (!obj || typeof obj !== "object" || Array.isArray(obj)) {{
        throw new Error("Expected JSON object");
      }}
      var claimed = obj.report_sha256 || "";
      var copy = Object.assign({{}}, obj);
      delete copy.report_sha256;
      var canonical = JSON.stringify(sortKeysDeep(copy)).replace(/[\\u007f-\\uffff]/g, function(ch) {{
        return "\\\\u" + ("0000" + ch.charCodeAt(0).toString(16)).slice(-4);
      }});
      var recomputed = sha256Hex(canonical);
      var ok = (claimed === recomputed) && obj.contract === "fieldglass-causal-chiasm/v1" && obj.executed === false && obj.sentience_claimed === false && obj.tokens_used === 0;
      badge.textContent = ok ? "SHA-256 VERIFIED" : "SEAL MISMATCH";
      badge.style.color = ok ? "#8ce094" : "#f46a7e";
      txt.style.color = ok ? "#8ce094" : "#f46a7e";
      txt.textContent = ok ? ("MATCH: " + recomputed.slice(0, 16) + "...") : ("MISMATCH (got " + recomputed.slice(0, 16) + "...)");
    }} catch (err) {{
      badge.textContent = "INVALID JSON";
      badge.style.color = "#f46a7e";
      txt.style.color = "#f46a7e";
      txt.textContent = String(err);
    }}
  }}
  document.getElementById("verifyShaBtn").addEventListener("click", verifyBox);
  document.getElementById("resetJsonBtn").addEventListener("click", function() {{
    document.getElementById("reportJsonBox").value = JSON.stringify(DATA.report, null, 2);
    verifyBox();
  }});

  var pl = document.getElementById("pipelineList");
  DATA.stages.forEach(function(st) {{
    var d = document.createElement("div");
    d.className = "kpi";
    d.style.marginBottom = "8px";
    d.innerHTML = '<div class="lbl" style="color:var(--cyan);">' + st.stage + ' · ' + st.module + '</div><div style="font-size:0.84rem;">' + st.contract + ' &rarr; <span class="mono" style="color:var(--gold);">' + st.output + '</span></div>';
    pl.appendChild(d);
  }});
  var mb = document.getElementById("matrixBody");
  DATA.matrix.forEach(function(r) {{
    var tr = document.createElement("tr");
    tr.innerHTML = '<td class="mono" style="color:var(--gold);">' + r.layer + '</td><td>' + r.win7_target + '</td><td>' + r.modern_observatory + '</td>';
    mb.appendChild(tr);
  }});

  document.getElementById("reportJsonBox").value = JSON.stringify(DATA.report, null, 2);
  updateKloster();
  verifyBox();
}})();
"""
    return _html_shell(
        "Software Systems & Fieldglass Architecture Workbench",
        "R1 Domain 04 · Pipeline, Kloster Metrics & Compatibility",
        "Interactive 6-stage Fieldglass pipeline inspector, strict A_tau(p) > tau calculator, synchronous pure-JS SHA-256 verifier, and Win7 matrix.",
        "software",
        "",
        body,
        script,
    )


# ---------------------------------------------------------------------------
# Build Orchestration for All 4 R1 Domains
# ---------------------------------------------------------------------------

def _build_domain(
    *,
    dir_name: str,
    slug: str,
    title: str,
    subtitle: str,
    telem: dict[str, Any],
    plate_fn: Any,
    preview_fn: Any,
    html_fn: Any,
    highlights: list[str],
    extra_flags: dict[str, Any] | None = None,
    braille_title: str | None = None,
) -> dict[str, Any]:
    out_dir = DOCS_DIR / dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    chiasm_svg_path = out_dir / f"{slug}_chiasm.svg"
    write_chiasm_svg(
        chiasm_svg_path,
        title=f"{title.upper()} · CAUSAL CHIASM & FILTRATION TOMOGRAPHY",
        subtitle=subtitle,
        chiasm=telem["chiasm_nexus"],
        tomography=telem["persistent_filtration_tomography"],
        per_sec_a004=telem["per_ep_a004"],
        per_sec_a010=telem["per_ep_a010"],
        nexus_sec=telem["nexus_ep"],
    )
    scene_sha = hashlib.sha256(chiasm_svg_path.read_bytes()).hexdigest()

    plate_svg_path = out_dir / f"{slug}_plate.svg"
    plate_fn(plate_svg_path)
    braille_paths = _save_braille_from_plate(
        plate_svg_path,
        out_dir,
        slug,
        title=braille_title or f"{title.upper()} — 2x4 UNICODE BRAILLE PLATE",
        subtitle=f"{subtitle} · 64-col Braille",
    )

    preview_path = out_dir / "preview.png"
    preview_fn(preview_path)

    raw_report: dict[str, Any] = {
        "slug": slug,
        "title": title,
        "subtitle": subtitle,
        "episode_count": telem["episode_count"],
        "nexus_ep": telem["nexus_ep"],
        "chiasm_nexus": telem["chiasm_nexus"],
        "persistent_filtration_tomography": telem["persistent_filtration_tomography"],
        "per_episode": telem["per_episode"],
        "h1_mean_bits": telem["h1_mean_bits"],
        "h2_mean_bits": telem["h2_mean_bits"],
        "m4_mean_purity": telem["m4_mean_purity"],
        "scene_sha256": scene_sha,
    }
    if extra_flags:
        raw_report.update(extra_flags)
    sealed_report = seal_chiasm_report(raw_report)
    report_path = out_dir / "chiasm_report.json"
    report_path.write_text(json.dumps(sealed_report, indent=2) + "\n", encoding="utf-8")

    # Note: HTML for software embeds sealed_report cleanly; JSON.stringify in JS matches Python when ensure_ascii=True
    html_text = html_fn(sealed_report) if slug == "software" else html_fn()
    index_path = out_dir / "index.html"
    index_path.write_text(html_text, encoding="utf-8")

    summary: dict[str, Any] = {
        "contract": SUMMARY_CONTRACT,
        "domain": dir_name,
        "slug": slug,
        "title": title,
        "subtitle": subtitle,
        "route": f"{dir_name}/index.html",
        "metrics": {
            "episode_count": telem["episode_count"],
            "past_a_010": telem["chiasm_nexus"]["past_accessible_volume"],
            "future_a_010": telem["chiasm_nexus"]["future_accessible_volume"],
            "effective_information_bits": telem["chiasm_nexus"]["effective_information_bits"],
            "presence_glyph": telem["chiasm_nexus"]["presence_glyph"],
            "h1_mean_bits": telem["h1_mean_bits"],
            "h2_mean_bits": telem["h2_mean_bits"],
            "m4_mean_purity": telem["m4_mean_purity"],
        },
        "highlights": highlights,
        "assets": {
            "index_html": "index.html",
            "preview_png": "preview.png",
            "chiasm_svg": chiasm_svg_path.name,
            "plate_svg": plate_svg_path.name,
            "braille_txt": Path(braille_paths["txt"]).name,
            "braille_json": Path(braille_paths["json"]).name,
            "braille_preview_png": Path(braille_paths["preview_png"]).name,
            "chiasm_report": report_path.name,
        },
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    if extra_flags:
        summary.update(extra_flags)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def build_all() -> dict[str, dict[str, Any]]:
    msdos = MSDOS8086Model()
    msdos_telem = msdos.simulate_boot_telemetry()

    flight = FlightSim6DOF()
    flight_telem = flight.simulate_sortie()

    med_telem = MedicalSandboxModel.simulate_telemetry()
    sw_telem = SoftwareObservatoryModel.simulate_pipeline_telemetry()

    results = {
        "msdos": _build_domain(
            dir_name="msdos",
            slug="msdos",
            title="MS-DOS 6.22 & 8086 Real-Mode Simulator",
            subtitle="16-bit 8086 registers, 640 KB memory map, 1.44 MB FAT12 & COMMAND.COM",
            telem=msdos_telem,
            plate_fn=write_msdos_plate_svg,
            preview_fn=lambda p: render_msdos_preview(p, msdos, msdos_telem),
            html_fn=lambda: build_msdos_html(msdos_telem),
            highlights=[
                "16-bit 8086 registers & A20 real-mode physical address calculator",
                "640 KB Conventional + 384 KB UMA + 64 KB HMA memory layout",
                "1.44 MB FAT12 (2,880 x 512 B) volume & interactive COMMAND.COM shell",
            ],
        ),
        "flight-sim": _build_domain(
            dir_name="flight-sim",
            slug="flight_sim",
            title="6-DOF Flight Dynamics & Telemetry HUD",
            subtitle="ISA atmosphere, stall-bounded aerodynamics, bank-to-turn & six-pack HUD",
            telem=flight_telem,
            plate_fn=write_flight_plate_svg,
            preview_fn=lambda p: render_flight_preview(p, flight_telem),
            html_fn=lambda: build_flight_html(flight_telem),
            highlights=[
                "ISA air density rho(h) & 6-DOF semi-implicit aerodynamic integrator",
                "Interactive Canvas artificial horizon + six-pack flight gauges",
                "16-episode sortie coupled into Kloster A_tau(p_t) & Causal Chiasm",
            ],
        ),
        "medical-sim": _build_domain(
            dir_name="medical-sim",
            slug="medical_sim",
            title="Simulated Medical Equipment Sandbox (Non-Clinical)",
            subtitle="Strictly simulated / educational biomedical waveforms & Beer-Lambert optics",
            telem=med_telem,
            plate_fn=write_medical_plate_svg,
            preview_fn=lambda p: render_medical_preview(p, med_telem),
            html_fn=lambda: build_medical_html(med_telem),
            highlights=[
                "STRICTLY SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL USE",
                "Synthetic ECG PQRST, Beer-Lambert 660/940nm SpO2, Capnography & P-V Loop",
                "Educational dimensional-analysis infusion rate calculator",
            ],
            extra_flags=dict(NON_CLINICAL_FLAGS),
            braille_title="MEDICAL SANDBOX (NON-CLINICAL) — 2x4 BRAILLE PLATE",
        ),
        "software": _build_domain(
            dir_name="software",
            slug="software",
            title="Software Systems & Fieldglass Observatory",
            subtitle="6-stage pipeline, strict A_tau(p) > tau, SHA-256 seals & Win7 matrix",
            telem=sw_telem,
            plate_fn=write_software_plate_svg,
            preview_fn=lambda p: render_software_preview(p, sw_telem),
            html_fn=lambda rep: build_software_html(sw_telem, rep),
            highlights=[
                "6-stage deterministic Fieldglass pipeline mapped to src/fieldglass/",
                "Live strict p(x) > tau superlevel-set calculator & pure-JS SHA-256 seal verifier",
                "6-layer Windows 7 SP1 / ES5 / Python 3.7-3.8 compatibility matrix",
            ],
        ),
    }
    return results


def main() -> None:
    res = build_all()
    for name, s in res.items():
        print(
            f"[R1] Built docs/{name}/ -> A_0.10={s['metrics']['future_a_010']}, "
            f"glyph={s['metrics']['presence_glyph']}, tokens={s['tokens_used']}"
        )


if __name__ == "__main__":
    main()
