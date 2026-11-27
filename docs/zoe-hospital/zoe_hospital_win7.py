#!/usr/bin/env python3
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
        "unicode_preview": "\n".join(braille_lines),
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
    parts = [p for p in rel.replace("\\", "/").split("/") if p not in ("", ".")]
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
            sys.stdout.write("[zoe-hospital-win7] %s - %s\n" % (self.address_string(), safe_msg))
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
            raw = (json.dumps(payload, indent=2, allow_nan=False) + "\n").encode("utf-8")
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
        "contract=%s | a_tau_strict=OK | loopback=127.0.0.1 | clinical_use=false\n" % CONTRACT
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
        sys.stderr.write("ERROR: %s\n" % str(exc))
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
    sys.stdout.write("ZOE HOSPITAL EDITION (WIN7-ERA / SIMULATED NON-CLINICAL)\n")
    sys.stdout.write("DISCLAIMER: %s\n" % DISCLAIMER)
    sys.stdout.write("ZOE_HOSPITAL_URL=%s\n" % url)
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
