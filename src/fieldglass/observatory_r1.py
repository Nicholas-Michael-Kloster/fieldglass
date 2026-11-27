"""Deterministic R1 domain engines and telemetry helpers for Fieldglass Observatory.

Covers four educational domains under zero cloud tokens ($0.00):
  1. MSDOS8086Model: 16-bit 8086 registers, 640 KB conventional/UMA/HMA memory map,
     1.44 MB FAT12 geometry & virtual volume, and interactive COMMAND.COM shell.
  2. FlightSim6DOF: ISA atmosphere, 6-DOF aerodynamic lift/drag/thrust/stall/bank-to-turn
     integrator, flight presets, and six-pack HUD derivation.
  3. MedicalSandboxModel: STRICTLY SIMULATED / EDUCATIONAL / NON-CLINICAL biomedical
     physics models (synthetic ECG PQRST, Beer-Lambert SpO2, capnography,
     ventilator P-V loop, and dimensional-analysis infusion calculator).
  4. SoftwareObservatoryModel: 6-stage Fieldglass pipeline metadata, live Kloster A_tau(p)
     repertoire evaluator, SHA-256 Causal Chiasm verifier, and Win7-to-Modern matrix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
from PIL import Image

from .metrics import (
    CONTRACT,
    DEFAULT_THRESHOLDS,
    a_tau,
    accessible_set,
    causal_chiasm,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)

CHIASM_CONTRACT = CONTRACT
SUMMARY_CONTRACT = "fieldglass-r1-summary/v1"
EQUATION = "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]"

OBSERVATORY_PALETTE: dict[str, str] = {
    "bg": "#0b0f17",
    "panel": "#121926",
    "panel2": "#0e1420",
    "border": "#2a3c55",
    "gold": "#f2c45c",
    "cyan": "#5edaf0",
    "ruby": "#f46a7e",
    "text": "#eaeff5",
    "muted": "#93a6be",
    "parchment": "#f6f1e4",
    "ink": "#1b1916",
}

DISCLAIMER = (
    "STRICTLY SIMULATED / EDUCATIONAL SANDBOX ONLY — NOT FOR CLINICAL, "
    "DIAGNOSTIC, OR PATIENT-CARE USE."
)

NON_CLINICAL_FLAGS: dict[str, Any] = {
    "clinical_use": False,
    "educational_simulation_only": True,
    "clinical_certification_claimed": False,
    "executed": False,
    "sentience_claimed": False,
    "tokens_used": 0,
    "disclaimer": DISCLAIMER,
}


def _require_finite_num(val: Any, name: str) -> float:
    """Validate that val is a finite real number (rejecting bool, np.bool_, NaN, Inf, -Inf)."""
    if isinstance(val, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite number, not bool")
    if isinstance(val, np.ndarray):
        cur: Any = val
        seen: set[int] = set()
        while isinstance(cur, np.ndarray):
            obj_id = id(cur)
            if obj_id in seen:
                raise ValueError(f"{name} must be a scalar finite number")
            seen.add(obj_id)
            if cur.ndim != 0:
                raise ValueError(f"{name} must be a scalar finite number")
            if cur.dtype == np.bool_:
                raise ValueError(f"{name} must be a finite number, not bool")
            if cur.dtype == object:
                cur = cur.item()
            else:
                break
        if isinstance(cur, (bool, np.bool_)):
            raise ValueError(f"{name} must be a finite number, not bool")
    try:
        num = float(val)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(num):
        raise ValueError(f"{name} must be finite")
    return num


def canonical_sha256(obj: dict[str, Any]) -> str:
    """Compute canonical SHA-256 over JSON with sort_keys=True, compact separators, ensure_ascii=True."""
    clean = {k: v for k, v in obj.items() if k != "report_sha256"}
    payload = json.dumps(
        clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seal_chiasm_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach canonical Fieldglass safety invariants and report_sha256 seal."""
    sealed = dict(payload)
    sealed.pop("report_sha256", None)
    sealed["contract"] = CHIASM_CONTRACT
    sealed["equation"] = EQUATION
    sealed["executed"] = False
    sealed["sentience_claimed"] = False
    sealed["tokens_used"] = 0
    sealed["report_sha256"] = canonical_sha256(sealed)
    return sealed


def verify_report_sha256(report: dict[str, Any]) -> bool:
    """Verify that report_sha256 matches the recomputed canonical SHA-256 digest."""
    if not isinstance(report, dict):
        return False
    digest = report.get("report_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    try:
        expected = canonical_sha256(report)
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(digest.lower(), expected.lower())


def strip_png_metadata(png_path: str | Path) -> Path:
    """Rewrite a PNG without EXIF/GPS/text metadata chunks."""
    p = Path(png_path).expanduser().resolve()
    with Image.open(p) as im:
        clean = im.convert("RGB") if im.mode not in ("RGB", "RGBA", "L") else im.copy()
    clean.save(p, format="PNG", optimize=True)
    return p


def compute_distribution_telemetry(
    episodes: Sequence[dict[str, float]],
    *,
    tau: float = 0.10,
    nexus_idx: int | None = None,
    horizon: int = 4,
) -> dict[str, Any]:
    """Compute Kloster A_tau, Shannon H1, Renyi H2, M4^(1/4), Causal Chiasm, and Filtration Tomography."""
    tau_f = _require_finite_num(tau, "tau")
    if tau_f == 0.0:
        tau_f = 0.0
    if len(episodes) < 2:
        raise ValueError("At least 2 episode distributions are required for Causal Chiasm telemetry.")
    norm_eps = [normalize_dist(ep) for ep in episodes]
    keys = list(norm_eps[0].keys())

    per_ep_metrics: list[dict[str, Any]] = []
    a004_series: list[int] = []
    a010_series: list[int] = []
    for idx, ep in enumerate(norm_eps):
        vec = np.array([ep[k] for k in keys], dtype=np.float64)
        a004 = a_tau(vec, 0.04)
        a010 = a_tau(vec, tau_f)
        a004_series.append(a004)
        a010_series.append(a010)
        per_ep_metrics.append(
            {
                "episode": idx,
                "a_004": a004,
                "a_010": a010,
                "h1_bits": round(shannon_h1(vec), 6),
                "h2_bits": round(renyi_h2(vec), 6),
                "m4_purity": round(quartic_purity_m4(vec), 6),
            }
        )

    mid = nexus_idx if nexus_idx is not None else len(norm_eps) // 2
    mid = max(1, min(len(norm_eps) - 1, mid))
    past_avg = normalize_dist({k: float(np.mean([ep[k] for ep in norm_eps[:mid]])) for k in keys})
    fut_avg = normalize_dist({k: float(np.mean([ep[k] for ep in norm_eps[mid:]])) for k in keys})

    chiasm_res = causal_chiasm(past_avg, fut_avg, tau=tau_f, horizon=horizon)
    tomo_res = persistent_filtration_tomography(
        norm_eps, thresholds=DEFAULT_THRESHOLDS, invariant_tau=0.14
    )
    return {
        "episode_count": len(norm_eps),
        "nexus_ep": mid,
        "episodes": norm_eps,
        "per_episode": per_ep_metrics,
        "per_ep_a004": a004_series,
        "per_ep_a010": a010_series,
        "h1_mean_bits": round(float(np.mean([m["h1_bits"] for m in per_ep_metrics])), 4),
        "h2_mean_bits": round(float(np.mean([m["h2_bits"] for m in per_ep_metrics])), 4),
        "m4_mean_purity": round(float(np.mean([m["m4_purity"] for m in per_ep_metrics])), 4),
        "chiasm_nexus": chiasm_res,
        "persistent_filtration_tomography": tomo_res,
    }


# ---------------------------------------------------------------------------
# Domain 1: MS-DOS 6.22 / 8086 Real-Mode Educational Simulator
# ---------------------------------------------------------------------------

FLAG_MASKS: dict[str, int] = {
    "CF": 0x0001,
    "PF": 0x0004,
    "AF": 0x0010,
    "ZF": 0x0040,
    "SF": 0x0080,
    "TF": 0x0100,
    "IF": 0x0200,
    "DF": 0x0400,
    "OF": 0x0800,
}

MSDOS_MEMORY_REGIONS: list[dict[str, Any]] = [
    {"region": "IVT", "area": "Conventional", "start": 0x00000, "end": 0x003FF, "bytes": 1_024, "desc": "256 real-mode interrupt vectors"},
    {"region": "BIOS_DATA", "area": "Conventional", "start": 0x00400, "end": 0x004FF, "bytes": 256, "desc": "BIOS Data Area (COM/LPT/kbd buffer)"},
    {"region": "DOS_COMM", "area": "Conventional", "start": 0x00500, "end": 0x006FF, "bytes": 512, "desc": "DOS communication & PrintScreen status"},
    {"region": "IO_MSDOS_SYS", "area": "Conventional", "start": 0x00700, "end": 0x06DFF, "bytes": 26_368, "desc": "IO.SYS + MSDOS.SYS resident kernel"},
    {"region": "COMMAND_RESIDENT", "area": "Conventional", "start": 0x06E00, "end": 0x09FFF, "bytes": 12_800, "desc": "COMMAND.COM resident stub & env"},
    {"region": "FREE_TPA", "area": "Conventional", "start": 0x0A000, "end": 0x9FFFF, "bytes": 614_400, "desc": "Free Transient Program Area (600 KB)"},
    {"region": "VGA_VRAM", "area": "UMA", "start": 0xA0000, "end": 0xBFFFF, "bytes": 131_072, "desc": "VGA planar graphics & CGA/MDA text"},
    {"region": "UMB_HIMEM_EMM386", "area": "UMA", "start": 0xC0000, "end": 0xEFFFF, "bytes": 196_608, "desc": "Upper Memory Blocks / option ROMs"},
    {"region": "SYSTEM_BIOS", "area": "UMA", "start": 0xF0000, "end": 0xFFFFF, "bytes": 65_536, "desc": "POST & system ROM BIOS"},
    {"region": "HMA_HIGH", "area": "HMA", "start": 0x100000, "end": 0x10FFEF, "bytes": 65_520, "desc": "High Memory Area (64 KB - 16 B, DOS=HIGH)"},
]

FAT12_GEOMETRY: dict[str, int] = {
    "bytes_per_sector": 512,
    "sectors_per_cluster": 1,
    "reserved_sectors": 1,
    "num_fats": 2,
    "sectors_per_fat": 9,
    "root_entries": 224,
    "root_sectors": 14,
    "data_start_sector": 33,
    "total_sectors": 2880,
    "total_bytes": 1_474_560,
    "data_clusters": 2847,
}

MSDOS_VIRTUAL_FILES: list[dict[str, Any]] = [
    {"name": "IO.SYS", "bytes": 40_774, "attr": "RHS", "date": "05-31-94", "time": "6:22a", "clusters": "2..81", "hidden": True, "content": None},
    {"name": "MSDOS.SYS", "bytes": 38_138, "attr": "RHS", "date": "05-31-94", "time": "6:22a", "clusters": "82..156", "hidden": True, "content": None},
    {"name": "COMMAND.COM", "bytes": 54_645, "attr": "A", "date": "05-31-94", "time": "6:22a", "clusters": "157..263", "hidden": False, "content": None},
    {
        "name": "CONFIG.SYS",
        "bytes": 142,
        "attr": "A",
        "date": "05-31-94",
        "time": "6:22a",
        "clusters": "264",
        "hidden": False,
        "content": (
            "DEVICE=C:\\DOS\\HIMEM.SYS\n"
            "DOS=HIGH,UMB\n"
            "FILES=40\n"
            "BUFFERS=20\n"
            "SHELL=C:\\COMMAND.COM C:\\ /P /E:512"
        ),
    },
    {
        "name": "AUTOEXEC.BAT",
        "bytes": 168,
        "attr": "A",
        "date": "05-31-94",
        "time": "6:22a",
        "clusters": "265",
        "hidden": False,
        "content": (
            "@ECHO OFF\n"
            "PROMPT $P$G\n"
            "PATH C:\\DOS;C:\\FIELDGLS\n"
            "LH C:\\DOS\\MSCDEX.EXE /D:MSCD001\n"
            "ECHO Fieldglass 8086 Observatory Ready."
        ),
    },
    {"name": "HIMEM.SYS", "bytes": 29_136, "attr": "A", "date": "05-31-94", "time": "6:22a", "clusters": "266..322", "hidden": False, "content": None},
    {
        "name": "FIELDGLS.TXT",
        "bytes": 418,
        "attr": "A",
        "date": "11-27-26",
        "time": "4:12a",
        "clusters": "323",
        "hidden": False,
        "content": (
            "FIELDGLASS OBSERVATORY — 8086 REAL-MODE SPECIMEN\n"
            "Equation: A_tau(p) = |{x in X : p(x) > tau}|\n"
            "Conventional RAM: 640 KB (655,360 bytes)\n"
            "Free TPA: 600 KB (614,400 bytes) with DOS=HIGH\n"
            "Zero cloud tokens ($0.00) · executed=False"
        ),
    },
    {
        "name": "CHIASM.DAT",
        "bytes": 256,
        "attr": "A",
        "date": "11-27-26",
        "time": "4:12a",
        "clusters": "324",
        "hidden": False,
        "content": (
            "CONTRACT=fieldglass-causal-chiasm/v1\n"
            "TAU=0.10\n"
            "NEXUS_EP=6\n"
            "SUBSYSTEMS=ivt_bios,dos_kernel,command_shell,conv_free_tpa,video_uma,umb_rom,hma_high,fat12_io"
        ),
    },
]

MSDOS_STATES: tuple[str, ...] = (
    "ivt_bios",
    "dos_kernel",
    "command_shell",
    "conv_free_tpa",
    "video_uma",
    "umb_rom",
    "hma_high",
    "fat12_io",
)


@dataclass
class MSDOS8086Model:
    """Deterministic 16-bit 8086 real-mode and MS-DOS 6.22 educational model."""

    a20_enabled: bool = True
    cwd: str = "C:\\"
    step_pc: int = 0
    history: list[str] = field(default_factory=list)
    regs: dict[str, int] = field(
        default_factory=lambda: {
            "AX": 0x0000,
            "BX": 0x0000,
            "CX": 0x00FF,
            "DX": 0x0000,
            "SI": 0x0100,
            "DI": 0x0200,
            "BP": 0x0000,
            "SP": 0xFFFE,
            "CS": 0x0800,
            "DS": 0x0800,
            "ES": 0x0800,
            "SS": 0x0800,
            "IP": 0x0100,
            "FLAGS": 0x0202,
        }
    )

    _PROGRAM: tuple[tuple[str, int], ...] = (
        ("MOV AX, 0900h", 3),
        ("MOV DX, 0140h", 3),
        ("INT 21h", 2),
        ("ADD AX, 002Ah", 3),
        ("CMP AX, 092Ah", 3),
        ("NOP", 1),
    )

    def phys_addr(self, seg: int, off: int, a20_enabled: bool | None = None) -> int:
        """Compute 20/21-bit real-mode physical address ((seg << 4) + off)."""
        use_a20 = self.a20_enabled if a20_enabled is None else a20_enabled
        addr = ((seg & 0xFFFF) << 4) + (off & 0xFFFF)
        return addr if use_a20 else (addr & 0xFFFFF)

    def _update_arith_flags(self, result16: int, *, carry: bool = False, overflow: bool = False) -> None:
        val = result16 & 0xFFFF
        flags = self.regs["FLAGS"] & ~(
            FLAG_MASKS["CF"]
            | FLAG_MASKS["PF"]
            | FLAG_MASKS["ZF"]
            | FLAG_MASKS["SF"]
            | FLAG_MASKS["OF"]
        )
        if carry:
            flags |= FLAG_MASKS["CF"]
        if val == 0:
            flags |= FLAG_MASKS["ZF"]
        if val & 0x8000:
            flags |= FLAG_MASKS["SF"]
        if bin(val & 0xFF).count("1") % 2 == 0:
            flags |= FLAG_MASKS["PF"]
        if overflow:
            flags |= FLAG_MASKS["OF"]
        self.regs["FLAGS"] = flags & 0xFFFF

    def flags_dict(self) -> dict[str, int]:
        f = self.regs["FLAGS"]
        return {name: int(bool(f & mask)) for name, mask in FLAG_MASKS.items()}

    def flags_string(self) -> str:
        fd = self.flags_dict()
        return " ".join(f"{k}={v}" for k, v in fd.items())

    def step_instruction(self) -> dict[str, Any]:
        """Execute one deterministic 8086 micro-program instruction."""
        idx = self.step_pc % len(self._PROGRAM)
        mnem, length = self._PROGRAM[idx]
        if idx == 0:
            self.regs["AX"] = 0x0900
        elif idx == 1:
            self.regs["DX"] = 0x0140
        elif idx == 2:
            # Simulated DOS INT 21h AH=09h print string (returns AL=24h)
            self.regs["AX"] = (self.regs["AX"] & 0xFF00) | 0x0024
        elif idx == 3:
            a = self.regs["AX"]
            res = a + 0x002A
            self.regs["AX"] = res & 0xFFFF
            self._update_arith_flags(res, carry=res > 0xFFFF)
        elif idx == 4:
            a = self.regs["AX"]
            diff = (a - 0x092A) & 0xFFFF
            self._update_arith_flags(diff, carry=a < 0x092A)
        else:
            pass

        self.regs["IP"] = (0x0100 + sum(self._PROGRAM[i][1] for i in range(idx + 1))) & 0xFFFF
        self.step_pc += 1
        return {
            "instruction": mnem,
            "length_bytes": length,
            "step_index": idx,
            "phys_cs_ip": f"0x{self.phys_addr(self.regs['CS'], self.regs['IP']):05X}",
            "registers": dict(self.regs),
            "flags": self.flags_dict(),
        }

    def memory_summary(self) -> dict[str, int]:
        conv = sum(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["area"] == "Conventional")
        uma = sum(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["area"] == "UMA")
        hma = sum(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["area"] == "HMA")
        free_tpa = next(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["region"] == "FREE_TPA")
        return {
            "conventional_bytes": conv,
            "uma_bytes": uma,
            "hma_bytes": hma,
            "free_tpa_bytes": free_tpa,
            "total_addressable_real_mode": conv + uma,
        }

    def run_command(self, line: str) -> dict[str, Any]:
        """Execute a deterministic COMMAND.COM shell command."""
        raw = line.strip()
        self.history.append(raw)
        if not raw:
            return {
                "command": "",
                "output_lines": [],
                "clear_screen": False,
                "registers": dict(self.regs),
                "flags": self.flags_dict(),
            }

        parts = raw.split()
        verb = parts[0].upper()
        arg = parts[1].upper() if len(parts) > 1 else ""
        clear_screen = False
        lines: list[str] = []

        if verb == "VER":
            lines = ["", "MS-DOS Version 6.22 (8086 Educational Real-Mode Model)", ""]
        elif verb == "HELP":
            lines = [
                "Supported COMMAND.COM verbs:",
                "  DIR           List FAT12 virtual directory entries",
                "  MEM [/C]      Display 640 KB conventional, UMA, and HMA memory",
                "  CHKDSK        Check 1.44 MB FAT12 disk geometry & memory",
                "  TYPE <FILE>   Display text file (CONFIG.SYS, AUTOEXEC.BAT, FIELDGLS.TXT, CHIASM.DAT)",
                "  VER           Display MS-DOS version",
                "  AUTOEXEC.BAT  Run simulated startup batch file",
                "  STEP          Step one 8086 micro-program instruction",
                "  REGS          Print current 8086 registers and FLAGS",
                "  CLS           Clear terminal output",
                "  HELP          Show this command summary",
            ]
        elif verb == "CLS":
            clear_screen = True
            lines = []
        elif verb == "DIR":
            visible = [f for f in MSDOS_VIRTUAL_FILES if not f["hidden"]]
            used_bytes = sum(f["bytes"] for f in MSDOS_VIRTUAL_FILES)
            free_bytes = FAT12_GEOMETRY["total_bytes"] - used_bytes
            lines = [
                " Volume in drive C is FIELDGLS622",
                " Volume Serial Number is 1994-0622",
                f" Directory of {self.cwd}",
                "",
            ]
            for f in visible:
                stem, ext = (f["name"].split(".", 1) + [""])[:2]
                lines.append(
                    f"{stem:<8s} {ext:<3s}  {f['bytes']:>10,d}  {f['date']}  {f['time']}  [{f['attr']}]"
                )
            lines.extend([
                f"        {len(visible)} file(s)      {sum(f['bytes'] for f in visible):>10,d} bytes",
                f"        {len(MSDOS_VIRTUAL_FILES) - len(visible)} hidden       {free_bytes:>10,d} bytes free",
            ])
        elif verb == "MEM":
            ms = self.memory_summary()
            lines = [
                "Memory Type        Total       Used       Free",
                "----------------  --------   --------   --------",
                f"Conventional         640K        40K       600K  ({ms['free_tpa_bytes']:,d} bytes)",
                f"Upper                384K       192K       192K  ({ms['uma_bytes']:,d} bytes total UMA)",
                f"Reserved             384K       384K         0K",
                f"Extended (XMS/HMA)    64K        47K        17K  ({ms['hma_bytes']:,d} bytes HMA)",
                "----------------  --------   --------   --------",
                f"Largest executable program size:  600K ({ms['free_tpa_bytes']:,d} bytes)",
                "MS-DOS is resident in the high memory area (DOS=HIGH,UMB).",
            ]
            if arg == "/C":
                lines.append("Modules: IO.SYS(26K) COMMAND.COM(13K) HIMEM.SYS(HMA)")
        elif verb == "CHKDSK":
            used_bytes = sum(f["bytes"] for f in MSDOS_VIRTUAL_FILES)
            free_bytes = FAT12_GEOMETRY["total_bytes"] - used_bytes
            ms = self.memory_summary()
            lines = [
                "Volume FIELDGLS622 created 05-31-1994 6:22a",
                "Volume Serial Number is 1994-0622",
                "",
                f"  {FAT12_GEOMETRY['total_bytes']:>10,d} bytes total disk space (FAT12 2880 sectors)",
                f"      {sum(f['bytes'] for f in MSDOS_VIRTUAL_FILES if f['hidden']):>6,d} bytes in 2 hidden files",
                f"      {sum(f['bytes'] for f in MSDOS_VIRTUAL_FILES if not f['hidden']):>6,d} bytes in 6 user files",
                f"  {free_bytes:>10,d} bytes available on disk",
                "",
                f"         {FAT12_GEOMETRY['bytes_per_sector']} bytes in each allocation unit",
                f"       {FAT12_GEOMETRY['total_sectors']:,d} total allocation sectors on disk",
                "",
                f"     {ms['conventional_bytes']:>7,d} total bytes memory",
                f"     {ms['free_tpa_bytes']:>7,d} bytes free",
            ]
        elif verb == "TYPE":
            if not arg:
                lines = ["Required parameter missing"]
            else:
                match = next((f for f in MSDOS_VIRTUAL_FILES if f["name"] == arg), None)
                if match is None:
                    lines = [f"File not found - {arg}"]
                elif match["content"] is None:
                    lines = [f"{match['name']} is a binary system image ({match['bytes']:,d} bytes)."]
                else:
                    lines = match["content"].splitlines()
        elif verb == "AUTOEXEC.BAT":
            lines = [
                "C:\\>@ECHO OFF",
                "C:\\>PROMPT $P$G",
                "C:\\>PATH C:\\DOS;C:\\FIELDGLS",
                "C:\\>LH C:\\DOS\\MSCDEX.EXE /D:MSCD001",
                "Fieldglass 8086 Observatory Ready.",
            ]
            self.regs["AX"] = 0x0900
            self.regs["DX"] = 0x0140
        elif verb == "STEP":
            step_res = self.step_instruction()
            lines = [
                f"STEP #{step_res['step_index']}: {step_res['instruction']} (CS:IP={self.regs['CS']:04X}:{self.regs['IP']:04X}, phys={step_res['phys_cs_ip']})",
                f"  AX={self.regs['AX']:04X} BX={self.regs['BX']:04X} CX={self.regs['CX']:04X} DX={self.regs['DX']:04X}",
                f"  FLAGS={self.regs['FLAGS']:04X} [{self.flags_string()}]",
            ]
        elif verb == "REGS":
            lines = [
                f"AX={self.regs['AX']:04X}  BX={self.regs['BX']:04X}  CX={self.regs['CX']:04X}  DX={self.regs['DX']:04X}",
                f"SI={self.regs['SI']:04X}  DI={self.regs['DI']:04X}  BP={self.regs['BP']:04X}  SP={self.regs['SP']:04X}",
                f"CS={self.regs['CS']:04X}  DS={self.regs['DS']:04X}  ES={self.regs['ES']:04X}  SS={self.regs['SS']:04X}  IP={self.regs['IP']:04X}",
                f"FLAGS={self.regs['FLAGS']:04X} ({self.flags_string()})  A20={'ON' if self.a20_enabled else 'OFF'}",
            ]
        else:
            lines = [f"Bad command or file name - {verb}"]

        return {
            "command": raw,
            "output_lines": lines,
            "clear_screen": clear_screen,
            "registers": dict(self.regs),
            "flags": self.flags_dict(),
        }

    def simulate_boot_telemetry(self) -> dict[str, Any]:
        """Generate 12 deterministic boot-to-shell episodes and Kloster Chiasm telemetry."""
        # Past (0..5): BIOS POST, IVT setup, IO.SYS/MSDOS.SYS loading, FAT12 read
        # Nexus (6): COMMAND.COM prompt ready
        # Future (7..11): MEM, CHKDSK, DIR, 8086 STEP execution in Free TPA + HMA
        raw_episodes: list[dict[str, float]] = [
            {"ivt_bios": 0.34, "dos_kernel": 0.14, "command_shell": 0.05, "conv_free_tpa": 0.11, "video_uma": 0.14, "umb_rom": 0.13, "hma_high": 0.03, "fat12_io": 0.06},
            {"ivt_bios": 0.28, "dos_kernel": 0.18, "command_shell": 0.06, "conv_free_tpa": 0.12, "video_uma": 0.13, "umb_rom": 0.12, "hma_high": 0.04, "fat12_io": 0.07},
            {"ivt_bios": 0.20, "dos_kernel": 0.26, "command_shell": 0.07, "conv_free_tpa": 0.13, "video_uma": 0.11, "umb_rom": 0.10, "hma_high": 0.05, "fat12_io": 0.08},
            {"ivt_bios": 0.14, "dos_kernel": 0.25, "command_shell": 0.09, "conv_free_tpa": 0.14, "video_uma": 0.11, "umb_rom": 0.09, "hma_high": 0.08, "fat12_io": 0.10},
            {"ivt_bios": 0.11, "dos_kernel": 0.22, "command_shell": 0.12, "conv_free_tpa": 0.16, "video_uma": 0.11, "umb_rom": 0.08, "hma_high": 0.11, "fat12_io": 0.09},
            {"ivt_bios": 0.09, "dos_kernel": 0.18, "command_shell": 0.17, "conv_free_tpa": 0.18, "video_uma": 0.11, "umb_rom": 0.07, "hma_high": 0.12, "fat12_io": 0.08},
            # Nexus episode 6: COMMAND.COM prompt ready
            {"ivt_bios": 0.08, "dos_kernel": 0.15, "command_shell": 0.21, "conv_free_tpa": 0.20, "video_uma": 0.11, "umb_rom": 0.06, "hma_high": 0.12, "fat12_io": 0.07},
            {"ivt_bios": 0.06, "dos_kernel": 0.14, "command_shell": 0.19, "conv_free_tpa": 0.23, "video_uma": 0.12, "umb_rom": 0.06, "hma_high": 0.12, "fat12_io": 0.08},
            {"ivt_bios": 0.05, "dos_kernel": 0.13, "command_shell": 0.18, "conv_free_tpa": 0.24, "video_uma": 0.12, "umb_rom": 0.05, "hma_high": 0.11, "fat12_io": 0.12},
            {"ivt_bios": 0.05, "dos_kernel": 0.12, "command_shell": 0.17, "conv_free_tpa": 0.25, "video_uma": 0.12, "umb_rom": 0.05, "hma_high": 0.10, "fat12_io": 0.14},
            {"ivt_bios": 0.05, "dos_kernel": 0.12, "command_shell": 0.16, "conv_free_tpa": 0.26, "video_uma": 0.13, "umb_rom": 0.05, "hma_high": 0.11, "fat12_io": 0.12},
            {"ivt_bios": 0.05, "dos_kernel": 0.12, "command_shell": 0.16, "conv_free_tpa": 0.27, "video_uma": 0.13, "umb_rom": 0.05, "hma_high": 0.11, "fat12_io": 0.11},
        ]
        telem = compute_distribution_telemetry(raw_episodes, tau=0.10, nexus_idx=6, horizon=5)
        telem["memory_summary"] = self.memory_summary()
        telem["fat12_geometry"] = dict(FAT12_GEOMETRY)
        return telem


# ---------------------------------------------------------------------------
# Domain 2: 6-DOF Flight Simulator & Telemetry HUD
# ---------------------------------------------------------------------------

FLIGHT_STATES: tuple[str, ...] = (
    "airspeed_band",
    "climb_energy",
    "bank_authority",
    "pitch_stability",
    "aoa_margin",
    "thrust_reserve",
    "heading_sweep",
    "slip_damping",
)


def isa_density(alt_m: float) -> float:
    """International Standard Atmosphere air density rho(h) in kg/m^3."""
    h = max(0.0, _require_finite_num(alt_m, "alt_m"))
    return 1.225 * (max(0.1, 1.0 - 2.25577e-5 * h) ** 4.25588)


@dataclass
class FlightSim6DOF:
    """Deterministic 6-DOF light single-engine educational flight dynamics integrator."""

    mass_kg: float = 1043.0
    wing_area_m2: float = 16.2
    chord_m: float = 1.49
    span_m: float = 11.0
    cl0: float = 0.28
    cl_alpha: float = 4.41
    cd0: float = 0.027
    induced_k: float = 0.054
    max_thrust_n: float = 2400.0
    g: float = 9.80665

    # Body velocities (m/s), body angular rates (rad/s), Euler angles (rad), position (m)
    u: float = 56.0
    v: float = 0.0
    w: float = 1.8
    p: float = 0.0
    q: float = 0.0
    r: float = 0.0
    phi: float = 0.0
    theta: float = math.radians(3.0)
    psi: float = math.radians(90.0)
    x_n: float = 0.0
    y_e: float = 0.0
    alt_m: float = 1500.0
    throttle: float = 0.72
    last_g_load: float = 1.0

    def reset_preset(self, name: str) -> dict[str, Any]:
        """Reset 6-DOF state to a named educational flight regime."""
        key = name.strip().lower()
        self.v = 0.0
        self.p = 0.0
        self.q = 0.0
        self.r = 0.0
        self.x_n = 0.0
        self.y_e = 0.0
        if key == "cruise":
            self.u, self.w = 56.0, 1.6
            self.phi, self.theta, self.psi = 0.0, math.radians(2.8), math.radians(90.0)
            self.alt_m, self.throttle = 1500.0, 0.72
        elif key == "climb":
            self.u, self.w = 46.0, 3.4
            self.phi, self.theta, self.psi = 0.0, math.radians(10.5), math.radians(90.0)
            self.alt_m, self.throttle = 900.0, 0.95
        elif key == "turn30":
            self.u, self.w = 54.0, 2.4
            self.phi, self.theta, self.psi = math.radians(30.0), math.radians(4.0), math.radians(90.0)
            self.alt_m, self.throttle = 1500.0, 0.78
        elif key == "approach":
            self.u, self.w = 38.0, 1.9
            self.phi, self.theta, self.psi = 0.0, math.radians(-2.5), math.radians(270.0)
            self.alt_m, self.throttle = 450.0, 0.38
        else:
            raise ValueError(f"Unknown flight preset: {name}")
        return self.hud()

    def _substep(
        self,
        dt: float,
        throttle: float,
        pitch_cmd: float,
        roll_cmd: float,
        rudder_cmd: float,
    ) -> None:
        thr = max(0.0, min(1.0, _require_finite_num(throttle, "throttle")))
        self.throttle = thr
        pcmd = max(-1.0, min(1.0, _require_finite_num(pitch_cmd, "pitch_cmd")))
        rcmd = max(-1.0, min(1.0, _require_finite_num(roll_cmd, "roll_cmd")))
        ycmd = max(-1.0, min(1.0, _require_finite_num(rudder_cmd, "rudder_cmd")))

        v_a = math.sqrt(self.u * self.u + self.v * self.v + self.w * self.w)
        v_safe = max(12.0, v_a)
        alpha = math.atan2(self.w, max(5.0, self.u))
        beta = math.asin(max(-0.99, min(0.99, self.v / v_safe)))

        rho = isa_density(self.alt_m)
        q_bar = 0.5 * rho * v_safe * v_safe

        # Smooth stall rolloff above |alpha| > 15 deg
        stall_rad = math.radians(15.0)
        if abs(alpha) <= stall_rad:
            cl = self.cl0 + self.cl_alpha * alpha
        else:
            excess = abs(alpha) - stall_rad
            cl_peak = self.cl0 + self.cl_alpha * math.copysign(stall_rad, alpha)
            cl = cl_peak * math.exp(-3.5 * excess)
        cd = self.cd0 + self.induced_k * (cl * cl) + 0.12 * (beta * beta)

        lift = q_bar * self.wing_area_m2 * cl
        drag = q_bar * self.wing_area_m2 * cd
        side = -0.35 * q_bar * self.wing_area_m2 * beta + 0.06 * q_bar * self.wing_area_m2 * ycmd
        thrust = thr * self.max_thrust_n * ((rho / 1.225) ** 0.7)

        # Rotate lift/drag from wind frame into body (u, w)
        ca, sa = math.cos(alpha), math.sin(alpha)
        fx_aero = -drag * ca + lift * sa + thrust
        fz_aero = -drag * sa - lift * ca

        # Gravity components in body axes
        sp, cp = math.sin(self.phi), math.cos(self.phi)
        st, ct = math.sin(self.theta), math.cos(self.theta)
        fx = fx_aero - self.mass_kg * self.g * st
        fy = side + self.mass_kg * self.g * ct * sp
        fz = fz_aero + self.mass_kg * self.g * ct * cp

        self.last_g_load = max(-2.0, min(6.0, lift / (self.mass_kg * self.g)))

        # Translational body acceleration with Coriolis terms
        du = fx / self.mass_kg + self.r * self.v - self.q * self.w
        dv = fy / self.mass_kg + self.p * self.w - self.r * self.u
        dw = fz / self.mass_kg + self.q * self.u - self.p * self.v

        # Rotational moments (damped stability derivatives)
        target_pitch = math.radians(3.0) + pcmd * math.radians(16.0)
        target_roll = rcmd * math.radians(42.0)
        dp = 3.2 * (target_roll - self.phi) - 2.6 * self.p
        dq = 2.4 * (target_pitch - self.theta) - 2.8 * self.q - 0.6 * (alpha - math.radians(4.0))
        turn_r = (self.g / v_safe) * math.tan(max(-1.0, min(1.0, self.phi))) * cp
        dr = 2.2 * (turn_r + 0.25 * ycmd - self.r) - 0.9 * beta

        self.u = max(14.0, min(120.0, self.u + du * dt))
        self.v = max(-20.0, min(20.0, self.v + dv * dt))
        self.w = max(-20.0, min(25.0, self.w + dw * dt))
        self.p = max(-2.5, min(2.5, self.p + dp * dt))
        self.q = max(-2.0, min(2.0, self.q + dq * dt))
        self.r = max(-2.0, min(2.0, self.r + dr * dt))

        # Euler kinematics
        tan_t = math.tan(max(-1.35, min(1.35, self.theta)))
        dphi = self.p + (self.q * sp + self.r * cp) * tan_t
        dtheta = self.q * cp - self.r * sp
        dpsi = (self.q * sp + self.r * cp) / max(0.2, ct)

        self.phi = max(math.radians(-65.0), min(math.radians(65.0), self.phi + dphi * dt))
        self.theta = max(math.radians(-35.0), min(math.radians(35.0), self.theta + dtheta * dt))
        self.psi = (self.psi + dpsi * dt) % (2.0 * math.pi)

        # Inertial kinematics (NED vertical up -> alt_m)
        sp, cp = math.sin(self.phi), math.cos(self.phi)
        st, ct = math.sin(self.theta), math.cos(self.theta)
        sy, cy = math.sin(self.psi), math.cos(self.psi)
        vx_n = self.u * ct * cy + self.v * (sp * st * cy - cp * sy) + self.w * (cp * st * cy + sp * sy)
        vy_e = self.u * ct * sy + self.v * (sp * st * sy + cp * cy) + self.w * (cp * st * sy - sp * cy)
        vz_up = self.u * st - self.v * sp * ct - self.w * cp * ct

        self.x_n += vx_n * dt
        self.y_e += vy_e * dt
        self.alt_m = max(0.0, self.alt_m + vz_up * dt)

    def step(
        self,
        dt: float = 0.05,
        throttle: float = 0.72,
        pitch_cmd: float = 0.0,
        roll_cmd: float = 0.0,
        rudder_cmd: float = 0.0,
    ) -> dict[str, Any]:
        """Advance 6-DOF state deterministically (sub-stepping dt <= 0.05s, clamped to [0.001, 60.0])."""
        raw_dt = _require_finite_num(dt, "dt")
        thr_f = _require_finite_num(throttle, "throttle")
        pitch_f = _require_finite_num(pitch_cmd, "pitch_cmd")
        roll_f = _require_finite_num(roll_cmd, "roll_cmd")
        rudder_f = _require_finite_num(rudder_cmd, "rudder_cmd")
        total_dt = max(0.001, min(60.0, raw_dt))
        n_sub = max(1, int(math.ceil(total_dt / 0.05)))
        sub_dt = total_dt / n_sub
        for _ in range(n_sub):
            self._substep(sub_dt, thr_f, pitch_f, roll_f, rudder_f)
        return self.hud()

    def hud(self) -> dict[str, Any]:
        """Derive six-pack HUD gauges and aerodynamic indicators from 6-DOF state."""
        v_a = math.sqrt(self.u * self.u + self.v * self.v + self.w * self.w)
        vz_up = (
            self.u * math.sin(self.theta)
            - self.v * math.sin(self.phi) * math.cos(self.theta)
            - self.w * math.cos(self.phi) * math.cos(self.theta)
        )
        aoa_deg = math.degrees(math.atan2(self.w, max(1.0, self.u)))
        slip_norm = max(-1.0, min(1.0, self.v / max(v_a, 5.0)))
        return {
            "airspeed_kt": round(v_a * 1.943844, 2),
            "alt_m": round(self.alt_m, 2),
            "alt_ft": round(self.alt_m * 3.28084, 1),
            "vsi_fpm": round(vz_up * 196.8504, 1),
            "heading_deg": round(math.degrees(self.psi) % 360.0, 2) % 360.0,
            "pitch_deg": round(math.degrees(self.theta), 2),
            "roll_deg": round(math.degrees(self.phi), 2),
            "aoa_deg": round(aoa_deg, 2),
            "slip_norm": round(slip_norm, 4),
            "turn_rate_dps": round(math.degrees(self.r), 2),
            "g_load": round(self.last_g_load, 3),
            "mach": round(v_a / 340.29, 4),
            "stall_warning": abs(aoa_deg) > 14.5,
            "rho_kg_m3": round(isa_density(self.alt_m), 4),
            "throttle": round(self.throttle, 3),
        }

    def hud_to_repertoire(self, hud: dict[str, Any]) -> dict[str, float]:
        """Map 6-DOF flight HUD state into an 8-state normalized Kloster repertoire."""
        raw = {
            "airspeed_band": max(0.04, min(0.35, hud["airspeed_kt"] / 450.0)),
            "climb_energy": max(0.03, min(0.30, 0.12 + hud["vsi_fpm"] / 5000.0)),
            "bank_authority": max(0.03, min(0.30, 0.08 + abs(hud["roll_deg"]) / 160.0)),
            "pitch_stability": max(0.04, min(0.28, 0.18 - abs(hud["pitch_deg"]) / 120.0)),
            "aoa_margin": max(0.03, min(0.28, 0.22 - abs(hud["aoa_deg"]) / 80.0)),
            "thrust_reserve": max(0.04, min(0.28, 0.06 + hud["throttle"] * 0.20)),
            "heading_sweep": max(0.03, min(0.25, 0.07 + abs(hud["turn_rate_dps"]) / 30.0)),
            "slip_damping": max(0.04, min(0.25, 0.14 - abs(hud["slip_norm"]) * 0.10)),
        }
        return normalize_dist(raw)

    def simulate_sortie(self) -> dict[str, Any]:
        """Run a deterministic 24s / 16-episode sortie (Climb -> Cruise -> 30° Turn -> Approach)."""
        sim = FlightSim6DOF()
        sim.reset_preset("climb")
        episodes: list[dict[str, float]] = []
        trajectory: list[dict[str, Any]] = []

        schedule = (
            [(0.95, 0.35, 0.0)] * 6
            + [(0.72, 0.0, 0.0)] * 4
            + [(0.78, 0.05, 0.72)] * 3
            + [(0.38, -0.25, 0.0)] * 3
        )
        for idx, (thr, pcmd, rcmd) in enumerate(schedule):
            # 1.5s per episode in 0.05s steps
            for _ in range(30):
                hud = sim.step(0.05, throttle=thr, pitch_cmd=pcmd, roll_cmd=rcmd)
            hud["episode"] = idx
            hud["t_sec"] = round((idx + 1) * 1.5, 2)
            trajectory.append(hud)
            episodes.append(sim.hud_to_repertoire(hud))

        telem = compute_distribution_telemetry(episodes, tau=0.10, nexus_idx=8, horizon=8)
        telem["trajectory"] = trajectory
        return telem


# ---------------------------------------------------------------------------
# Domain 3: Simulated Medical Equipment Sandbox (STRICTLY NON-CLINICAL)
# ---------------------------------------------------------------------------

MEDICAL_STATES: tuple[str, ...] = (
    "pqrst_r_peak",
    "pqrst_st_t",
    "ppg_red_ac",
    "ppg_ir_dc",
    "capno_plateau",
    "capno_baseline",
    "pv_compliance",
    "pv_resistive",
)


class MedicalSandboxModel:
    """Strictly simulated, educational, non-clinical biomedical physics & optics sandbox."""

    @staticmethod
    def ecg_pqrst(t_sec: float, hr_bpm: float = 72.0) -> float:
        """Synthetic Lead II P-QRS-T Gaussian sum (educational morphology only, mV)."""
        t_f = _require_finite_num(t_sec, "t_sec")
        hr_f = _require_finite_num(hr_bpm, "hr_bpm")
        hr = max(20.0, min(220.0, hr_f))
        phi = (t_f * (hr / 60.0)) % 1.0
        waves = (
            (0.16, 0.15, 0.032),   # P wave
            (0.36, -0.14, 0.012),  # Q deflection
            (0.40, 1.15, 0.013),   # R peak
            (0.44, -0.26, 0.013),  # S trough
            (0.64, 0.32, 0.048),   # T wave
        )
        val = 0.0
        for center, amp, width in waves:
            d = phi - center
            val += amp * math.exp(-0.5 * (d / width) ** 2)
        return round(val, 6)

    @classmethod
    def ecg_trace(
        cls, *, hr_bpm: float = 72.0, duration_sec: float = 2.0, fs_hz: int = 128
    ) -> dict[str, Any]:
        """Generate synthetic ECG trace tagged with strict non-clinical flags."""
        hr_f = _require_finite_num(hr_bpm, "hr_bpm")
        dur_f = _require_finite_num(duration_sec, "duration_sec")
        fs_f = _require_finite_num(fs_hz, "fs_hz")
        fs = max(1.0, fs_f)
        dur = max(0.1, dur_f)
        n = max(16, int(round(dur * fs)))
        t_vals = [round(i / fs, 4) for i in range(n)]
        mv_vals = [cls.ecg_pqrst(t, hr_bpm=hr_f) for t in t_vals]
        return {
            **NON_CLINICAL_FLAGS,
            "hr_bpm": hr_f,
            "duration_sec": dur,
            "fs_hz": int(round(fs)),
            "t_sec": t_vals,
            "lead_ii_mv": mv_vals,
            "peak_mv": max(mv_vals),
            "min_mv": min(mv_vals),
        }

    @staticmethod
    def spo2_beer_lambert(
        r_ratio: float,
        perfusion_index: float = 0.025,
        t_sec: float = 0.0,
        hr_bpm: float = 72.0,
    ) -> dict[str, Any]:
        """Educational Beer-Lambert dual-wavelength (660nm/940nm) SpO2 & synthetic PPG model."""
        r = max(0.35, min(2.2, _require_finite_num(r_ratio, "r_ratio")))
        pi = max(0.002, min(0.15, _require_finite_num(perfusion_index, "perfusion_index")))
        t_f = _require_finite_num(t_sec, "t_sec")
        hr = max(20.0, min(220.0, _require_finite_num(hr_bpm, "hr_bpm")))
        spo2 = max(70.0, min(100.0, 110.0 - 25.0 * r))
        phi = (t_f * (hr / 60.0)) % 1.0
        # Dual-peak arterial + dicrotic notch synthetic plethysmograph
        systolic = math.exp(-0.5 * ((phi - 0.22) / 0.09) ** 2)
        dicrotic = 0.42 * math.exp(-0.5 * ((phi - 0.44) / 0.10) ** 2)
        pleth = systolic + dicrotic
        # Educational Beer-Lambert optical attenuation I = I0 * exp(-eps * c * d(t))
        eps_660 = 0.32 + 0.55 * (1.0 - spo2 / 100.0)
        eps_940 = 0.24 + 0.14 * (spo2 / 100.0)
        d_t = 1.0 + pi * pleth
        i_660 = math.exp(-eps_660 * d_t)
        i_940 = math.exp(-eps_940 * d_t)
        return {
            **NON_CLINICAL_FLAGS,
            "r_ratio": round(r, 4),
            "perfusion_index": round(pi, 4),
            "spo2_pct": round(spo2, 2),
            "pleth_norm": round(pleth, 5),
            "intensity_660nm": round(i_660, 6),
            "intensity_940nm": round(i_940, 6),
        }

    @staticmethod
    def capnography_waveform(
        t_sec: float, rr_bpm: float = 14.0, etco2_mmhg: float = 38.0
    ) -> float:
        """Synthetic 4-phase educational capnography curve (mmHg)."""
        t_f = _require_finite_num(t_sec, "t_sec")
        rr = max(4.0, min(60.0, _require_finite_num(rr_bpm, "rr_bpm")))
        etco2 = max(10.0, min(80.0, _require_finite_num(etco2_mmhg, "etco2_mmhg")))
        phi = (t_f * (rr / 60.0)) % 1.0
        if phi < 0.28:
            # Phase I: inspiratory baseline
            val = 0.0
        elif phi < 0.40:
            # Phase II: expiratory upstroke (smooth logistic-like S-curve)
            u = (phi - 0.28) / 0.12
            val = etco2 * 0.90 * (0.5 - 0.5 * math.cos(math.pi * u))
        elif phi < 0.72:
            # Phase III: alveolar plateau rising gently to EtCO2
            u = (phi - 0.40) / 0.32
            val = etco2 * (0.90 + 0.10 * u)
        elif phi < 0.80:
            # Phase 0: rapid inspiratory drop
            u = (phi - 0.72) / 0.08
            val = etco2 * (1.0 - 0.5 * (1.0 - math.cos(math.pi * u)))
        else:
            val = 0.0
        return round(val, 4)

    @classmethod
    def capnography_trace(
        cls,
        *,
        rr_bpm: float = 14.0,
        etco2_mmhg: float = 38.0,
        duration_sec: float = 8.0,
        fs_hz: int = 32,
    ) -> dict[str, Any]:
        rr_f = _require_finite_num(rr_bpm, "rr_bpm")
        et_f = _require_finite_num(etco2_mmhg, "etco2_mmhg")
        dur_f = _require_finite_num(duration_sec, "duration_sec")
        fs_f = _require_finite_num(fs_hz, "fs_hz")
        fs = max(1.0, fs_f)
        dur = max(0.1, dur_f)
        n = max(16, int(round(dur * fs)))
        t_vals = [round(i / fs, 4) for i in range(n)]
        co2 = [cls.capnography_waveform(t, rr_bpm=rr_f, etco2_mmhg=et_f) for t in t_vals]
        return {
            **NON_CLINICAL_FLAGS,
            "rr_bpm": rr_f,
            "etco2_mmhg": et_f,
            "t_sec": t_vals,
            "co2_mmhg": co2,
            "peak_mmhg": max(co2),
        }

    @staticmethod
    def ventilator_pv_loop(
        compliance_ml_cmh2o: float = 50.0,
        resistance_cmh2o_l_s: float = 8.0,
        vt_ml: float = 480.0,
        peep_cmh2o: float = 5.0,
        n_pts: int = 80,
    ) -> dict[str, Any]:
        """Parametric synthetic ventilator P-V loop via P = PEEP + V/C + R * flow."""
        c = max(10.0, _require_finite_num(compliance_ml_cmh2o, "compliance_ml_cmh2o"))
        r = max(1.0, _require_finite_num(resistance_cmh2o_l_s, "resistance_cmh2o_l_s"))
        vt = max(100.0, _require_finite_num(vt_ml, "vt_ml"))
        peep = max(0.0, _require_finite_num(peep_cmh2o, "peep_cmh2o"))
        n_f = _require_finite_num(n_pts, "n_pts")
        n = max(16, int(n_f))

        points: list[dict[str, Any]] = []
        for i in range(n):
            theta = 2.0 * math.pi * (i / float(n))
            vol_ml = 0.5 * vt * (1.0 - math.cos(theta))
            # Synthetic flow in L/s: positive on inspiration (0..pi), negative on expiration (pi..2pi)
            flow_l_s = 0.55 * math.sin(theta)
            pressure = peep + (vol_ml / c) + (r * flow_l_s)
            points.append(
                {
                    "step": i,
                    "phase": "inspiration" if i < n // 2 else "expiration",
                    "volume_ml": round(vol_ml, 3),
                    "flow_l_s": round(flow_l_s, 4),
                    "pressure_cmh2o": round(pressure, 3),
                }
            )

        return {
            **NON_CLINICAL_FLAGS,
            "compliance_ml_cmh2o": c,
            "resistance_cmh2o_l_s": r,
            "vt_ml": vt,
            "peep_cmh2o": peep,
            "peak_pressure_cmh2o": max(p["pressure_cmh2o"] for p in points),
            "plateau_pressure_cmh2o": round(peep + vt / c, 3),
            "points": points,
        }

    @staticmethod
    def infusion_rate_calc(
        dose_mcg_kg_min: float,
        weight_kg: float,
        conc_mcg_ml: float,
        drop_factor_gtt_ml: int = 20,
    ) -> dict[str, Any]:
        """Educational dimensional-analysis infusion rate calculation (non-clinical math)."""
        dose = _require_finite_num(dose_mcg_kg_min, "dose_mcg_kg_min")
        wt = _require_finite_num(weight_kg, "weight_kg")
        conc = _require_finite_num(conc_mcg_ml, "conc_mcg_ml")
        df_f = _require_finite_num(drop_factor_gtt_ml, "drop_factor_gtt_ml")
        if dose < 0.0:
            raise ValueError("dose_mcg_kg_min must be >= 0")
        if wt <= 0.0:
            raise ValueError("weight_kg must be > 0")
        if conc <= 0.0:
            raise ValueError("conc_mcg_ml must be > 0")
        if df_f <= 0.0:
            raise ValueError("drop_factor_gtt_ml must be > 0")
        df = max(1, int(round(df_f)))
        rate_ml_hr = (dose * wt * 60.0) / conc
        drops_per_min = (rate_ml_hr * df) / 60.0
        if not math.isfinite(rate_ml_hr) or not math.isfinite(drops_per_min):
            raise ValueError("Infusion calculation overflowed finite bounds")
        return {
            **NON_CLINICAL_FLAGS,
            "dose_mcg_kg_min": dose,
            "weight_kg": wt,
            "conc_mcg_ml": conc,
            "drop_factor_gtt_ml": df,
            "rate_ml_hr": round(rate_ml_hr, 4),
            "drops_per_min": round(drops_per_min, 4),
        }

    @classmethod
    def simulate_telemetry(cls) -> dict[str, Any]:
        """Generate 16 simulated episodes across 4 educational biomedical regimes."""
        regimes = [
            # (label, hr, r_ratio, compliance, resistance)
            ("Baseline Sinus", 72.0, 0.52, 55.0, 6.0),
            ("Exercise Tachycardia", 118.0, 0.56, 52.0, 7.0),
            ("Low-Perfusion Optics", 84.0, 0.88, 48.0, 9.0),
            ("Changed Compliance P-V", 78.0, 0.62, 32.0, 14.0),
        ]
        episodes: list[dict[str, float]] = []
        regime_labels: list[str] = []
        for r_idx, (label, hr, r_rat, comp, res) in enumerate(regimes):
            for sub in range(4):
                t = r_idx * 4.0 + sub * 0.8
                ecg_v = abs(cls.ecg_pqrst(t + 0.33, hr_bpm=hr))
                spo2_d = cls.spo2_beer_lambert(r_rat + 0.02 * sub, t_sec=t, hr_bpm=hr)
                cap_v = cls.capnography_waveform(t + 1.5, rr_bpm=14.0 + r_idx * 2.0)
                pv = cls.ventilator_pv_loop(compliance_ml_cmh2o=comp, resistance_cmh2o_l_s=res)
                raw = {
                    "pqrst_r_peak": 0.14 + 0.08 * min(1.2, ecg_v + 0.25),
                    "pqrst_st_t": 0.11 + 0.02 * (hr / 100.0),
                    "ppg_red_ac": 0.13 + 0.06 * (1.0 - spo2_d["r_ratio"] / 2.0),
                    "ppg_ir_dc": 0.15 + 0.04 * spo2_d["intensity_940nm"],
                    "capno_plateau": 0.13 + 0.04 * (cap_v / 40.0),
                    "capno_baseline": 0.07 + 0.015 * sub,
                    "pv_compliance": 0.11 + 0.08 * (comp / 60.0),
                    "pv_resistive": 0.08 + 0.08 * (pv["peak_pressure_cmh2o"] / 30.0),
                }
                episodes.append(normalize_dist(raw))
                regime_labels.append(label)

        telem = compute_distribution_telemetry(episodes, tau=0.10, nexus_idx=8, horizon=8)
        telem.update(NON_CLINICAL_FLAGS)
        telem["regimes"] = regime_labels
        return telem


# ---------------------------------------------------------------------------
# Domain 4: Software Systems & Fieldglass Architecture Observatory
# ---------------------------------------------------------------------------

SOFTWARE_STATES: tuple[str, ...] = (
    "frame_ingest",
    "deskew_geom",
    "bg_clean",
    "svg_braille",
    "kloster_atp",
    "chiasm_seal",
    "win7_compat",
    "local_serve",
)


class SoftwareObservatoryModel:
    """Deterministic Fieldglass & systems architecture workbench model."""

    PIPELINE_STAGES: tuple[dict[str, str], ...] = (
        {
            "stage": "01 / Frame Ingest",
            "module": "fieldglass.plate.extract_sharpest_frame",
            "contract": "Laplacian variance selection at zero cloud cost",
            "output": "Lossless sharpest-frame PNG",
        },
        {
            "stage": "02 / Perspective Deskew",
            "module": "fieldglass.plate.perspective_deskew",
            "contract": "4-corner projective homography to canonical rect",
            "output": "Rectified plate image",
        },
        {
            "stage": "03 / Illumination Clean",
            "module": "fieldglass.plate.clean_illumination",
            "contract": "Gaussian background division -> archival parchment",
            "output": "Normalized [0..1] ink strength field",
        },
        {
            "stage": "04 / Vector & 2x4 Braille",
            "module": "fieldglass.plate.trace_ink_to_svg & ink_to_braille_lines",
            "contract": "Framed SVG + Bayer-dithered U+2800..U+28FF cells",
            "output": "SVG, TXT, JSON, Braille PNG",
        },
        {
            "stage": "05 / Kloster Metrics & Chiasm",
            "module": "fieldglass.metrics.a_tau & causal_chiasm",
            "contract": "Strict p(x) > tau superlevel volume + SHA-256 seal",
            "output": "chiasm_report.json & SVG dashboard",
        },
        {
            "stage": "06 / Static Loopback Serve",
            "module": "fieldglass.showcase.make_range_handler",
            "contract": "HTTP 206 Range-capable 127.0.0.1 static delivery",
            "output": "Self-contained offline Observatory",
        },
    )

    WIN7_MODERN_MATRIX: tuple[dict[str, str], ...] = (
        {
            "layer": "JS Runtime",
            "win7_target": "IE8-IE11 / mshta.exe ES5 (var, function(), no fetch/Promise)",
            "modern_observatory": "ES2022 Vanilla JS + Canvas 2D + WebCrypto / pure-JS SHA-256",
            "invariant": "Zero external CDNs, zero runtime console errors",
        },
        {
            "layer": "CSS Layout",
            "win7_target": "Explicit hex colors + table/inline-block/float layout",
            "modern_observatory": "CSS custom properties (--bg/#0b0f17) + CSS Grid/Flexbox",
            "invariant": "High-contrast dark/parchment legibility",
        },
        {
            "layer": "Python Runtime",
            "win7_target": "Python 3.7/3.8 stdlib-only (no PEP 604 X|Y, no match/case)",
            "modern_observatory": "Python 3.14 + NumPy/SciPy/PIL/Matplotlib",
            "invariant": "Deterministic computation with $0.00 cloud tokens",
        },
        {
            "layer": "Graphics Surface",
            "win7_target": "VML/Basic SVG + GDI-safe static PNG",
            "modern_observatory": "HTML5 Canvas + inline SVG + 2x4 Unicode Braille",
            "invariant": "GPS-stripped PNGs (< 5 MB) & valid XML SVGs",
        },
        {
            "layer": "Packaging & Delivery",
            "win7_target": "Offline .hta + .bat launcher + portable .zip bundle",
            "modern_observatory": "Static docs/ GitHub Pages tree (< 50 MB per file)",
            "invariant": "Self-contained offline execution",
        },
        {
            "layer": "Transport & Integrity",
            "win7_target": "127.0.0.1 HTTP/1.1 loopback + non-ANSI cmd.exe log",
            "modern_observatory": "Range-capable 127.0.0.1 showcase + canonical SHA-256 seals",
            "invariant": "executed=False, sentience_claimed=False, tokens_used=0",
        },
    )

    @staticmethod
    def evaluate_repertoire(dist: dict[str, float], tau: float = 0.10) -> dict[str, Any]:
        """Evaluate Kloster A_tau(p), accessible states, H1, H2, and M4^(1/4) for any distribution."""
        tau_f = _require_finite_num(tau, "tau")
        if tau_f == 0.0:
            tau_f = 0.0
        norm = normalize_dist(dist)
        vec = np.array([norm[k] for k in sorted(norm)], dtype=np.float64)
        acc = accessible_set(norm, tau_f)
        return {
            "tau": tau_f,
            "normalized": norm,
            "a_tau": a_tau(vec, tau_f),
            "accessible_states": acc,
            "shannon_h1": round(shannon_h1(vec), 6),
            "renyi_h2": round(renyi_h2(vec), 6),
            "quartic_purity_m4": round(quartic_purity_m4(vec), 6),
            "executed": False,
            "sentience_claimed": False,
            "tokens_used": 0,
        }

    @staticmethod
    def verify_chiasm_bundle(report: dict[str, Any]) -> dict[str, Any]:
        """Validate Causal Chiasm invariants and canonical SHA-256 integrity."""
        if not isinstance(report, dict):
            return {
                "valid": False,
                "sha256_match": False,
                "contract_match": False,
                "safety_invariants_ok": False,
                "recomputed_sha256": None,
                "claimed_sha256": None,
            }
        sha_ok = verify_report_sha256(report)
        contract_ok = report.get("contract") == CHIASM_CONTRACT
        tokens = report.get("tokens_used")
        invariants_ok = (
            report.get("executed") is False
            and report.get("sentience_claimed") is False
            and type(tokens) is int
            and tokens == 0
        )
        try:
            recomputed: str | None = canonical_sha256(report)
        except (TypeError, ValueError):
            recomputed = None
            sha_ok = False
        return {
            "valid": bool(sha_ok and contract_ok and invariants_ok),
            "sha256_match": sha_ok,
            "contract_match": contract_ok,
            "safety_invariants_ok": invariants_ok,
            "recomputed_sha256": recomputed,
            "claimed_sha256": report.get("report_sha256"),
        }

    @classmethod
    def simulate_pipeline_telemetry(cls) -> dict[str, Any]:
        """Generate 12 deterministic pipeline & compatibility verification episodes."""
        raw_episodes: list[dict[str, float]] = [
            {"frame_ingest": 0.30, "deskew_geom": 0.22, "bg_clean": 0.14, "svg_braille": 0.08, "kloster_atp": 0.08, "chiasm_seal": 0.06, "win7_compat": 0.06, "local_serve": 0.06},
            {"frame_ingest": 0.24, "deskew_geom": 0.26, "bg_clean": 0.18, "svg_braille": 0.09, "kloster_atp": 0.08, "chiasm_seal": 0.05, "win7_compat": 0.05, "local_serve": 0.05},
            {"frame_ingest": 0.16, "deskew_geom": 0.22, "bg_clean": 0.25, "svg_braille": 0.13, "kloster_atp": 0.09, "chiasm_seal": 0.05, "win7_compat": 0.05, "local_serve": 0.05},
            {"frame_ingest": 0.11, "deskew_geom": 0.16, "bg_clean": 0.24, "svg_braille": 0.21, "kloster_atp": 0.11, "chiasm_seal": 0.06, "win7_compat": 0.06, "local_serve": 0.05},
            {"frame_ingest": 0.08, "deskew_geom": 0.12, "bg_clean": 0.19, "svg_braille": 0.25, "kloster_atp": 0.15, "chiasm_seal": 0.08, "win7_compat": 0.07, "local_serve": 0.06},
            {"frame_ingest": 0.07, "deskew_geom": 0.10, "bg_clean": 0.15, "svg_braille": 0.22, "kloster_atp": 0.20, "chiasm_seal": 0.11, "win7_compat": 0.08, "local_serve": 0.07},
            # Nexus 6: Kloster A_tau + Chiasm seal handover to target runtimes
            {"frame_ingest": 0.06, "deskew_geom": 0.08, "bg_clean": 0.12, "svg_braille": 0.17, "kloster_atp": 0.23, "chiasm_seal": 0.16, "win7_compat": 0.10, "local_serve": 0.08},
            {"frame_ingest": 0.05, "deskew_geom": 0.07, "bg_clean": 0.10, "svg_braille": 0.14, "kloster_atp": 0.21, "chiasm_seal": 0.19, "win7_compat": 0.13, "local_serve": 0.11},
            {"frame_ingest": 0.05, "deskew_geom": 0.06, "bg_clean": 0.09, "svg_braille": 0.12, "kloster_atp": 0.19, "chiasm_seal": 0.20, "win7_compat": 0.15, "local_serve": 0.14},
            {"frame_ingest": 0.04, "deskew_geom": 0.06, "bg_clean": 0.08, "svg_braille": 0.11, "kloster_atp": 0.18, "chiasm_seal": 0.20, "win7_compat": 0.17, "local_serve": 0.16},
            {"frame_ingest": 0.04, "deskew_geom": 0.05, "bg_clean": 0.08, "svg_braille": 0.11, "kloster_atp": 0.17, "chiasm_seal": 0.19, "win7_compat": 0.18, "local_serve": 0.18},
            {"frame_ingest": 0.04, "deskew_geom": 0.05, "bg_clean": 0.07, "svg_braille": 0.11, "kloster_atp": 0.17, "chiasm_seal": 0.19, "win7_compat": 0.18, "local_serve": 0.19},
        ]
        telem = compute_distribution_telemetry(raw_episodes, tau=0.10, nexus_idx=6, horizon=5)
        telem["pipeline_stages"] = list(cls.PIPELINE_STAGES)
        telem["win7_modern_matrix"] = list(cls.WIN7_MODERN_MATRIX)
        return telem
