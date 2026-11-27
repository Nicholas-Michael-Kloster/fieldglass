#!/usr/bin/env python3
"""Reproducible builder for Milestone M3: Zoe Hospital Edition (Windows 7-Era, Non-Clinical).

Generates all self-contained, offline-first deliverables in docs/zoe-hospital/:
  - index.html (Observatory overview + Windows 7 SP1 compatibility matrix)
  - zoe_hospital_kiosk.html (ES5-only, IE8-IE11 safe offline interactive kiosk)
  - zoe_hospital_kiosk.hta (Windows 7 mshta.exe HTA interactive kiosk)
  - zoe_hospital_win7.py (Python 3.7/3.8+ stdlib-only loopback HTTP/1.1 server)
  - launch_win7.bat (CRLF Windows 7 launcher with mshta.exe / HTML fallback)
  - chiasm_tomography.svg (via fieldglass.overlay.write_chiasm_svg)
  - chiasm_report.json (fieldglass-causal-chiasm/v1 + non-clinical SHA-256 seal)
  - summary.json (M4 integration metadata + SHA-256 seal)
  - preview.png (1280x720 Pillow render scrubbed with ffmpeg -map_metadata -1)
  - manifest.json (file inventory + SHA-256 hashes + non-clinical contract)
  - README_WIN7.txt (CRLF Windows 7 Notepad-friendly deployment guide)
  - zoe_hospital_win7_bundle.zip (deterministic portable offline bundle < 5 MB)
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from fieldglass.metrics import (  # noqa: E402
    CONTRACT,
    TONAL_STATES,
    a_tau,
    causal_chiasm,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)
from fieldglass.overlay import write_chiasm_svg  # noqa: E402
from fieldglass.plate import DOT_BITS  # noqa: E402

OUT_DIR = REPO_ROOT / "docs" / "zoe-hospital"
MIN_WINDOWS_VERSION = "Windows 7 SP1 (NT 6.1)"
DISCLAIMER = (
    "STRICTLY SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL, DIAGNOSTIC, "
    "OR PATIENT-CARE USE. No clinical certification claimed."
)
FIXED_ZIP_TIME = (2026, 11, 27, 0, 0, 0)

# 5x7 uppercase/digit/symbol bitmap table shared between Python builder, Win7 server, and ES5 JS
GLYPH_5X7 = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "/": ["00001", "00010", "00100", "00100", "01000", "10000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def sha256_seal(payload: dict) -> str:
    """Compute canonical Fieldglass SHA-256 digest before attaching report_sha256."""
    body = {k: v for k, v in payload.items() if k != "report_sha256"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_text_to_braille_lines(text: str) -> list[str]:
    """Encode short ASCII label into 2-row 2x4 Unicode Braille banner using Fieldglass DOT_BITS."""
    clean = "".join(ch if ch in GLYPH_5X7 else " " for ch in text.upper()[:16]) or "ZOE"
    bitmap_rows: list[list[int]] = [[] for _ in range(8)]
    for ch_idx, ch in enumerate(clean):
        glyph = GLYPH_5X7[ch]
        for r in range(7):
            bitmap_rows[r].extend(1 if c == "1" else 0 for c in glyph[r])
            if ch_idx < len(clean) - 1:
                bitmap_rows[r].append(0)
        bitmap_rows[7].extend([0] * (5 + (1 if ch_idx < len(clean) - 1 else 0)))
    if len(bitmap_rows[0]) % 2 == 1:
        for r in range(8):
            bitmap_rows[r].append(0)

    lines: list[str] = []
    width = len(bitmap_rows[0])
    for cy in (0, 4):
        chars: list[str] = []
        for cx in range(0, width, 2):
            mask = 0
            for dy in range(4):
                for dx in range(2):
                    if bitmap_rows[cy + dy][cx + dx]:
                        mask |= DOT_BITS[dy][dx]
            chars.append(chr(0x2800 + mask))
        lines.append("".join(chars))
    return lines


def simulated_ward_episodes() -> list[dict[str, float]]:
    """Deterministic 16-episode simulated non-clinical ambient ward-calm distributions."""
    raw_profiles = [
        # Episodes 0..7: Morning prep & daytime simulated corridor rounds
        [0.03, 0.06, 0.14, 0.22, 0.24, 0.16, 0.10, 0.05],
        [0.04, 0.07, 0.15, 0.21, 0.23, 0.15, 0.10, 0.05],
        [0.05, 0.09, 0.16, 0.20, 0.20, 0.14, 0.10, 0.06],
        [0.06, 0.11, 0.17, 0.18, 0.18, 0.13, 0.10, 0.07],
        [0.07, 0.12, 0.18, 0.17, 0.16, 0.13, 0.10, 0.07],
        [0.08, 0.13, 0.17, 0.16, 0.16, 0.12, 0.10, 0.08],
        [0.06, 0.11, 0.16, 0.19, 0.18, 0.14, 0.09, 0.07],
        [0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.09, 0.06],
        # Episodes 8..15: Simulated shift handoff -> quiet evening ward ambience
        [0.05, 0.08, 0.13, 0.21, 0.24, 0.15, 0.09, 0.05],
        [0.04, 0.07, 0.12, 0.22, 0.26, 0.16, 0.08, 0.05],
        [0.03, 0.06, 0.11, 0.22, 0.28, 0.17, 0.08, 0.05],
        [0.03, 0.05, 0.10, 0.21, 0.30, 0.18, 0.08, 0.05],
        [0.02, 0.05, 0.09, 0.20, 0.31, 0.20, 0.08, 0.05],
        [0.02, 0.04, 0.09, 0.19, 0.32, 0.21, 0.08, 0.05],
        [0.02, 0.04, 0.08, 0.19, 0.33, 0.21, 0.08, 0.05],
        [0.02, 0.04, 0.08, 0.20, 0.32, 0.21, 0.08, 0.05],
    ]
    episodes: list[dict[str, float]] = []
    for vec in raw_profiles:
        episodes.append(normalize_dist({s: vec[i] for i, s in enumerate(TONAL_STATES)}))
    return episodes


def build_chiasm_and_summary(out_dir: Path) -> tuple[dict, dict, list[str]]:
    episodes = simulated_ward_episodes()
    nexus_ep = 8
    past_avg = normalize_dist(
        {s: sum(ep[s] for ep in episodes[:nexus_ep]) / nexus_ep for s in TONAL_STATES}
    )
    future_avg = normalize_dist(
        {s: sum(ep[s] for ep in episodes[nexus_ep:]) / (len(episodes) - nexus_ep) for s in TONAL_STATES}
    )

    chiasm_nexus = causal_chiasm(past_avg, future_avg, tau=0.10, horizon=len(episodes) - nexus_ep)
    tomography = persistent_filtration_tomography(episodes, invariant_tau=0.14)

    a004 = [a_tau(list(ep.values()), 0.04) for ep in episodes]
    a010 = [a_tau(list(ep.values()), 0.10) for ep in episodes]
    a014 = [a_tau(list(ep.values()), 0.14) for ep in episodes]
    a020 = [a_tau(list(ep.values()), 0.20) for ep in episodes]
    h1_bits = [round(shannon_h1(list(ep.values())), 6) for ep in episodes]
    h2_bits = [round(renyi_h2(list(ep.values())), 6) for ep in episodes]
    m4_vals = [round(quartic_purity_m4(list(ep.values())), 6) for ep in episodes]

    write_chiasm_svg(
        out_dir / "chiasm_tomography.svg",
        title="ZOE HOSPITAL EDITION · CAUSAL CHIASM & FILTRATION TOMOGRAPHY",
        subtitle="Windows 7 SP1 (NT 6.1) Simulated Ambient Ward-Calm Drill — Non-Clinical / Educational Only",
        chiasm=chiasm_nexus,
        tomography=tomography,
        per_sec_a004=a004,
        per_sec_a010=a010,
        nexus_sec=nexus_ep,
    )

    braille_lines = render_text_to_braille_lines("ZOE WIN7")

    chiasm_report = {
        "slug": "zoe_hospital_win7",
        "title": "ZOE HOSPITAL EDITION (WIN7-ERA · SIMULATED / NON-CLINICAL)",
        "contract": CONTRACT,
        "equation": "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]",
        "episode_count": len(episodes),
        "nexus_episode": nexus_ep,
        "chiasm_nexus": chiasm_nexus,
        "persistent_filtration_tomography": tomography,
        "a_tau_series": {
            "tau_004": a004,
            "tau_010": a010,
            "tau_014": a014,
            "tau_020": a020,
            "h1_bits": h1_bits,
            "h2_bits": h2_bits,
            "m4_purity": m4_vals,
        },
        "braille_badge": {
            "label": "ZOE WIN7",
            "lines": braille_lines,
        },
        "chiasm_svg": "chiasm_tomography.svg",
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
        "clinical_use": False,
        "educational_simulation_only": True,
        "clinical_certification_claimed": False,
        "min_windows_version": MIN_WINDOWS_VERSION,
        "disclaimer": DISCLAIMER,
    }
    chiasm_report["report_sha256"] = sha256_seal(chiasm_report)
    (out_dir / "chiasm_report.json").write_text(
        json.dumps(chiasm_report, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "id": "zoe-hospital",
        "slug": "zoe-hospital",
        "title": "Zoe Hospital Edition (Windows 7-Era, Non-Clinical)",
        "subtitle": (
            "Offline ES5/HTA Kiosk & Python 3.7/3.8+ Stdlib Loopback Sandbox "
            "for Legacy Healthcare Workstations"
        ),
        "milestone": "M3",
        "requirement": "R3",
        "contract": CONTRACT,
        "entry_html": "index.html",
        "kiosk_html": "zoe_hospital_kiosk.html",
        "kiosk_hta": "zoe_hospital_kiosk.hta",
        "server_py": "zoe_hospital_win7.py",
        "launch_bat": "launch_win7.bat",
        "preview_png": "preview.png",
        "chiasm_svg": "chiasm_tomography.svg",
        "chiasm_report": "chiasm_report.json",
        "manifest": "manifest.json",
        "bundle_zip": "zoe_hospital_win7_bundle.zip",
        "readme_txt": "README_WIN7.txt",
        "min_windows_version": MIN_WINDOWS_VERSION,
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
        "clinical_use": False,
        "educational_simulation_only": True,
        "clinical_certification_claimed": False,
        "disclaimer": DISCLAIMER,
        "metrics": {
            "episode_count": len(episodes),
            "tau": chiasm_nexus["tau"],
            "past_accessible_volume": chiasm_nexus["past_accessible_volume"],
            "future_accessible_volume": chiasm_nexus["future_accessible_volume"],
            "chiasm_shift": chiasm_nexus["chiasm_shift"],
            "effective_information_bits": chiasm_nexus["effective_information_bits"],
            "presence_glyph": chiasm_nexus["presence_glyph"],
            "structural_invariants": tomography["structural_invariants"],
            "mean_h1_bits": round(sum(h1_bits) / len(h1_bits), 6),
            "mean_m4_purity": round(sum(m4_vals) / len(m4_vals), 6),
        },
        "highlights": [
            "Zero-CDN ES5 + HTA (mshta.exe) kiosk compatible with IE8-IE11 on Windows 7 SP1 (NT 6.1)",
            "Standalone Python 3.7/3.8+ stdlib-only HTTP/1.1 loopback server (127.0.0.1, zero ANSI escapes)",
            "Simulated hospital communication board, 2x4 Unicode Braille converter, Kloster A_tau(p) ward-calm simulator, and training checklist",
            "Strictly simulated/educational non-clinical framing across UI, manifests, and SHA-256 sealed Chiasm reports",
        ],
    }
    summary["report_sha256"] = sha256_seal(summary)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return chiasm_report, summary, braille_lines


def _load_font(size: int, bold: bool = False):
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for path_str in candidates:
        if Path(path_str).is_file():
            return ImageFont.truetype(path_str, size)
    return ImageFont.load_default()


def render_preview_png(out_dir: Path, chiasm_report: dict, braille_lines: list[str]) -> Path:
    """Render 1280x720 preview.png with Pillow and scrub all metadata via ffmpeg -map_metadata -1."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (11, 15, 23))
    d = ImageDraw.Draw(img)

    f_banner = _load_font(16, bold=True)
    f_title = _load_font(26, bold=True)
    f_sub = _load_font(15, bold=False)
    f_card_h = _load_font(16, bold=True)
    f_body = _load_font(14, bold=False)
    f_small = _load_font(12, bold=False)

    # Top non-clinical Ruby alert banner
    d.rounded_rectangle([20, 16, w - 20, 56], radius=6, fill=(44, 16, 26), outline=(244, 106, 126), width=2)
    d.text(
        (36, 26),
        "SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL USE - NO CLINICAL CERTIFICATION CLAIMED",
        fill=(244, 106, 126),
        font=f_banner,
    )

    # Header title block
    d.text((24, 72), "ZOE HOSPITAL EDITION  ·  WINDOWS 7 SP1 (NT 6.1)", fill=(242, 196, 92), font=f_title)
    d.text(
        (24, 108),
        "Offline ES5 / mshta.exe HTA Kiosk + Python 3.7/3.8+ Stdlib Loopback Sandbox (127.0.0.1)",
        fill=(94, 218, 238),
        font=f_sub,
    )

    # Left card: Windows 7 Runtime Stack & Non-Clinical Contract
    d.rounded_rectangle([24, 146, 626, 420], radius=8, fill=(18, 25, 38), outline=(42, 60, 85), width=2)
    d.text((42, 162), "01 / WINDOWS 7-ERA COMPATIBILITY MATRIX", fill=(94, 218, 238), font=f_card_h)
    rows_left = [
        ("Target OS:", "Windows 7 SP1 (NT 6.1) / x86 & x64"),
        ("Browser / HTA:", "IE8-IE11 + mshta.exe (X-UA-Compatible: IE=edge)"),
        ("JavaScript:", "Strict ES5 (var, function, zero CDN / zero fetch)"),
        ("CSS Layout:", "Explicit #hex + table/inline-block (no Grid/var)"),
        ("Local Server:", "Python 3.7/3.8+ stdlib HTTP/1.1 (127.0.0.1)"),
        ("Safety Flags:", "clinical_use=false | executed=false | tokens=0"),
    ]
    for idx, (k, v) in enumerate(rows_left):
        y = 202 + idx * 32
        d.text((42, y), k, fill=(242, 196, 92), font=f_body)
        d.text((190, y), v, fill=(234, 239, 245), font=f_body)

    # Right card: Kloster A_tau(p) Simulated Ward-Calm Trajectory
    d.rounded_rectangle([646, 146, w - 24, 420], radius=8, fill=(18, 25, 38), outline=(42, 60, 85), width=2)
    d.text((664, 162), "02 / KLOSTER A_tau(p_t) WARD-CALM SIMULATION", fill=(94, 218, 238), font=f_card_h)
    ch = chiasm_report["chiasm_nexus"]
    d.text(
        (664, 192),
        f"Glyph: {ch['presence_glyph']}  |  Past A_0.10={ch['past_accessible_volume']}  ->  Future A_0.10={ch['future_accessible_volume']}  |  EI={ch['effective_information_bits']:.3f} bits",
        fill=(242, 196, 92),
        font=f_small,
    )

    gx0, gy0, gx1, gy1 = 668, 224, w - 48, 388
    d.rectangle([gx0, gy0, gx1, gy1], fill=(9, 13, 21), outline=(42, 60, 85), width=1)
    a004 = chiasm_report["a_tau_series"]["tau_004"]
    a010 = chiasm_report["a_tau_series"]["tau_010"]
    n_eps = max(1, len(a010) - 1)
    pts_004 = [
        (
            int(round(gx0 + 14 + (i / n_eps) * (gx1 - gx0 - 28))),
            int(round(gy1 - 14 - (val / 8.0) * (gy1 - gy0 - 28))),
        )
        for i, val in enumerate(a004)
    ]
    pts_010 = [
        (
            int(round(gx0 + 14 + (i / n_eps) * (gx1 - gx0 - 28))),
            int(round(gy1 - 14 - (val / 8.0) * (gy1 - gy0 - 28))),
        )
        for i, val in enumerate(a010)
    ]
    nx = int(round(gx0 + 14 + (chiasm_report["nexus_episode"] / n_eps) * (gx1 - gx0 - 28)))
    d.line([(nx, gy0 + 4), (nx, gy1 - 4)], fill=(244, 106, 126), width=2)
    d.line(pts_004, fill=(94, 218, 238), width=3)
    d.line(pts_010, fill=(242, 196, 92), width=3)
    d.text((668, 396), "Cyan: A_0.04(p_t)   Gold: A_0.10(p_t)   Ruby line: Simulated Handoff Nexus", fill=(147, 166, 190), font=f_small)

    # Bottom Left card: 2x4 Unicode Braille Tactile Matrix (via Fieldglass DOT_BITS)
    d.rounded_rectangle([24, 438, 760, 666], radius=8, fill=(18, 25, 38), outline=(42, 60, 85), width=2)
    d.text((42, 454), "03 / 2x4 UNICODE BRAILLE TACTILE CONVERTER (DOT_BITS)", fill=(94, 218, 238), font=f_card_h)
    d.text((42, 480), "Offline 5x7 glyph -> U+2800..U+28FF + dot-matrix fallback for Win7 terminals", fill=(147, 166, 190), font=f_small)

    dot_step = 8
    cell_w = dot_step * 2 + 4
    cell_h = dot_step * 4 + 6
    ox, oy = 46, 514
    for r_idx, row_s in enumerate(braille_lines):
        cy = oy + r_idx * cell_h
        for c_idx, ch_b in enumerate(row_s):
            mask = ord(ch_b) - 0x2800
            cx = ox + c_idx * cell_w
            for dy in range(4):
                for dx in range(2):
                    px = cx + dx * dot_step
                    py = cy + dy * dot_step
                    lit = bool(mask & DOT_BITS[dy][dx])
                    col = (242, 236, 214) if lit else (28, 39, 56)
                    d.ellipse([px, py, px + 5, py + 5], fill=col)

    # Bottom Right card: Kiosk Modules & Bundle Seal
    d.rounded_rectangle([780, 438, w - 24, 666], radius=8, fill=(18, 25, 38), outline=(242, 196, 92), width=2)
    d.text((798, 454), "04 / OFFLINE KIOSK MODULES", fill=(242, 196, 92), font=f_card_h)
    modules = [
        "[1] Simulated Communication Drill Board",
        "[2] 2x4 Braille Tactile Matrix Converter",
        "[3] Kloster A_tau(p) Ward-Calm Simulator",
        "[4] Win7 Workstation Readiness Checklist",
        "[5] Portable Bundle: zoe_hospital_win7_bundle.zip",
    ]
    for idx, line in enumerate(modules):
        d.text((798, 492 + idx * 30), line, fill=(234, 239, 245), font=f_body)

    # Footer
    d.text(
        (24, 684),
        f"Contract: {CONTRACT}  |  Report SHA-256: {chiasm_report['report_sha256'][:24]}...  |  Zero Cloud Tokens ($0.00)",
        fill=(147, 166, 190),
        font=f_small,
    )

    raw_png = out_dir / "_raw_preview.png"
    final_png = out_dir / "preview.png"
    img.save(raw_png, format="PNG", optimize=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(raw_png),
            "-map_metadata",
            "-1",
            str(final_png),
        ],
        check=True,
    )
    raw_png.unlink(missing_ok=True)
    return final_png


def generate_win7_server_source() -> str:
    """Return standalone Python 3.7/3.8+ stdlib-only loopback HTTP/1.1 server source."""
    return '''#!/usr/bin/env python3
"""Zoe Hospital Edition (Windows 7-Era, Non-Clinical) Loopback HTTP/1.1 Server.

Standalone Python 3.7/3.8+ standard-library-only loopback server.
Strictly simulated/educational only -- NOT for clinical or diagnostic use.
Zero third-party imports, zero ANSI escape sequences, pure 7-bit ASCII console logs.
"""

import argparse
import hashlib
import http.server
import json
import math
import mimetypes
import os
import socketserver
import sys
import urllib.parse
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

CONTRACT = "fieldglass-causal-chiasm/v1"
MIN_WINDOWS_VERSION = "Windows 7 SP1 (NT 6.1)"
DISCLAIMER = (
    "STRICTLY SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL, DIAGNOSTIC, "
    "OR PATIENT-CARE USE. No clinical certification claimed."
)
ALLOWED_HOSTS = ("127.0.0.1", "localhost", "::1")

TONAL_STATES = (
    "deep_shadow",
    "ink_linework",
    "dark_midtone",
    "botanical_mid",
    "warm_sepia",
    "aged_paper",
    "bright_cream",
    "paper_highlight",
)

DOT_BITS = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

GLYPH_5X7 = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "/": ["00001", "00010", "00100", "00100", "01000", "10000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}

DEFAULT_PAST = {
    "deep_shadow": 0.055,
    "ink_linework": 0.098,
    "dark_midtone": 0.160,
    "botanical_mid": 0.196,
    "warm_sepia": 0.191,
    "aged_paper": 0.140,
    "bright_cream": 0.097,
    "paper_highlight": 0.063,
}

DEFAULT_FUTURE = {
    "deep_shadow": 0.029,
    "ink_linework": 0.052,
    "dark_midtone": 0.100,
    "botanical_mid": 0.206,
    "warm_sepia": 0.302,
    "aged_paper": 0.181,
    "bright_cream": 0.080,
    "paper_highlight": 0.050,
}


def validate_loopback_host(host: str) -> str:
    """Enforce loopback-only binding."""
    clean = host.strip()
    if clean not in ALLOWED_HOSTS:
        raise ValueError(
            "Loopback host required (127.0.0.1, localhost, or ::1); got: " + clean
        )
    return clean


def _require_finite_scalar(val: Any, name: str) -> float:
    if isinstance(val, bool):
        raise ValueError("%s must be a finite number, not bool" % name)
    try:
        num = float(val)
    except (TypeError, ValueError):
        raise ValueError("%s must be a finite number" % name)
    if not math.isfinite(num):
        raise ValueError("%s must be finite" % name)
    return num


def a_tau(values: List[float], tau: float) -> int:
    """Strict superlevel-set accessible volume: sum_x 1[p(x) > tau]."""
    t = _require_finite_scalar(tau, "tau")
    count = 0
    for val in values:
        if _require_finite_scalar(val, "value") > t:
            count += 1
    return count


def shannon_h1(values: List[float]) -> float:
    total = 0.0
    for val in values:
        p = _require_finite_scalar(val, "value")
        if p > 0.0:
            total -= p * math.log(p, 2)
    return total


def renyi_h2(values: List[float]) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    sq = 0.0
    for val in values:
        p = _require_finite_scalar(val, "value")
        sq += p * p
    return -math.log(max(sq, 1e-12), 2)


def quartic_purity_m4(values: List[float]) -> float:
    q = 0.0
    for val in values:
        p = _require_finite_scalar(val, "value")
        q += p * p * p * p
    return math.pow(q, 0.25)


def normalize_dist(dist: Dict[str, float]) -> Dict[str, float]:
    if not dist:
        raise ValueError("distribution cannot be empty")
    clean: Dict[str, float] = {}
    total = 0.0
    for k, v in dist.items():
        val = max(_require_finite_scalar(v, "weight"), 1e-9)
        clean[k] = val
        total += val
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("total weight must be finite and positive")
    norm: Dict[str, float] = {}
    max_k = None
    max_v = -1.0
    for k, v in clean.items():
        nv = v / total
        norm[k] = nv
        if nv > max_v:
            max_v = nv
            max_k = k
    others = sum(v for k, v in norm.items() if k != max_k)
    if max_k is not None:
        norm[max_k] = 1.0 - others
    return norm


def compute_chiasm(
    past_dist: Dict[str, float],
    future_dist: Dict[str, float],
    tau: float = 0.10,
    horizon: int = 8,
) -> Dict[str, Any]:
    t = _require_finite_scalar(tau, "tau")
    if t == 0.0:
        t = 0.0
    past = normalize_dist(past_dist)
    future = normalize_dist(future_dist)
    past_states = sorted(k for k, v in past.items() if v > t)
    future_states = sorted(k for k, v in future.items() if v > t)
    past_vol = len(past_states)
    future_vol = len(future_states)
    delta_vol = future_vol - past_vol

    ei_bits: Optional[float] = None
    if set(past.keys()) == set(future.keys()):
        kl = 0.0
        for k, pv in future.items():
            qv = max(past.get(k, 1e-12), 1e-12)
            if pv > 0.0:
                kl += pv * math.log(pv / qv, 2)
        ei_bits = round(max(0.0, kl), 6)

    future_boxed_in = (future_vol <= 1) and (past_vol > 1)
    if future_boxed_in:
        glyph = "??"
        meaning = "ambiguity alert: future boxed in while causal past remains unresolved"
    elif past_vol >= 2 and future_vol >= 2:
        glyph = "^_^"
        meaning = "corroborated chiasm: reversible future options preserved"
    else:
        glyph = "~"
        meaning = "still-looking: narrow repertoire"

    return {
        "contract": CONTRACT,
        "tau": t,
        "horizon": int(horizon),
        "past_repertoire": past,
        "future_repertoire": future,
        "past_accessible_volume": past_vol,
        "past_accessible_states": past_states,
        "future_accessible_volume": future_vol,
        "future_accessible_states": future_states,
        "chiasm_shift": delta_vol,
        "effective_information_bits": ei_bits,
        "future_boxed_in": future_boxed_in,
        "presence_glyph": glyph,
        "presence_meaning": meaning,
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
        "clinical_use": False,
        "educational_simulation_only": True,
        "clinical_certification_claimed": False,
        "min_windows_version": MIN_WINDOWS_VERSION,
        "disclaimer": DISCLAIMER,
    }


def text_to_braille(text: str) -> Dict[str, Any]:
    clean = "".join(ch if ch in GLYPH_5X7 else " " for ch in text.upper()[:16])
    if not clean:
        clean = "ZOE"
    rows: List[List[int]] = [[] for _ in range(8)]
    for idx, ch in enumerate(clean):
        glyph = GLYPH_5X7[ch]
        for r in range(7):
            for bit in glyph[r]:
                rows[r].append(1 if bit == "1" else 0)
            if idx < len(clean) - 1:
                rows[r].append(0)
        pad = 5 + (1 if idx < len(clean) - 1 else 0)
        for _ in range(pad):
            rows[7].append(0)
    if len(rows[0]) % 2 == 1:
        for r in range(8):
            rows[r].append(0)

    width = len(rows[0])
    braille_lines: List[str] = []
    for cy in (0, 4):
        chars: List[str] = []
        for cx in range(0, width, 2):
            mask = 0
            for dy in range(4):
                for dx in range(2):
                    if rows[cy + dy][cx + dx]:
                        mask |= DOT_BITS[dy][dx]
            chars.append(chr(0x2800 + mask))
        braille_lines.append("".join(chars))
    return {
        "ok": True,
        "text": clean,
        "cols": width // 2,
        "rows": braille_lines,
        "unicode_preview": "\\n".join(braille_lines),
        "dot_bits": [list(row) for row in DOT_BITS],
        "executed": False,
        "sentience_claimed": False,
        "clinical_use": False,
        "educational_simulation_only": True,
        "clinical_certification_claimed": False,
    }


def _sha256_seal(payload: Dict[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "report_sha256"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _reject_json_constant(token: str) -> None:
    raise ValueError("Invalid JSON constant: " + token)


def _validate_weight_dict(raw: Any, field_name: str, allow_list: bool = False) -> Dict[str, float]:
    clean: Dict[str, float] = {}
    total = 0.0
    if isinstance(raw, dict):
        if not raw:
            raise ValueError("%s must be a non-empty object" % field_name)
        for k, v in raw.items():
            if isinstance(v, bool):
                raise ValueError("%s weights must be numeric, not boolean" % field_name)
            try:
                w = float(v)
            except (ValueError, TypeError):
                raise ValueError("%s contains non-numeric weight" % field_name)
            if not math.isfinite(w) or w < 0.0:
                raise ValueError("%s weights must be finite and non-negative" % field_name)
            clean[str(k)] = w
            total += w
    elif allow_list and isinstance(raw, list):
        if not raw:
            raise ValueError("%s must be a non-empty array" % field_name)
        for idx, v in enumerate(raw):
            if isinstance(v, bool):
                raise ValueError("%s weights must be numeric, not boolean" % field_name)
            try:
                w = float(v)
            except (ValueError, TypeError):
                raise ValueError("%s contains non-numeric weight" % field_name)
            if not math.isfinite(w) or w < 0.0:
                raise ValueError("%s weights must be finite and non-negative" % field_name)
            clean["s_%d" % idx] = w
            total += w
    else:
        expected = "non-empty object or array" if allow_list else "non-empty object"
        raise ValueError("%s must be a %s" % (field_name, expected))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("%s total weight must be strictly positive" % field_name)
    return clean


def _safe_static_path(root_dir: str, url_path: str) -> Optional[str]:
    clean = url_path.split("?", 1)[0].split("#", 1)[0]
    if clean == "/" or clean == "":
        rel = "zoe_hospital_kiosk.html"
    else:
        rel = urllib.parse.unquote(clean.lstrip("/"))
    parts = [p for p in rel.replace("\\\\", "/").split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return None
    root_abs = os.path.abspath(root_dir)
    target = os.path.abspath(os.path.join(root_abs, *parts)) if parts else root_abs
    if target != root_abs and not target.startswith(root_abs + os.sep):
        return None
    return target


class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_handler(root_dir: str):
    abs_root = os.path.abspath(root_dir)

    class ZoeHospitalHandler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format_str: str, *args: Any) -> None:
            # Pure 7-bit ASCII logging for Windows 7 cmd.exe compatibility
            msg = format_str % args
            safe_msg = msg.encode("ascii", "replace").decode("ascii")
            sys.stdout.write("[zoe-hospital-win7] %s - %s\\n" % (self.address_string(), safe_msg))
            sys.stdout.flush()

        def _send_bytes(self, status: int, content_type: str, body: bytes, no_store: bool = False) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            if no_store:
                self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
            raw = (json.dumps(payload, indent=2, allow_nan=False) + "\\n").encode("utf-8")
            self._send_bytes(status, "application/json; charset=utf-8", raw, no_store=True)

        def _read_json_file(self, filename: str) -> Optional[Dict[str, Any]]:
            path = os.path.join(abs_root, filename)
            if not os.path.isfile(path):
                return None
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)

        def do_HEAD(self) -> None:
            self.do_GET()

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            route = parsed.path
            qs = urllib.parse.parse_qs(parsed.query)

            if route == "/api/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "contract": CONTRACT,
                        "min_windows_version": MIN_WINDOWS_VERSION,
                        "clinical_use": False,
                        "educational_simulation_only": True,
                        "clinical_certification_claimed": False,
                        "executed": False,
                        "sentience_claimed": False,
                        "tokens_used": 0,
                        "disclaimer": DISCLAIMER,
                    },
                )
                return

            if route == "/api/status":
                summary = self._read_json_file("summary.json")
                report = self._read_json_file("chiasm_report.json")
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "contract": CONTRACT,
                        "min_windows_version": MIN_WINDOWS_VERSION,
                        "clinical_use": False,
                        "educational_simulation_only": True,
                        "clinical_certification_claimed": False,
                        "executed": False,
                        "sentience_claimed": False,
                        "tokens_used": 0,
                        "disclaimer": DISCLAIMER,
                        "summary": summary,
                        "chiasm_sha256": report.get("report_sha256") if report else None,
                    },
                )
                return

            if route == "/api/chiasm":
                tau_raw = qs.get("tau", ["0.10"])[0]
                try:
                    tau_val = float(tau_raw)
                except ValueError:
                    self._send_json(400, {"ok": False, "error": "invalid tau parameter"})
                    return
                if not math.isfinite(tau_val) or not (0.0 <= tau_val <= 1.0):
                    self._send_json(400, {"ok": False, "error": "tau must be between 0.0 and 1.0"})
                    return
                if tau_val == 0.0:
                    tau_val = 0.0
                res = compute_chiasm(DEFAULT_PAST, DEFAULT_FUTURE, tau=tau_val, horizon=8)
                res["report_sha256"] = _sha256_seal(res)
                self._send_json(200, res)
                return

            if route == "/api/braille":
                txt = qs.get("text", ["ZOE WIN7"])[0]
                self._send_json(200, text_to_braille(txt))
                return

            if route == "/api/manifest":
                manifest = self._read_json_file("manifest.json")
                if manifest is None:
                    self._send_json(404, {"ok": False, "error": "manifest.json not found"})
                    return
                self._send_json(200, manifest)
                return

            target = _safe_static_path(abs_root, route)
            if target is None or not os.path.isfile(target):
                self._send_json(404, {"ok": False, "error": "not found"})
                return

            ctype, _ = mimetypes.guess_type(target)
            if target.endswith(".hta"):
                ctype = "application/hta; charset=utf-8"
            elif target.endswith(".svg"):
                ctype = "image/svg+xml; charset=utf-8"
            elif target.endswith(".json"):
                ctype = "application/json; charset=utf-8"
            elif ctype is None:
                ctype = "application/octet-stream"
            elif ctype.startswith("text/"):
                ctype = ctype + "; charset=utf-8"

            with open(target, "rb") as fh:
                data = fh.read()
            self._send_bytes(200, ctype, data, no_store=False)

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/api/metrics":
                self._send_json(404, {"ok": False, "error": "unknown POST endpoint"})
                return

            raw_len = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_len)
            except ValueError:
                self._send_json(400, {"ok": False, "error": "invalid Content-Length"})
                return
            if length <= 0 or length > 65536:
                self._send_json(400, {"ok": False, "error": "body must be 1..65536 bytes"})
                return

            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"), parse_constant=_reject_json_constant)
            except Exception:
                self._send_json(400, {"ok": False, "error": "invalid JSON body"})
                return

            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "JSON object required"})
                return

            if "tau" in payload:
                tau_val = payload["tau"]
                if isinstance(tau_val, bool):
                    self._send_json(400, {"ok": False, "error": "tau must be a finite number between 0.0 and 1.0"})
                    return
                try:
                    tau_f = float(tau_val)
                except (ValueError, TypeError):
                    self._send_json(400, {"ok": False, "error": "invalid tau"})
                    return
                if not math.isfinite(tau_f) or not (0.0 <= tau_f <= 1.0):
                    self._send_json(400, {"ok": False, "error": "tau must be a finite number between 0.0 and 1.0"})
                    return
            else:
                tau_f = 0.10
            if tau_f == 0.0:
                tau_f = 0.0

            try:
                if "distribution" in payload:
                    dist_clean = _validate_weight_dict(payload["distribution"], "distribution", allow_list=True)
                    norm = normalize_dist(dist_clean)
                else:
                    norm = normalize_dist(DEFAULT_FUTURE)

                vals = list(norm.values())
                chiasm_out = None
                if "future" in payload and payload["future"] is not None:
                    future_clean = _validate_weight_dict(payload["future"], "future", allow_list=False)
                    chiasm_out = compute_chiasm(norm, future_clean, tau=tau_f, horizon=1)
            except (ValueError, TypeError) as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
                return

            result: Dict[str, Any] = {
                "ok": True,
                "contract": CONTRACT,
                "tau": tau_f,
                "distribution": norm,
                "a_tau": a_tau(vals, tau_f),
                "accessible_states": sorted(k for k, v in norm.items() if v > tau_f),
                "shannon_h1_bits": round(shannon_h1(vals), 6),
                "renyi_h2_bits": round(renyi_h2(vals), 6),
                "quartic_purity_m4": round(quartic_purity_m4(vals), 6),
                "chiasm": chiasm_out,
                "executed": False,
                "sentience_claimed": False,
                "tokens_used": 0,
                "clinical_use": False,
                "educational_simulation_only": True,
                "clinical_certification_claimed": False,
                "min_windows_version": MIN_WINDOWS_VERSION,
                "disclaimer": DISCLAIMER,
            }
            result["report_sha256"] = _sha256_seal(result)
            self._send_json(200, result)

    return ZoeHospitalHandler


def run_self_test(root_dir: str) -> int:
    """Run deterministic self-tests including strict a_tau, Braille, loopback validation, and live HTTP/1.1."""
    # 1. Strict inequality check (p_i == tau excluded)
    assert a_tau([0.5, 0.25, 0.15, 0.10], 0.10) == 3
    assert a_tau([0.5, 0.25, 0.15, 0.10], 0.50) == 0

    # 2. Loopback host rejection check
    rejected = False
    try:
        validate_loopback_host("0.0.0.0")
    except ValueError:
        rejected = True
    assert rejected, "Non-loopback host must be rejected"

    # 3. Braille encoding check
    br = text_to_braille("ZOE WIN7")
    assert len(br["rows"]) == 2 and br["clinical_use"] is False and br["executed"] is False

    # 4. Chiasm invariant check
    ch = compute_chiasm(DEFAULT_PAST, DEFAULT_FUTURE, tau=0.10, horizon=8)
    assert ch["contract"] == CONTRACT
    assert ch["executed"] is False and ch["sentience_claimed"] is False and ch["tokens_used"] == 0
    assert ch["clinical_use"] is False and ch["educational_simulation_only"] is True
    assert ch["clinical_certification_claimed"] is False

    # 5. Live loopback HTTP/1.1 round-trip on ephemeral port 0
    import threading
    import urllib.request

    srv = _ThreadingHTTPServer(("127.0.0.1", 0), make_handler(root_dir))
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/health" % port, timeout=3) as resp:
            assert resp.status == 200
            health = json.loads(resp.read().decode("utf-8"))
            assert health["ok"] is True and health["clinical_use"] is False

        with urllib.request.urlopen("http://127.0.0.1:%d/api/chiasm?tau=0.10" % port, timeout=3) as resp:
            assert resp.status == 200
            ch_http = json.loads(resp.read().decode("utf-8"))
            assert ch_http["contract"] == CONTRACT and len(ch_http["report_sha256"]) == 64

        post_body = json.dumps({"tau": 0.10, "distribution": DEFAULT_FUTURE}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:%d/api/metrics" % port,
            data=post_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            met = json.loads(resp.read().decode("utf-8"))
            assert met["ok"] is True and met["clinical_use"] is False and met["executed"] is False
    finally:
        srv.shutdown()
        srv.server_close()

    sys.stdout.write(
        "SELF-TEST OK: Zoe Hospital Win7 Edition (Simulated/Non-Clinical) | "
        "contract=%s | a_tau_strict=OK | loopback=127.0.0.1 | clinical_use=false\\n" % CONTRACT
    )
    sys.stdout.flush()
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Zoe Hospital Edition (Windows 7-Era, Non-Clinical) Loopback Server"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Loopback bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8780, help="Port to bind (default: 8780, 0=ephemeral)")
    parser.add_argument(
        "--root",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Document root containing zoe_hospital_kiosk.html",
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-tests and exit")
    parser.add_argument("--once", action="store_true", help="Serve one HTTP request and exit")
    parser.add_argument("--no-browser", action="store_true", help="Do not launch default web browser")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        host = validate_loopback_host(args.host)
    except ValueError as exc:
        sys.stderr.write("ERROR: %s\\n" % str(exc))
        sys.stderr.flush()
        return 2

    root_dir = os.path.abspath(args.root)
    if args.self_test:
        return run_self_test(root_dir)

    srv_cls = http.server.HTTPServer if args.once else _ThreadingHTTPServer
    srv = srv_cls((host, int(args.port)), make_handler(root_dir))
    actual_port = srv.server_address[1]
    url_host = "[::1]" if host == "::1" else host
    url = "http://%s:%d/" % (url_host, actual_port)
    sys.stdout.write("ZOE HOSPITAL EDITION (WIN7-ERA / SIMULATED NON-CLINICAL)\\n")
    sys.stdout.write("DISCLAIMER: %s\\n" % DISCLAIMER)
    sys.stdout.write("ZOE_HOSPITAL_URL=%s\\n" % url)
    sys.stdout.flush()

    if not args.no_browser and not args.once:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        if args.once:
            srv.handle_request()
        else:
            srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def generate_kiosk_markup(is_hta: bool = False) -> str:
    """Generate strict ES5 / IE8-IE11 / mshta.exe compatible HTML or HTA kiosk."""
    glyph_json = json.dumps(GLYPH_5X7, sort_keys=True)
    tonal_json = json.dumps(list(TONAL_STATES))
    dot_bits_json = json.dumps([list(r) for r in DOT_BITS])

    hta_tag = ""
    if is_hta:
        hta_tag = (
            '  <HTA:APPLICATION ID="ZoeHospitalKiosk" '
            'APPLICATIONNAME="Zoe Hospital Edition (Simulated Non-Clinical)" '
            'BORDER="thick" BORDERSTYLE="normal" CAPTION="yes" '
            'MAXIMIZEBUTTON="yes" MINIMIZEBUTTON="yes" SCROLL="yes" '
            'SHOWINTASKBAR="yes" SINGLEINSTANCE="yes" SYSMENU="yes" '
            'VERSION="1.0" WINDOWSTATE="normal" />\n'
        )

    title_suffix = "HTA Desktop Kiosk" if is_hta else "Offline HTML Kiosk"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
{hta_tag}  <title>Zoe Hospital Edition ({title_suffix} - Simulated Non-Clinical)</title>
  <style type="text/css">
    body {{
      margin: 0;
      padding: 0;
      background-color: #0b0f17;
      color: #eaeff5;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    .wrap {{
      width: 96%;
      max-width: 1120px;
      margin: 0 auto;
      padding: 14px 8px 28px 8px;
    }}
    .alert-banner {{
      background-color: #2c101a;
      border: 2px solid #f46a7e;
      color: #ffdce2;
      padding: 10px 14px;
      margin-bottom: 12px;
      font-weight: bold;
      text-align: center;
      letter-spacing: 0.4px;
    }}
    .alert-tag {{
      color: #f46a7e;
      font-weight: bold;
    }}
    .header-box {{
      background-color: #121926;
      border: 1px solid #2a3c55;
      padding: 14px 16px;
      margin-bottom: 12px;
    }}
    .header-title {{
      margin: 0 0 4px 0;
      color: #f2c45c;
      font-size: 22px;
      font-weight: bold;
    }}
    .header-sub {{
      margin: 0;
      color: #93a6be;
      font-size: 13px;
    }}
    .nav-bar {{
      margin-bottom: 12px;
    }}
    .nav-btn {{
      display: inline-block;
      *display: inline;
      zoom: 1;
      background-color: #121926;
      color: #eaeff5;
      border: 1px solid #2a3c55;
      padding: 8px 14px;
      margin: 0 6px 6px 0;
      cursor: pointer;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      font-size: 13px;
      font-weight: bold;
    }}
    .nav-btn-active {{
      display: inline-block;
      *display: inline;
      zoom: 1;
      background-color: #1c2c42;
      color: #f2c45c;
      border: 2px solid #f2c45c;
      padding: 7px 13px;
      margin: 0 6px 6px 0;
      cursor: pointer;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      font-size: 13px;
      font-weight: bold;
    }}
    .panel {{
      background-color: #121926;
      border: 1px solid #2a3c55;
      padding: 14px 16px;
      margin-bottom: 14px;
    }}
    .panel-title {{
      margin: 0 0 8px 0;
      color: #5edaf0;
      font-size: 16px;
      font-weight: bold;
      border-bottom: 1px solid #2a3c55;
      padding-bottom: 6px;
    }}
    .muted {{
      color: #93a6be;
      font-size: 12px;
    }}
    .grid-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .grid-cell {{
      vertical-align: top;
      padding: 6px;
      width: 25%;
    }}
    .tile-btn {{
      width: 100%;
      min-height: 76px;
      background-color: #0e1420;
      border: 1px solid #2a3c55;
      color: #eaeff5;
      padding: 10px 8px;
      cursor: pointer;
      text-align: left;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      font-size: 13px;
    }}
    .tile-code {{
      color: #f2c45c;
      font-weight: bold;
      display: block;
      margin-bottom: 4px;
    }}
    .speech-draft {{
      background-color: #090d15;
      border: 2px solid #5edaf0;
      color: #eaeff5;
      padding: 12px 14px;
      margin: 10px 0;
      font-size: 17px;
      font-weight: bold;
    }}
    .btn-primary {{
      background-color: #1c2c42;
      color: #5edaf0;
      border: 1px solid #5edaf0;
      padding: 6px 12px;
      cursor: pointer;
      font-weight: bold;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
    }}
    .btn-gold {{
      background-color: #292212;
      color: #f2c45c;
      border: 1px solid #f2c45c;
      padding: 6px 12px;
      cursor: pointer;
      font-weight: bold;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
    }}
    .btn-ruby {{
      background-color: #2c101a;
      color: #f46a7e;
      border: 1px solid #f46a7e;
      padding: 6px 12px;
      cursor: pointer;
      font-weight: bold;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
    }}
    .txt-input {{
      background-color: #090d15;
      color: #eaeff5;
      border: 1px solid #2a3c55;
      padding: 6px 8px;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      font-size: 13px;
      width: 280px;
    }}
    .mono-box {{
      background-color: #090d15;
      border: 1px solid #2a3c55;
      color: #eaeff5;
      padding: 10px 12px;
      font-family: "Segoe UI Symbol", "DejaVu Sans Mono", "Courier New", monospace;
      font-size: 13px;
      white-space: pre-wrap;
      word-wrap: break-word;
      overflow-x: auto;
    }}
    .braille-unicode {{
      background-color: #090d15;
      border: 1px solid #2a3c55;
      color: #f2c45c;
      padding: 10px 12px;
      font-family: "Segoe UI Symbol", "DejaVu Sans Mono", "Courier New", monospace;
      font-size: 18px;
      line-height: 1.3;
      white-space: pre;
      overflow-x: auto;
    }}
    .dot-matrix-wrap {{
      background-color: #090d15;
      border: 1px solid #2a3c55;
      padding: 8px;
      overflow-x: auto;
      margin-top: 8px;
    }}
    .dot-table {{
      border-collapse: collapse;
    }}
    .dot-cell-on {{
      width: 6px;
      height: 6px;
      background-color: #f2ecd6;
      border: 1px solid #090d15;
      font-size: 1px;
      line-height: 1px;
    }}
    .dot-cell-off {{
      width: 6px;
      height: 6px;
      background-color: #182233;
      border: 1px solid #090d15;
      font-size: 1px;
      line-height: 1px;
    }}
    .bar-track {{
      width: 100%;
      background-color: #090d15;
      border: 1px solid #2a3c55;
      height: 16px;
    }}
    .bar-fill-hi {{
      background-color: #f2c45c;
      height: 16px;
    }}
    .bar-fill-lo {{
      background-color: #5edaf0;
      height: 16px;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}
    .data-table th, .data-table td {{
      border: 1px solid #2a3c55;
      padding: 6px 8px;
      text-align: left;
      font-size: 13px;
    }}
    .data-table th {{
      background-color: #0e1420;
      color: #5edaf0;
    }}
    .check-row {{
      padding: 6px 4px;
      border-bottom: 1px solid #1e2c40;
    }}
    .pill {{
      display: inline-block;
      *display: inline;
      zoom: 1;
      background-color: #0e1420;
      border: 1px solid #2a3c55;
      color: #5edaf0;
      padding: 2px 8px;
      margin-right: 6px;
      font-size: 12px;
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="alert-banner">
      <span class="alert-tag">NON-CLINICAL NOTICE:</span>
      SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL USE — NO CLINICAL CERTIFICATION CLAIMED
    </div>

    <div class="header-box">
      <div class="header-title">ZOE HOSPITAL EDITION · WINDOWS 7 SP1 (NT 6.1) KIOSK</div>
      <p class="header-sub">
        Offline ES5 / IE8–IE11 / mshta.exe Sandbox &nbsp;|&nbsp;
        <span class="pill">clinical_use = false</span>
        <span class="pill">educational_simulation_only = true</span>
        <span class="pill">executed = false</span>
        <span class="pill">tokens_used = 0</span>
      </p>
      <p class="muted" style="margin: 8px 0 0 0;">
        Runtime status: <span id="loopbackStatus">Offline local mode (file:// or mshta.exe)</span>
        &nbsp;<button type="button" class="btn-primary" id="btnRefreshLoopback">Check Loopback Server</button>
      </p>
    </div>

    <div class="nav-bar">
      <button type="button" class="nav-btn-active" id="tabBtnComm">1. Communication Drill Board</button>
      <button type="button" class="nav-btn" id="tabBtnBraille">2. 2x4 Braille Converter</button>
      <button type="button" class="nav-btn" id="tabBtnKloster">3. Kloster A_tau(p) Simulator</button>
      <button type="button" class="nav-btn" id="tabBtnChecklist">4. Win7 Readiness Checklist</button>
    </div>

    <!-- SECTION 1: SIMULATED HOSPITAL COMMUNICATION BOARD -->
    <div class="panel" id="panelComm">
      <div class="panel-title">01 / SIMULATED HOSPITAL COMMUNICATION BOARD (ACCESSIBILITY &amp; COMFORT DRILL)</div>
      <p class="muted">
        All phrase cards are strictly non-clinical educational accessibility drills. No patient records or medical orders are stored or transmitted.
      </p>
      <table class="grid-table">
        <tr>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile0"><span class="tile-code">[DRILL 01]</span>Hydration / Water Comfort Check</button></td>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile1"><span class="tile-code">[DRILL 02]</span>Dim Room Lighting / Quiet Hours</button></td>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile2"><span class="tile-code">[DRILL 03]</span>Adjust Blanket / Room Warmth</button></td>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile3"><span class="tile-code">[DRILL 04]</span>Simulated Family / Visitor Call</button></td>
        </tr>
        <tr>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile4"><span class="tile-code">[DRILL 05]</span>Language / Translation Support</button></td>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile5"><span class="tile-code">[DRILL 06]</span>Accessibility Braille Card Request</button></td>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile6"><span class="tile-code">[DRILL 07]</span>Quiet Posture / Pillow Support</button></td>
          <td class="grid-cell"><button type="button" class="tile-btn" id="commTile7"><span class="tile-code">[DRILL 08]</span>Routine Staff Check-In Drill</button></td>
        </tr>
      </table>

      <div class="speech-draft" id="commSpeechDraft">
        SIMULATED COMMUNICATION DRILL READY — Select a comfort drill tile or type a custom non-clinical drill message below.
      </div>

      <div style="margin: 8px 0;">
        <input type="text" class="txt-input" id="commCustomInput" value="Simulated comfort check: room lighting OK" />
        <button type="button" class="btn-gold" id="btnCommAdd">Add Simulated Draft</button>
        <button type="button" class="btn-primary" id="btnCommSpeak">Optional Speech Preview</button>
        <button type="button" class="btn-ruby" id="btnCommClear">Clear Drill Log</button>
        <span class="muted" id="speechSupportNote"></span>
      </div>

      <div class="mono-box" id="commLogBox">[SIMULATED LOG] Waiting for drill input...</div>
    </div>

    <!-- SECTION 2: 2x4 UNICODE BRAILLE TACTILE CONVERTER -->
    <div class="panel" id="panelBraille">
      <div class="panel-title">02 / 2x4 UNICODE BRAILLE TACTILE CONVERTER (FIELDGLASS DOT_BITS)</div>
      <p class="muted">
        Uses Fieldglass DOT_BITS (U+2800..U+28FF) and built-in 5x7 glyph bitmaps. Both Unicode Braille text and visual 2x4 dot cells are rendered offline.
      </p>
      <div style="margin-bottom: 10px;">
        <input type="text" class="txt-input" id="brailleInput" value="ZOE WIN7" maxlength="16" />
        <button type="button" class="btn-gold" id="btnBrailleRender">Render 2x4 Braille</button>
        <button type="button" class="btn-primary" id="btnBraillePreset1">QUIET ROOM</button>
        <button type="button" class="btn-primary" id="btnBraillePreset2">WATER DRILL</button>
      </div>
      <div class="muted" id="brailleStats"></div>
      <div class="braille-unicode" id="brailleUnicodeBox"></div>
      <div class="dot-matrix-wrap" id="brailleDotGrid"></div>
    </div>

    <!-- SECTION 3: KLOSTER A_tau(p) AMBIENT WARD-CALM SIMULATOR -->
    <div class="panel" id="panelKloster">
      <div class="panel-title">03 / KLOSTER A_tau(p) AMBIENT WARD-CALM SIMULATOR (STRICT &gt; TAU)</div>
      <p class="muted">
        Pure ES5 implementation of A_tau(p) = sum 1[p(x) &gt; tau], Shannon H1 (via Math.log/LN2), Renyi H2, quartic purity M4^(1/4), and Causal Chiasm decussation.
      </p>
      <div style="margin-bottom: 10px;">
        <button type="button" class="btn-gold" id="btnPresetQuiet">Preset: Quiet Night Ward</button>
        <button type="button" class="btn-primary" id="btnPresetHandoff">Preset: Shift Handoff Drill</button>
        <button type="button" class="btn-primary" id="btnPresetMorning">Preset: Morning Rounds Drill</button>
        &nbsp;&nbsp;
        <strong>Threshold tau:</strong>
        <select id="tauSelect" class="txt-input" style="width: 100px;">
          <option value="0.04">0.04</option>
          <option value="0.08">0.08</option>
          <option value="0.10" selected="selected">0.10</option>
          <option value="0.12">0.12</option>
          <option value="0.14">0.14</option>
          <option value="0.18">0.18</option>
          <option value="0.25">0.25</option>
        </select>
      </div>

      <table class="data-table" style="margin-bottom: 10px;">
        <tr>
          <th>Simulated Ambience Control (Non-Clinical)</th>
          <th>Level</th>
          <th>Adjust</th>
        </tr>
        <tr>
          <td>Acoustic Calm Weight</td>
          <td id="valAcoustic">70</td>
          <td>
            <button type="button" class="btn-primary" id="btnAcousticDown">-</button>
            <button type="button" class="btn-primary" id="btnAcousticUp">+</button>
          </td>
        </tr>
        <tr>
          <td>Soft Lighting Balance</td>
          <td id="valLight">65</td>
          <td>
            <button type="button" class="btn-primary" id="btnLightDown">-</button>
            <button type="button" class="btn-primary" id="btnLightUp">+</button>
          </td>
        </tr>
        <tr>
          <td>Corridor Activity Quietness</td>
          <td id="valTraffic">60</td>
          <td>
            <button type="button" class="btn-primary" id="btnTrafficDown">-</button>
            <button type="button" class="btn-primary" id="btnTrafficUp">+</button>
          </td>
        </tr>
      </table>

      <div class="mono-box" id="klosterSummaryBox"></div>
      <div id="klosterBarsBox" style="margin-top: 8px;"></div>
    </div>

    <!-- SECTION 4: NON-CLINICAL SHIFT-HANDOFF & WIN7 WORKSTATION READINESS CHECKLIST -->
    <div class="panel" id="panelChecklist">
      <div class="panel-title">04 / NON-CLINICAL SHIFT-HANDOFF &amp; WIN7 WORKSTATION READINESS CHECKLIST</div>
      <p class="muted">
        Local educational verification checklist for Windows 7 SP1 workstations. Zero data leaves this workstation.
      </p>
      <div id="checklistItems">
        <div class="check-row"><label><input type="checkbox" id="chk0" checked="checked" /> 1. Non-clinical / simulated-educational banner visibly displayed at top and footer</label></div>
        <div class="check-row"><label><input type="checkbox" id="chk1" checked="checked" /> 2. Zero-PHI rule confirmed (no real patient identifiers entered into drill logs)</label></div>
        <div class="check-row"><label><input type="checkbox" id="chk2" /> 3. Offline ES5 / HTA rendering verified without external CDN or internet access</label></div>
        <div class="check-row"><label><input type="checkbox" id="chk3" /> 4. Python 3.7/3.8+ loopback server bound strictly to 127.0.0.1 (if used)</label></div>
        <div class="check-row"><label><input type="checkbox" id="chk4" /> 5. 2x4 Unicode Braille dot-matrix legibility verified on local display</label></div>
        <div class="check-row"><label><input type="checkbox" id="chk5" /> 6. Batch launcher fallback (launch_win7.bat -&gt; mshta.exe / HTML) tested</label></div>
      </div>
      <div style="margin: 10px 0;">
        <strong>Readiness Progress:</strong> <span id="checklistProgress">2 / 6 Verified</span>
        &nbsp;&nbsp;
        <button type="button" class="btn-ruby" id="btnChecklistReset">Reset Checklist</button>
      </div>
      <div class="mono-box" id="checklistJsonBox"></div>
    </div>

    <div class="alert-banner" style="margin-top: 14px;">
      SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL USE — contract: fieldglass-causal-chiasm/v1 — executed=false — sentience_claimed=false — tokens_used=0
    </div>
  </div>

  <script type="text/javascript">
  /* <![CDATA[ */
  (function (root) {{
    var CONTRACT = "fieldglass-causal-chiasm/v1";
    var MIN_WIN = "Windows 7 SP1 (NT 6.1)";
    var DISCLAIMER = "STRICTLY SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL, DIAGNOSTIC, OR PATIENT-CARE USE. No clinical certification claimed.";
    var TONAL_STATES = {tonal_json};
    var DOT_BITS = {dot_bits_json};
    var GLYPH_5X7 = {glyph_json};

    function bindEvent(el, evt, fn) {{
      if (!el) {{ return; }}
      if (el.addEventListener) {{
        el.addEventListener(evt, fn, false);
      }} else if (el.attachEvent) {{
        el.attachEvent("on" + evt, fn);
      }} else {{
        el["on" + evt] = fn;
      }}
    }}

    function setText(el, txt) {{
      if (!el) {{ return; }}
      if (typeof el.textContent !== "undefined") {{
        el.textContent = txt;
      }} else {{
        el.innerText = txt;
      }}
    }}

    function trimStr(s) {{
      return String(s || "").replace(/^\\s+|\\s+$/g, "");
    }}

    function objectKeys(obj) {{
      var keys = [];
      var k;
      for (k in obj) {{
        if (Object.prototype.hasOwnProperty.call(obj, k)) {{
          keys.push(k);
        }}
      }}
      keys.sort();
      return keys;
    }}

    function escapeHtml(str) {{
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\\x22/g, "&quot;");
    }}

    function log2Safe(x) {{
      return Math.log(x) / Math.LN2;
    }}

    function roundTo(val, digits) {{
      var f = Math.pow(10, digits);
      return Math.round(val * f) / f;
    }}

    /* ---------- 1. Communication Board ---------- */
    var COMM_TILES = [
      "SIMULATED DRILL 01: Comfort hydration / water check requested.",
      "SIMULATED DRILL 02: Please dim room lighting for quiet rest hours.",
      "SIMULATED DRILL 03: Extra blanket or room temperature comfort check.",
      "SIMULATED DRILL 04: Simulated family / visitor call-back reminder.",
      "SIMULATED DRILL 05: Language / interpreter educational assistance drill.",
      "SIMULATED DRILL 06: 2x4 Braille tactile room card accessibility drill.",
      "SIMULATED DRILL 07: Posture / pillow comfort adjustment drill.",
      "SIMULATED DRILL 08: Routine simulated staff check-in completed."
    ];
    var commLog = [];

    function renderCommLog() {{
      var box = typeof document !== "undefined" ? document.getElementById("commLogBox") : null;
      if (!box) {{ return; }}
      if (commLog.length === 0) {{
        setText(box, "[SIMULATED LOG] Waiting for drill input...");
        return;
      }}
      setText(box, commLog.join("\\n"));
    }}

    function selectCommTile(idx) {{
      if (typeof idx !== "number" || !isFinite(idx) || idx < 0 || idx >= COMM_TILES.length) {{
        idx = 0;
      }} else {{
        idx = Math.floor(idx);
      }}
      var msg = COMM_TILES[idx] || COMM_TILES[0];
      var draftEl = typeof document !== "undefined" ? document.getElementById("commSpeechDraft") : null;
      if (draftEl) {{ setText(draftEl, msg); }}
      commLog.unshift("[TILE " + (idx + 1) + "] " + msg);
      if (commLog.length > 8) {{ commLog.pop(); }}
      renderCommLog();
      return msg;
    }}

    function addCustomCommNote(rawText) {{
      var cleaned = trimStr(rawText);
      if (!cleaned) {{ cleaned = "Simulated comfort note (empty input)"; }}
      var msg = "SIMULATED DRILL NOTE: " + cleaned;
      var draftEl = typeof document !== "undefined" ? document.getElementById("commSpeechDraft") : null;
      if (draftEl) {{ setText(draftEl, msg); }}
      commLog.unshift("[CUSTOM] " + msg);
      if (commLog.length > 8) {{ commLog.pop(); }}
      renderCommLog();
      return msg;
    }}

    function clearCommLog() {{
      commLog = [];
      var draftEl = typeof document !== "undefined" ? document.getElementById("commSpeechDraft") : null;
      if (draftEl) {{
        setText(draftEl, "SIMULATED COMMUNICATION DRILL READY — Log cleared.");
      }}
      renderCommLog();
    }}

    function speakCurrentDraft() {{
      var draftEl = typeof document !== "undefined" ? document.getElementById("commSpeechDraft") : null;
      var noteEl = typeof document !== "undefined" ? document.getElementById("speechSupportNote") : null;
      var txt = draftEl ? (draftEl.textContent || draftEl.innerText || "") : "";
      if (typeof window !== "undefined" && window.speechSynthesis && typeof SpeechSynthesisUtterance !== "undefined") {{
        try {{
          var utter = new SpeechSynthesisUtterance(txt);
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utter);
          if (noteEl) {{ setText(noteEl, "Local browser speechSynthesis triggered."); }}
          return true;
        }} catch (err) {{
          if (noteEl) {{ setText(noteEl, "Speech preview unavailable in this browser."); }}
          return false;
        }}
      }}
      if (noteEl) {{ setText(noteEl, "Text-only mode (IE8-IE11/HTA has no speechSynthesis API)."); }}
      return false;
    }}

    /* ---------- 2. 2x4 Unicode Braille Converter ---------- */
    function textToBrailleMatrix(inputText) {{
      var upper = trimStr(inputText).toUpperCase();
      if (!upper) {{ upper = "ZOE WIN7"; }}
      if (upper.length > 16) {{ upper = upper.substring(0, 16); }}

      var rows = [[], [], [], [], [], [], [], []];
      var i, r, c, ch, glyph, chBits;
      for (i = 0; i < upper.length; i++) {{
        ch = upper.charAt(i);
        glyph = GLYPH_5X7[ch] || GLYPH_5X7[" "];
        for (r = 0; r < 7; r++) {{
          chBits = glyph[r];
          for (c = 0; c < 5; c++) {{
            rows[r].push(chBits.charAt(c) === "1" ? 1 : 0);
          }}
          if (i < upper.length - 1) {{
            rows[r].push(0);
          }}
        }}
        for (c = 0; c < 5 + (i < upper.length - 1 ? 1 : 0); c++) {{
          rows[7].push(0);
        }}
      }}
      if (rows[0].length % 2 === 1) {{
        for (r = 0; r < 8; r++) {{
          rows[r].push(0);
        }}
      }}

      var width = rows[0].length;
      var bandStarts = [0, 4];
      var brailleLines = [];
      var b, cy, cx, dy, dx, mask, lineStr;
      for (b = 0; b < bandStarts.length; b++) {{
        cy = bandStarts[b];
        lineStr = "";
        for (cx = 0; cx < width; cx += 2) {{
          mask = 0;
          for (dy = 0; dy < 4; dy++) {{
            for (dx = 0; dx < 2; dx++) {{
              if (rows[cy + dy][cx + dx]) {{
                mask = mask | DOT_BITS[dy][dx];
              }}
            }}
          }}
          lineStr += String.fromCharCode(0x2800 + mask);
        }}
        brailleLines.push(lineStr);
      }}

      return {{
        text: upper,
        cols: width / 2,
        rows: rows,
        brailleLines: brailleLines,
        unicodeText: brailleLines.join("\\n"),
        cellCount: width,
        clinical_use: false,
        executed: false
      }};
    }}

    function renderBrailleOutput(inputText) {{
      var res = textToBrailleMatrix(inputText);
      var uniEl = typeof document !== "undefined" ? document.getElementById("brailleUnicodeBox") : null;
      var statsEl = typeof document !== "undefined" ? document.getElementById("brailleStats") : null;
      var gridEl = typeof document !== "undefined" ? document.getElementById("brailleDotGrid") : null;
      if (uniEl) {{ setText(uniEl, res.unicodeText); }}
      if (statsEl) {{
        setText(statsEl, "Label: " + res.text + " | Cells: " + res.cols + "x2 | Subpixels: " + (res.cols * 2) + "x8");
      }}
      if (gridEl) {{
        var htmlParts = ['<table class="dot-table">'];
        var r, c;
        for (r = 0; r < res.rows.length; r++) {{
          htmlParts.push("<tr>");
          for (c = 0; c < res.rows[r].length; c++) {{
            htmlParts.push(
              res.rows[r][c]
                ? '<td class="dot-cell-on">&nbsp;</td>'
                : '<td class="dot-cell-off">&nbsp;</td>'
            );
          }}
          htmlParts.push("</tr>");
        }}
        htmlParts.push("</table>");
        gridEl.innerHTML = htmlParts.join("");
      }}
      return res;
    }}

    /* ---------- 3. Kloster A_tau(p) & Causal Chiasm Simulator ---------- */
    function normalizeDist(distObj) {{
      var keys = objectKeys(distObj);
      if (keys.length === 0) {{
        throw new Error("distribution cannot be empty");
      }}
      var clean = {{}};
      var total = 0.0;
      var i, k, rawVal, v;
      for (i = 0; i < keys.length; i++) {{
        k = keys[i];
        rawVal = distObj[k];
        if (typeof rawVal === "boolean") {{
          throw new Error("distribution weights must be numeric, not boolean");
        }}
        v = parseFloat(rawVal);
        if (isNaN(v) || !isFinite(v)) {{
          throw new Error("distribution weights must be finite");
        }}
        if (v < 1e-9) {{ v = 1e-9; }}
        clean[k] = v;
        total += v;
      }}
      if (!isFinite(total) || total <= 0.0) {{
        throw new Error("distribution total weight must be finite and positive");
      }}
      var norm = {{}};
      var maxK = keys[0];
      var maxV = -1.0;
      for (i = 0; i < keys.length; i++) {{
        k = keys[i];
        norm[k] = clean[k] / total;
        if (norm[k] > maxV) {{
          maxV = norm[k];
          maxK = k;
        }}
      }}
      var others = 0.0;
      for (i = 0; i < keys.length; i++) {{
        k = keys[i];
        if (k !== maxK) {{ others += norm[k]; }}
      }}
      norm[maxK] = 1.0 - others;
      return norm;
    }}

    function aTau(distObj, tau) {{
      if (typeof tau === "boolean") {{
        throw new Error("tau must be finite");
      }}
      var t = parseFloat(tau);
      if (isNaN(t) || !isFinite(t)) {{
        throw new Error("tau must be finite");
      }}
      var keys = objectKeys(distObj);
      var cnt = 0;
      var i;
      for (i = 0; i < keys.length; i++) {{
        if (distObj[keys[i]] > t) {{
          cnt += 1;
        }}
      }}
      return cnt;
    }}

    function accessibleStates(distObj, tau) {{
      if (typeof tau === "boolean") {{
        throw new Error("tau must be finite");
      }}
      var t = parseFloat(tau);
      if (isNaN(t) || !isFinite(t)) {{
        throw new Error("tau must be finite");
      }}
      var keys = objectKeys(distObj);
      var out = [];
      var i;
      for (i = 0; i < keys.length; i++) {{
        if (distObj[keys[i]] > t) {{
          out.push(keys[i]);
        }}
      }}
      return out;
    }}

    function shannonH1(distObj) {{
      var keys = objectKeys(distObj);
      var h = 0.0;
      var i, p;
      for (i = 0; i < keys.length; i++) {{
        p = distObj[keys[i]];
        if (p > 0.0) {{
          h -= p * log2Safe(p);
        }}
      }}
      return h;
    }}

    function renyiH2(distObj) {{
      var keys = objectKeys(distObj);
      var sq = 0.0;
      var i, p;
      for (i = 0; i < keys.length; i++) {{
        p = distObj[keys[i]];
        sq += p * p;
      }}
      if (sq < 1e-12) {{ sq = 1e-12; }}
      return -log2Safe(sq);
    }}

    function quarticPurityM4(distObj) {{
      var keys = objectKeys(distObj);
      var q = 0.0;
      var i, p;
      for (i = 0; i < keys.length; i++) {{
        p = distObj[keys[i]];
        q += p * p * p * p;
      }}
      return Math.pow(q, 0.25);
    }}

    function causalChiasm(pastRaw, futureRaw, tau, horizon) {{
      if (typeof tau === "boolean") {{
        throw new Error("tau must be finite");
      }}
      var t = parseFloat(tau);
      if (isNaN(t) || !isFinite(t)) {{
        throw new Error("tau must be finite");
      }}
      if (t === 0) {{ t = 0; }}
      var past = normalizeDist(pastRaw);
      var future = normalizeDist(futureRaw);
      var pastStates = accessibleStates(past, t);
      var futureStates = accessibleStates(future, t);
      var pastVol = pastStates.length;
      var futureVol = futureStates.length;
      var deltaVol = futureVol - pastVol;

      var pastKeys = objectKeys(past);
      var futureKeys = objectKeys(future);
      var keysMatch = (pastKeys.length === futureKeys.length);
      var i, k, pv, qv;
      if (keysMatch) {{
        for (i = 0; i < pastKeys.length; i++) {{
          if (pastKeys[i] !== futureKeys[i]) {{
            keysMatch = false;
            break;
          }}
        }}
      }}
      var eiBits = null;
      if (keysMatch) {{
        var kl = 0.0;
        for (i = 0; i < futureKeys.length; i++) {{
          k = futureKeys[i];
          pv = future[k];
          qv = past[k] > 1e-12 ? past[k] : 1e-12;
          if (pv > 0.0) {{
            kl += pv * log2Safe(pv / qv);
          }}
        }}
        if (kl < 0.0) {{ kl = 0.0; }}
        eiBits = roundTo(kl, 6);
      }}

      var boxed = (futureVol <= 1) && (pastVol > 1);
      var glyph = "~";
      var meaning = "still-looking: narrow repertoire";
      if (boxed) {{
        glyph = "??";
        meaning = "ambiguity alert: future boxed in while causal past remains unresolved";
      }} else if (pastVol >= 2 && futureVol >= 2) {{
        glyph = "^_^";
        meaning = "corroborated chiasm: reversible future options preserved";
      }}

      return {{
        contract: CONTRACT,
        tau: t,
        horizon: horizon || 8,
        past_repertoire: past,
        future_repertoire: future,
        past_accessible_volume: pastVol,
        past_accessible_states: pastStates,
        future_accessible_volume: futureVol,
        future_accessible_states: futureStates,
        chiasm_shift: deltaVol,
        effective_information_bits: eiBits,
        future_boxed_in: boxed,
        presence_glyph: glyph,
        presence_meaning: meaning,
        h1_bits: roundTo(shannonH1(future), 6),
        h2_bits: roundTo(renyiH2(future), 6),
        m4_purity: roundTo(quarticPurityM4(future), 6),
        executed: false,
        sentience_claimed: false,
        tokens_used: 0,
        clinical_use: false,
        educational_simulation_only: true,
        clinical_certification_claimed: false,
        min_windows_version: MIN_WIN,
        disclaimer: DISCLAIMER
      }};
    }}

    var simState = {{
      acoustic: 70,
      light: 65,
      traffic: 60,
      tau: 0.10
    }};

    function buildSimulatedProfile(acoustic, light, traffic) {{
      var a = acoustic / 100.0;
      var l = light / 100.0;
      var tr = traffic / 100.0;
      return {{
        deep_shadow: 0.03 + 0.04 * (1.0 - l),
        ink_linework: 0.05 + 0.06 * (1.0 - tr),
        dark_midtone: 0.10 + 0.06 * (1.0 - a),
        botanical_mid: 0.16 + 0.08 * a,
        warm_sepia: 0.18 + 0.14 * ((a + l) * 0.5),
        aged_paper: 0.12 + 0.08 * l,
        bright_cream: 0.08 + 0.04 * tr,
        paper_highlight: 0.05 + 0.03 * tr
      }};
    }}

    function updateKlosterDisplay() {{
      var pastBase = buildSimulatedProfile(55, 50, 45);
      var futureNow = buildSimulatedProfile(simState.acoustic, simState.light, simState.traffic);
      var res = causalChiasm(pastBase, futureNow, simState.tau, 8);

      var acEl = typeof document !== "undefined" ? document.getElementById("valAcoustic") : null;
      var liEl = typeof document !== "undefined" ? document.getElementById("valLight") : null;
      var trEl = typeof document !== "undefined" ? document.getElementById("valTraffic") : null;
      if (acEl) {{ setText(acEl, String(simState.acoustic)); }}
      if (liEl) {{ setText(liEl, String(simState.light)); }}
      if (trEl) {{ setText(trEl, String(simState.traffic)); }}

      var sumEl = typeof document !== "undefined" ? document.getElementById("klosterSummaryBox") : null;
      if (sumEl) {{
        setText(
          sumEl,
          "Contract: " + res.contract + " | Presence: " + res.presence_glyph + " (" + res.presence_meaning + ")\\n" +
          "Past A_" + res.tau.toFixed(2) + " = " + res.past_accessible_volume +
          " | Future A_" + res.tau.toFixed(2) + " = " + res.future_accessible_volume +
          " | Chiasm Shift = " + (res.chiasm_shift >= 0 ? "+" : "") + res.chiasm_shift +
          " | EI = " + res.effective_information_bits + " bits\\n" +
          "H1 = " + res.h1_bits + " bits | H2 = " + res.h2_bits + " bits | M4^(1/4) = " + res.m4_purity + "\\n" +
          "executed=false | sentience_claimed=false | clinical_use=false | tokens_used=0"
        );
      }}

      var barsEl = typeof document !== "undefined" ? document.getElementById("klosterBarsBox") : null;
      if (barsEl) {{
        var parts = ['<table class="data-table"><tr><th>Simulated State</th><th>p(x)</th><th>Accessible (&gt; tau)</th></tr>'];
        var i, s, pv, pct, cls;
        for (i = 0; i < TONAL_STATES.length; i++) {{
          s = TONAL_STATES[i];
          pv = res.future_repertoire[s];
          pct = Math.min(100, Math.max(2, Math.round(pv * 240)));
          cls = pv > res.tau ? "bar-fill-hi" : "bar-fill-lo";
          parts.push(
            "<tr><td>" + escapeHtml(s) + "</td>" +
            "<td>" + pv.toFixed(4) + (pv > res.tau ? " [ACTIVE]" : "") + "</td>" +
            '<td style="width: 45%;"><div class="bar-track"><div class="' + cls + '" style="width: ' + pct + '%;"></div></div></td></tr>'
          );
        }}
        parts.push("</table>");
        barsEl.innerHTML = parts.join("");
      }}
      return res;
    }}

    /* ---------- 4. Readiness Checklist ---------- */
    function jsonEscapeStr(s) {{
      return '"' + String(s)
        .replace(/\\\\/g, "\\\\\\\\")
        .replace(/\\x22/g, '\\\\"')
        .replace(/\\r/g, "\\\\r")
        .replace(/\\n/g, "\\\\n")
        .replace(/\\t/g, "\\\\t") + '"';
    }}

    function serializeJsonFallback(val, depth) {{
      var pad = "";
      var childPad = "";
      var i, keys, parts;
      for (i = 0; i < depth; i++) {{ pad += "  "; }}
      childPad = pad + "  ";
      if (val === null || typeof val === "undefined") {{ return "null"; }}
      if (typeof val === "boolean") {{ return val ? "true" : "false"; }}
      if (typeof val === "number") {{
        return isFinite(val) ? String(val) : "null";
      }}
      if (typeof val === "string") {{ return jsonEscapeStr(val); }}
      if (Object.prototype.toString.call(val) === "[object Array]") {{
        if (val.length === 0) {{ return "[]"; }}
        parts = [];
        for (i = 0; i < val.length; i++) {{
          parts.push(childPad + serializeJsonFallback(val[i], depth + 1));
        }}
        return "[\\n" + parts.join(",\\n") + "\\n" + pad + "]";
      }}
      keys = objectKeys(val);
      if (keys.length === 0) {{ return "{{}}"; }}
      parts = [];
      for (i = 0; i < keys.length; i++) {{
        parts.push(childPad + jsonEscapeStr(keys[i]) + ": " + serializeJsonFallback(val[keys[i]], depth + 1));
      }}
      return "{{\\n" + parts.join(",\\n") + "\\n" + pad + "}}";
    }}

    function formatChecklistJson(report) {{
      if (typeof JSON !== "undefined" && JSON && typeof JSON.stringify === "function") {{
        return JSON.stringify(report, null, 2);
      }}
      return serializeJsonFallback(report, 0);
    }}

    function getChecklistSummary() {{
      var total = 6;
      var checkedCount = 0;
      var states = [];
      var i, el, isChecked;
      for (i = 0; i < total; i++) {{
        el = typeof document !== "undefined" ? document.getElementById("chk" + i) : null;
        isChecked = el ? !!el.checked : (i < 2);
        if (isChecked) {{ checkedCount += 1; }}
        states.push({{ item: i + 1, verified: isChecked }});
      }}
      var report = {{
        contract: CONTRACT,
        min_windows_version: MIN_WIN,
        clinical_use: false,
        educational_simulation_only: true,
        clinical_certification_claimed: false,
        executed: false,
        sentience_claimed: false,
        tokens_used: 0,
        verified_count: checkedCount,
        total_items: total,
        items: states
      }};
      var progEl = typeof document !== "undefined" ? document.getElementById("checklistProgress") : null;
      var jsonEl = typeof document !== "undefined" ? document.getElementById("checklistJsonBox") : null;
      if (progEl) {{ setText(progEl, checkedCount + " / " + total + " Verified"); }}
      if (jsonEl) {{ setText(jsonEl, formatChecklistJson(report)); }}
      return report;
    }}

    function resetChecklist() {{
      var i, el;
      for (i = 0; i < 6; i++) {{
        el = typeof document !== "undefined" ? document.getElementById("chk" + i) : null;
        if (el) {{ el.checked = false; }}
      }}
      return getChecklistSummary();
    }}

    /* ---------- Optional Loopback Server Sync (Only on http://) ---------- */
    function checkLoopbackServer() {{
      var statusEl = typeof document !== "undefined" ? document.getElementById("loopbackStatus") : null;
      var proto = typeof window !== "undefined" && window.location ? window.location.protocol : "file:";
      if (proto !== "http:" && proto !== "https:") {{
        if (statusEl) {{ setText(statusEl, "Offline local mode (" + proto + ") - zero network calls needed"); }}
        return false;
      }}
      var xhr = null;
      try {{
        if (typeof XMLHttpRequest !== "undefined") {{
          xhr = new XMLHttpRequest();
        }} else if (typeof ActiveXObject !== "undefined") {{
          xhr = new ActiveXObject("Microsoft.XMLHTTP");
        }}
        if (!xhr) {{ return false; }}
        xhr.open("GET", "/api/health", true);
        xhr.onreadystatechange = function () {{
          if (xhr.readyState === 4 && xhr.status === 200) {{
            if (typeof JSON !== "undefined" && JSON && typeof JSON.parse === "function") {{
              try {{
                var data = JSON.parse(xhr.responseText);
                if (statusEl) {{
                  setText(statusEl, "Connected to 127.0.0.1 loopback | clinical_use=" + data.clinical_use + " | " + data.min_windows_version);
                }}
              }} catch (parseErr) {{
                if (statusEl) {{ setText(statusEl, "Loopback connected (JSON parse skipped)"); }}
              }}
            }} else {{
              if (statusEl) {{ setText(statusEl, "Connected to 127.0.0.1 loopback (IE7 fallback mode)"); }}
            }}
          }}
        }};
        xhr.send(null);
        return true;
      }} catch (err) {{
        if (statusEl) {{ setText(statusEl, "Offline fallback active"); }}
        return false;
      }}
    }}

    /* ---------- Navigation Tabs ---------- */
    function switchTab(activeIdx) {{
      var btnIds = ["tabBtnComm", "tabBtnBraille", "tabBtnKloster", "tabBtnChecklist"];
      var panelIds = ["panelComm", "panelBraille", "panelKloster", "panelChecklist"];
      var i, b, p;
      for (i = 0; i < btnIds.length; i++) {{
        b = typeof document !== "undefined" ? document.getElementById(btnIds[i]) : null;
        p = typeof document !== "undefined" ? document.getElementById(panelIds[i]) : null;
        if (b) {{ b.className = (i === activeIdx) ? "nav-btn-active" : "nav-btn"; }}
        if (p) {{ p.style.display = (i === activeIdx) ? "block" : "none"; }}
      }}
    }}

    function clampVal(v, lo, hi) {{
      if (v < lo) {{ return lo; }}
      if (v > hi) {{ return hi; }}
      return v;
    }}

    function wireUiEvents() {{
      if (typeof document === "undefined") {{ return; }}
      var i;
      for (i = 0; i < 8; i++) {{
        (function (tileIdx) {{
          bindEvent(document.getElementById("commTile" + tileIdx), "click", function () {{
            selectCommTile(tileIdx);
          }});
        }}(i));
      }}
      bindEvent(document.getElementById("btnCommAdd"), "click", function () {{
        var inp = document.getElementById("commCustomInput");
        addCustomCommNote(inp ? inp.value : "");
      }});
      bindEvent(document.getElementById("btnCommSpeak"), "click", speakCurrentDraft);
      bindEvent(document.getElementById("btnCommClear"), "click", clearCommLog);

      bindEvent(document.getElementById("btnBrailleRender"), "click", function () {{
        var inp = document.getElementById("brailleInput");
        renderBrailleOutput(inp ? inp.value : "ZOE WIN7");
      }});
      bindEvent(document.getElementById("btnBraillePreset1"), "click", function () {{
        var inp = document.getElementById("brailleInput");
        if (inp) {{ inp.value = "QUIET ROOM"; }}
        renderBrailleOutput("QUIET ROOM");
      }});
      bindEvent(document.getElementById("btnBraillePreset2"), "click", function () {{
        var inp = document.getElementById("brailleInput");
        if (inp) {{ inp.value = "WATER DRILL"; }}
        renderBrailleOutput("WATER DRILL");
      }});

      bindEvent(document.getElementById("btnPresetQuiet"), "click", function () {{
        simState.acoustic = 88; simState.light = 82; simState.traffic = 85;
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnPresetHandoff"), "click", function () {{
        simState.acoustic = 60; simState.light = 65; simState.traffic = 45;
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnPresetMorning"), "click", function () {{
        simState.acoustic = 48; simState.light = 52; simState.traffic = 35;
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("tauSelect"), "change", function () {{
        var sel = document.getElementById("tauSelect");
        simState.tau = sel ? parseFloat(sel.value) : 0.10;
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnAcousticDown"), "click", function () {{
        simState.acoustic = clampVal(simState.acoustic - 10, 10, 100);
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnAcousticUp"), "click", function () {{
        simState.acoustic = clampVal(simState.acoustic + 10, 10, 100);
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnLightDown"), "click", function () {{
        simState.light = clampVal(simState.light - 10, 10, 100);
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnLightUp"), "click", function () {{
        simState.light = clampVal(simState.light + 10, 10, 100);
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnTrafficDown"), "click", function () {{
        simState.traffic = clampVal(simState.traffic - 10, 10, 100);
        updateKlosterDisplay();
      }});
      bindEvent(document.getElementById("btnTrafficUp"), "click", function () {{
        simState.traffic = clampVal(simState.traffic + 10, 10, 100);
        updateKlosterDisplay();
      }});

      for (i = 0; i < 6; i++) {{
        bindEvent(document.getElementById("chk" + i), "click", getChecklistSummary);
      }}
      bindEvent(document.getElementById("btnChecklistReset"), "click", resetChecklist);
      bindEvent(document.getElementById("btnRefreshLoopback"), "click", checkLoopbackServer);

      bindEvent(document.getElementById("tabBtnComm"), "click", function () {{ switchTab(0); }});
      bindEvent(document.getElementById("tabBtnBraille"), "click", function () {{ switchTab(1); }});
      bindEvent(document.getElementById("tabBtnKloster"), "click", function () {{ switchTab(2); }});
      bindEvent(document.getElementById("tabBtnChecklist"), "click", function () {{ switchTab(3); }});

      renderBrailleOutput("ZOE WIN7");
      updateKlosterDisplay();
      getChecklistSummary();
      checkLoopbackServer();
      switchTab(0);
    }}

    root.ZoeHospitalKiosk = {{
      contract: CONTRACT,
      minWindowsVersion: MIN_WIN,
      selectCommTile: selectCommTile,
      addCustomCommNote: addCustomCommNote,
      clearCommLog: clearCommLog,
      textToBrailleMatrix: textToBrailleMatrix,
      renderBrailleOutput: renderBrailleOutput,
      normalizeDist: normalizeDist,
      aTau: aTau,
      shannonH1: shannonH1,
      renyiH2: renyiH2,
      quarticPurityM4: quarticPurityM4,
      causalChiasm: causalChiasm,
      updateKlosterDisplay: updateKlosterDisplay,
      getChecklistSummary: getChecklistSummary,
      resetChecklist: resetChecklist,
      switchTab: switchTab
    }};

    if (typeof document !== "undefined") {{
      wireUiEvents();
    }}
  }}(typeof window !== "undefined" ? window : this));
  /* ]]> */
  </script>
</body>
</html>
'''


def generate_index_html(chiasm_report: dict, summary: dict) -> str:
    """Generate IE8-IE11 safe Observatory overview page docs/zoe-hospital/index.html."""
    esc = html.escape
    ch = chiasm_report["chiasm_nexus"]
    metrics = summary["metrics"]
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>Zoe Hospital Edition (Windows 7-Era, Non-Clinical) — Fieldglass Observatory</title>
  <style type="text/css">
    body {{
      margin: 0;
      padding: 0;
      background-color: #0b0f17;
      color: #eaeff5;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.5;
    }}
    a {{
      color: #5edaf0;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .wrap {{
      width: 96%;
      max-width: 1120px;
      margin: 0 auto;
      padding: 18px 10px 36px 10px;
    }}
    .alert-banner {{
      background-color: #2c101a;
      border: 2px solid #f46a7e;
      color: #ffdce2;
      padding: 12px 16px;
      margin-bottom: 16px;
      font-weight: bold;
      text-align: center;
    }}
    .hero {{
      background-color: #121926;
      border: 1px solid #2a3c55;
      padding: 18px 20px;
      margin-bottom: 16px;
    }}
    .hero-title {{
      margin: 0 0 6px 0;
      color: #f2c45c;
      font-size: 25px;
      font-weight: bold;
    }}
    .hero-sub {{
      margin: 0 0 10px 0;
      color: #93a6be;
      font-size: 14px;
    }}
    .btn-link {{
      display: inline-block;
      *display: inline;
      zoom: 1;
      background-color: #1c2c42;
      color: #f2c45c;
      border: 1px solid #f2c45c;
      padding: 8px 14px;
      margin: 4px 8px 4px 0;
      font-weight: bold;
      font-size: 13px;
    }}
    .btn-link-cyan {{
      display: inline-block;
      *display: inline;
      zoom: 1;
      background-color: #0e1420;
      color: #5edaf0;
      border: 1px solid #5edaf0;
      padding: 8px 14px;
      margin: 4px 8px 4px 0;
      font-weight: bold;
      font-size: 13px;
    }}
    .card {{
      background-color: #121926;
      border: 1px solid #2a3c55;
      padding: 16px 18px;
      margin-bottom: 16px;
    }}
    .card-title {{
      margin: 0 0 10px 0;
      color: #5edaf0;
      font-size: 17px;
      font-weight: bold;
      border-bottom: 1px solid #2a3c55;
      padding-bottom: 6px;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .data-table th, .data-table td {{
      border: 1px solid #2a3c55;
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }}
    .data-table th {{
      background-color: #0e1420;
      color: #f2c45c;
    }}
    .kpi-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .kpi-cell {{
      width: 25%;
      border: 1px solid #2a3c55;
      background-color: #0e1420;
      padding: 10px 12px;
      vertical-align: top;
    }}
    .kpi-label {{
      color: #93a6be;
      font-size: 12px;
    }}
    .kpi-val {{
      color: #f2c45c;
      font-size: 18px;
      font-weight: bold;
      margin-top: 4px;
    }}
    .code-block {{
      background-color: #090d15;
      border: 1px solid #2a3c55;
      padding: 10px 12px;
      font-family: "DejaVu Sans Mono", "Courier New", monospace;
      font-size: 13px;
      color: #eaeff5;
      white-space: pre-wrap;
    }}
    .preview-img {{
      width: 100%;
      max-width: 100%;
      height: auto;
      border: 1px solid #2a3c55;
      display: block;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="alert-banner">
      SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL, DIAGNOSTIC, OR PATIENT-CARE USE — NO CLINICAL CERTIFICATION CLAIMED
    </div>

    <div class="hero">
      <div class="hero-title">R3 · ZOE HOSPITAL EDITION (WINDOWS 7-ERA, NON-CLINICAL)</div>
      <p class="hero-sub">
        {esc(summary["subtitle"])} · Minimum Target: <strong>{esc(MIN_WINDOWS_VERSION)}</strong>
      </p>
      <div>
        <a class="btn-link" href="zoe_hospital_kiosk.html">Launch Offline HTML Kiosk (ES5)</a>
        <a class="btn-link" href="zoe_hospital_kiosk.hta">Download / Launch HTA Kiosk (mshta.exe)</a>
        <a class="btn-link-cyan" href="zoe_hospital_win7_bundle.zip">Download Portable Win7 ZIP Bundle</a>
        <a class="btn-link-cyan" href="../index.html">Back to Fieldglass Observatory</a>
      </div>
    </div>

    <div class="card">
      <div class="card-title">01 / KLOSTER A_tau(p) &amp; NON-CLINICAL INVARIANT SUMMARY</div>
      <table class="kpi-table">
        <tr>
          <td class="kpi-cell">
            <div class="kpi-label">Contract</div>
            <div class="kpi-val" style="font-size: 14px;">{esc(CONTRACT)}</div>
          </td>
          <td class="kpi-cell">
            <div class="kpi-label">Chiasm Presence ({metrics["episode_count"]} episodes)</div>
            <div class="kpi-val">{esc(ch["presence_glyph"])} ({ch["past_accessible_volume"]} &rarr; {ch["future_accessible_volume"]})</div>
          </td>
          <td class="kpi-cell">
            <div class="kpi-label">Effective Information</div>
            <div class="kpi-val">{ch["effective_information_bits"]:.4f} bits</div>
          </td>
          <td class="kpi-cell">
            <div class="kpi-label">Safety &amp; Cost Flags</div>
            <div class="kpi-val" style="font-size: 13px; color: #5edaf0;">clinical_use=false<br/>executed=false | tokens=0</div>
          </td>
        </tr>
      </table>
    </div>

    <div class="card">
      <div class="card-title">02 / WINDOWS 7 SP1 (NT 6.1) COMPATIBILITY MATRIX</div>
      <table class="data-table">
        <tr>
          <th>Component</th>
          <th>Target Win7 Runtime</th>
          <th>Compatibility Guard</th>
          <th>Artifact</th>
        </tr>
        <tr>
          <td>Offline HTML Kiosk</td>
          <td>IE8, IE9, IE10, IE11 &amp; Modern Browsers</td>
          <td>Strict ES5 JS (var/function), IE8 attachEvent/innerText shims, explicit hex CSS + table/inline-block layouts, zero CDNs</td>
          <td><a href="zoe_hospital_kiosk.html">zoe_hospital_kiosk.html</a></td>
        </tr>
        <tr>
          <td>Native Win7 Desktop App</td>
          <td>mshta.exe (Windows 7 SP1 Built-In)</td>
          <td>&lt;meta http-equiv="X-UA-Compatible" content="IE=edge" /&gt; + declarative &lt;HTA:APPLICATION&gt; (no COM JS access)</td>
          <td><a href="zoe_hospital_kiosk.hta">zoe_hospital_kiosk.hta</a></td>
        </tr>
        <tr>
          <td>Local Loopback Server</td>
          <td>Python 3.7 / 3.8+ (Stdlib Only)</td>
          <td>Py 3.7+ AST clean, zero third-party deps, 127.0.0.1 loopback-only, HTTP/1.1 exact Content-Length, zero ANSI escapes</td>
          <td><a href="zoe_hospital_win7.py">zoe_hospital_win7.py</a></td>
        </tr>
        <tr>
          <td>Workstation Launcher</td>
          <td>Windows 7 cmd.exe (cp437 / cp1252)</td>
          <td>CRLF line endings, probes py -3 / python &gt;= 3.7, automatic fallback to mshta.exe or default browser</td>
          <td><a href="launch_win7.bat">launch_win7.bat</a></td>
        </tr>
      </table>
    </div>

    <div class="card">
      <div class="card-title">03 / DEPLOYMENT INSTRUCTIONS (OFFLINE HOSPITAL SANDBOX WORKSTATION)</div>
      <div class="code-block">1. Copy zoe_hospital_win7_bundle.zip to the Windows 7 SP1 workstation via approved offline media.
2. Extract to C:\\ZoeHospital\\ (no internet access, no admin rights, no external CDNs required).
3. Double-click launch_win7.bat:
   - If Python 3.7/3.8+ is installed, starts http://127.0.0.1:8780/ with JSON APIs.
   - If Python is absent, automatically launches mshta.exe zoe_hospital_kiosk.hta (or zoe_hospital_kiosk.html).
4. Optional verification on workstation: python zoe_hospital_win7.py --self-test</div>
    </div>

    <div class="card">
      <div class="card-title">04 / VISUAL PREVIEW &amp; ARTIFACT INVENTORY</div>
      <p><img class="preview-img" src="preview.png" alt="Zoe Hospital Edition Preview" /></p>
      <table class="data-table">
        <tr><th>Artifact</th><th>Purpose</th></tr>
        <tr><td><a href="zoe_hospital_kiosk.html">zoe_hospital_kiosk.html</a></td><td>Offline ES5 interactive kiosk (Communication Board, 2x4 Braille, A_tau(p), Checklist)</td></tr>
        <tr><td><a href="zoe_hospital_kiosk.hta">zoe_hospital_kiosk.hta</a></td><td>Windows 7 mshta.exe desktop application wrapper</td></tr>
        <tr><td><a href="zoe_hospital_win7.py">zoe_hospital_win7.py</a></td><td>Standalone Python 3.7/3.8+ stdlib loopback server</td></tr>
        <tr><td><a href="launch_win7.bat">launch_win7.bat</a></td><td>Windows 7 CRLF batch launcher</td></tr>
        <tr><td><a href="chiasm_tomography.svg">chiasm_tomography.svg</a></td><td>Causal Chiasm &amp; Persistent Filtration Tomography vector diagram</td></tr>
        <tr><td><a href="chiasm_report.json">chiasm_report.json</a></td><td>SHA-256 sealed fieldglass-causal-chiasm/v1 telemetry report</td></tr>
        <tr><td><a href="manifest.json">manifest.json</a></td><td>SHA-256 package manifest &amp; runtime compatibility flags</td></tr>
        <tr><td><a href="summary.json">summary.json</a></td><td>Observatory summary metadata for programmatic integration</td></tr>
        <tr><td><a href="README_WIN7.txt">README_WIN7.txt</a></td><td>Plain-text Windows 7 deployment &amp; non-clinical guide</td></tr>
        <tr><td><a href="zoe_hospital_win7_bundle.zip">zoe_hospital_win7_bundle.zip</a></td><td>Portable offline ZIP package (&lt; 5 MB)</td></tr>
      </table>
    </div>

    <div class="alert-banner">
      SIMULATED / EDUCATIONAL ONLY — NOT FOR CLINICAL USE — Report SHA-256: {esc(chiasm_report["report_sha256"])}
    </div>
  </div>
</body>
</html>
'''


def generate_launch_bat() -> bytes:
    """Return CRLF Windows 7 batch launcher."""
    lines = [
        "@echo off",
        "setlocal",
        'cd /d "%~dp0"',
        "echo =============================================================================",
        "echo ZOE HOSPITAL EDITION (WINDOWS 7 SP1 COMPATIBLE - SIMULATED / NON-CLINICAL)",
        "echo STRICTLY SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL OR PATIENT-CARE USE",
        "echo =============================================================================",
        "",
        'py -3 -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,7) else 1)" >nul 2>&1',
        "if %errorlevel%==0 (",
        '    py -3 "%~dp0zoe_hospital_win7.py" %*',
        "    goto :eof",
        ")",
        "",
        'python -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,7) else 1)" >nul 2>&1',
        "if %errorlevel%==0 (",
        '    python "%~dp0zoe_hospital_win7.py" %*',
        "    goto :eof",
        ")",
        "",
        'if exist "%SystemRoot%\\System32\\mshta.exe" (',
        "    echo Python 3.7+ not found. Launching native Windows 7 HTA kiosk via mshta.exe...",
        '    start "" "%SystemRoot%\\System32\\mshta.exe" "%~dp0zoe_hospital_kiosk.hta"',
        "    goto :eof",
        ")",
        "",
        "echo Launching offline HTML kiosk in default browser...",
        'start "" "%~dp0zoe_hospital_kiosk.html"',
        "",
    ]
    return "\r\n".join(lines).encode("ascii")


def generate_readme_win7() -> bytes:
    """Return CRLF plain-ASCII Windows 7 README_WIN7.txt."""
    lines = [
        "ZOE HOSPITAL EDITION - WINDOWS 7 SP1 (NT 6.1) OFFLINE SANDBOX",
        "================================================================",
        "",
        "IMPORTANT NON-CLINICAL NOTICE:",
        "  STRICTLY SIMULATED / EDUCATIONAL ONLY - NOT FOR CLINICAL, DIAGNOSTIC,",
        "  OR PATIENT-CARE USE. No clinical certification is claimed.",
        "  clinical_use=false | educational_simulation_only=true | executed=false",
        "",
        "SUPPORTED WINDOWS 7-ERA ENVIRONMENTS:",
        "  - Windows 7 SP1 (NT 6.1) x86 / x64",
        "  - Built-in mshta.exe (zoe_hospital_kiosk.hta, zero Python required)",
        "  - Internet Explorer 8 through 11 (zoe_hospital_kiosk.html, strict ES5)",
        "  - Python 3.7 / 3.8+ standard library only (zoe_hospital_win7.py)",
        "",
        "QUICK START:",
        "  1. Extract all files from zoe_hospital_win7_bundle.zip into a local folder.",
        "  2. Double-click launch_win7.bat (or double-click zoe_hospital_kiosk.hta).",
        "  3. If Python 3.7/3.8+ is available, the server binds 127.0.0.1:8780 only.",
        "  4. Run self-test anytime: python zoe_hospital_win7.py --self-test",
        "",
        "INCLUDED MODULES:",
        "  - Simulated Hospital Communication Board (non-clinical accessibility drills)",
        "  - 2x4 Unicode Braille Tactile Converter (U+2800..U+28FF + dot grid)",
        "  - Kloster A_tau(p) Ambient Ward-Calm Simulator & Causal Chiasm",
        "  - Win7 Workstation & Non-Clinical Readiness Checklist",
        "",
    ]
    return "\r\n".join(lines).encode("ascii")


def write_manifest_and_zip(out_dir: Path) -> None:
    core_filenames = [
        "index.html",
        "zoe_hospital_kiosk.html",
        "zoe_hospital_kiosk.hta",
        "zoe_hospital_win7.py",
        "launch_win7.bat",
        "chiasm_tomography.svg",
        "chiasm_report.json",
        "summary.json",
        "preview.png",
        "README_WIN7.txt",
    ]
    file_entries = []
    for name in core_filenames:
        raw = (out_dir / name).read_bytes()
        file_entries.append(
            {
                "path": name,
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
            }
        )

    manifest = {
        "package": "zoe-hospital-win7-edition",
        "version": "1.0.0",
        "contract": CONTRACT,
        "min_windows_version": MIN_WINDOWS_VERSION,
        "supported_runtimes": [
            "Internet Explorer 8-11 / mshta.exe (ES5-only JS, IE8-safe CSS, zero external CDNs)",
            "Python 3.7 / 3.8+ stdlib-only loopback HTTP/1.1 server (127.0.0.1, zero ANSI escapes)",
        ],
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
        "clinical_use": False,
        "educational_simulation_only": True,
        "clinical_certification_claimed": False,
        "disclaimer": DISCLAIMER,
        "bundle_zip": "zoe_hospital_win7_bundle.zip",
        "files": file_entries,
    }
    manifest["report_sha256"] = sha256_seal(manifest)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    bundle_members = [
        "index.html",
        "zoe_hospital_kiosk.html",
        "zoe_hospital_kiosk.hta",
        "zoe_hospital_win7.py",
        "launch_win7.bat",
        "manifest.json",
        "chiasm_tomography.svg",
        "chiasm_report.json",
        "summary.json",
        "preview.png",
        "README_WIN7.txt",
    ]
    zip_path = out_dir / "zoe_hospital_win7_bundle.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(bundle_members):
            data = (out_dir / name).read_bytes()
            info = zipfile.ZipInfo(filename=name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)


def build_all(out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    chiasm_report, summary, braille_lines = build_chiasm_and_summary(out_dir)
    render_preview_png(out_dir, chiasm_report, braille_lines)
    (out_dir / "zoe_hospital_win7.py").write_text(
        generate_win7_server_source(), encoding="utf-8"
    )
    (out_dir / "zoe_hospital_kiosk.html").write_text(
        generate_kiosk_markup(is_hta=False), encoding="utf-8"
    )
    (out_dir / "zoe_hospital_kiosk.hta").write_text(
        generate_kiosk_markup(is_hta=True), encoding="utf-8"
    )
    (out_dir / "index.html").write_text(
        generate_index_html(chiasm_report, summary), encoding="utf-8"
    )
    (out_dir / "launch_win7.bat").write_bytes(generate_launch_bat())
    (out_dir / "README_WIN7.txt").write_bytes(generate_readme_win7())
    write_manifest_and_zip(out_dir)
    return out_dir


def main() -> int:
    out_dir = build_all(OUT_DIR)
    print(f"Built R3 Zoe Hospital Edition (Win7-Era, Non-Clinical) in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
