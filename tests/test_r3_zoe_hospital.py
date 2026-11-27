"""Verification suite for Milestone M3: Zoe Hospital Edition (Windows 7-Era, Non-Clinical)."""

from __future__ import annotations

import ast
import hashlib
import http.client
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import zipfile

from PIL import Image
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ZOE_DIR = REPO_ROOT / "docs" / "zoe-hospital"
BUILDER_PATH = REPO_ROOT / "examples" / "build_r3_zoe_hospital.py"
SERVER_PATH = ZOE_DIR / "zoe_hospital_win7.py"

REQUIRED_FILES = (
    "index.html",
    "zoe_hospital_kiosk.html",
    "zoe_hospital_kiosk.hta",
    "zoe_hospital_win7.py",
    "launch_win7.bat",
    "manifest.json",
    "chiasm_report.json",
    "summary.json",
    "chiasm_tomography.svg",
    "preview.png",
    "zoe_hospital_win7_bundle.zip",
    "README_WIN7.txt",
)

BUNDLE_MEMBERS = (
    "README_WIN7.txt",
    "chiasm_report.json",
    "chiasm_tomography.svg",
    "index.html",
    "launch_win7.bat",
    "manifest.json",
    "preview.png",
    "summary.json",
    "zoe_hospital_kiosk.hta",
    "zoe_hospital_kiosk.html",
    "zoe_hospital_win7.py",
)

MODERN_STDLIB_ONLY = {"tomllib", "zoneinfo", "graphlib"}
PEP585_BUILTINS = {"list", "dict", "tuple", "set", "frozenset", "type"}


def _sha256_seal(payload: dict) -> str:
    body = {k: v for k, v in payload.items() if k != "report_sha256"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _strip_js_comments_and_strings(js_src: str) -> str:
    """Strip /*...*/, //... comments, regex literals, and '...' / "..." string literals."""
    out = []
    i = 0
    n = len(js_src)
    prev_sig = ""
    while i < n:
        ch = js_src[i]
        nxt = js_src[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "*":
            end = js_src.find("*/", i + 2)
            i = n if end == -1 else end + 2
            out.append(" ")
        elif ch == "/" and nxt == "/":
            end = js_src.find("\n", i + 2)
            i = n if end == -1 else end + 1
            out.append("\n")
        elif ch == "/" and prev_sig in ("", "(", "=", ",", ":", "!", "&", "|", "?", "[", "{", ";"):
            i += 1
            in_cls = False
            while i < n:
                if js_src[i] == "\\":
                    i += 2
                    continue
                if js_src[i] == "[":
                    in_cls = True
                elif js_src[i] == "]":
                    in_cls = False
                elif js_src[i] == "/" and not in_cls:
                    i += 1
                    break
                i += 1
            while i < n and js_src[i].isalpha():
                i += 1
            out.append(" /re/ ")
            prev_sig = "r"
        elif ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if js_src[i] == "\\":
                    i += 2
                    continue
                if js_src[i] == quote:
                    i += 1
                    break
                i += 1
            out.append('""')
            prev_sig = '"'
        else:
            out.append(ch)
            if not ch.isspace():
                prev_sig = ch
            i += 1
    return "".join(out)


def _extract_scripts(html_text: str) -> list[str]:
    return re.findall(r"<script[^>]*>(.*?)</script>", html_text, flags=re.IGNORECASE | re.DOTALL)


def _extract_styles(html_text: str) -> list[str]:
    return re.findall(r"<style[^>]*>(.*?)</style>", html_text, flags=re.IGNORECASE | re.DOTALL)


def _find_node_bin() -> str:
    found = shutil.which("node")
    if found:
        return found
    nvm_node = Path("/home/cowboy/.nvm/versions/node/v24.16.0/bin/node")
    if nvm_node.is_file():
        return str(nvm_node)
    pytest.skip("node binary not found for JS VM execution test")
    return ""


def test_r3_required_files_and_sizes():
    assert BUILDER_PATH.is_file(), "Missing examples/build_r3_zoe_hospital.py"
    assert ZOE_DIR.is_dir(), "Missing docs/zoe-hospital/"
    for name in REQUIRED_FILES:
        p = ZOE_DIR / name
        assert p.is_file(), f"Missing deliverable: {p}"
        sz = p.stat().st_size
        assert sz > 0, f"Empty deliverable: {p}"
        assert sz < 50 * 1024 * 1024, f"File exceeds 50 MB limit: {p} ({sz})"

    assert (ZOE_DIR / "preview.png").stat().st_size < 5 * 1024 * 1024
    assert (ZOE_DIR / "zoe_hospital_win7_bundle.zip").stat().st_size < 5 * 1024 * 1024


def test_r3_builder_reproducible_without_pythonpath(tmp_path: Path):
    # Verify builder runs cleanly without PYTHONPATH set (uses built-in src/ fallback)
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
    proc = subprocess.run(
        ["/usr/bin/python3", str(BUILDER_PATH)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Zoe Hospital Edition" in proc.stdout

    # Also verify build_all produces identical deterministic outputs in an isolated directory
    sys.path.insert(0, str(REPO_ROOT / "examples"))
    try:
        import build_r3_zoe_hospital as builder
        out_tmp = tmp_path / "zoe_hospital_copy"
        builder.build_all(out_tmp)
        for name in REQUIRED_FILES:
            if name in ("preview.png", "zoe_hospital_win7_bundle.zip"):
                assert (out_tmp / name).stat().st_size > 0
            else:
                assert (out_tmp / name).read_bytes() == (ZOE_DIR / name).read_bytes(), (
                    f"Non-deterministic output in {name}"
                )
    finally:
        if str(REPO_ROOT / "examples") in sys.path:
            sys.path.remove(str(REPO_ROOT / "examples"))


def test_r3_python_win7_ast_and_stdlib_compat():
    src = SERVER_PATH.read_text(encoding="utf-8")
    assert "\x1b[" not in src and "\033[" not in src and "\\x1b" not in src and "\\033" not in src
    src.encode("ascii")  # pure 7-bit ASCII source for Win7 cmd.exe safety

    # Python 3.7 parser rejects :=, match/case, and positional-only /
    tree37 = ast.parse(src, feature_version=(3, 7))
    tree_cur = ast.parse(src)

    for tree in (tree37, tree_cur):
        for node in ast.walk(tree):
            assert not isinstance(node, ast.NamedExpr), "Walrus operator := is not Python 3.7 compatible"
            if hasattr(ast, "Match"):
                assert not isinstance(node, ast.Match), "match/case is not Python 3.7/3.8 compatible"

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert not getattr(node.args, "posonlyargs", []), "Positional-only / is not Python 3.7 compatible"

            # Check annotations for PEP 604 BitOr (X | Y) and PEP 585 builtins (list[int], etc.)
            ann_nodes = []
            if isinstance(node, ast.AnnAssign) and node.annotation is not None:
                ann_nodes.append(node.annotation)
            elif isinstance(node, ast.arg) and node.annotation is not None:
                ann_nodes.append(node.annotation)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None:
                ann_nodes.append(node.returns)

            for ann in ann_nodes:
                for sub in ast.walk(ann):
                    assert not (
                        isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr)
                    ), "PEP 604 union annotation X | Y is not Python 3.7/3.8 compatible"
                    if isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Name):
                        assert sub.value.id not in PEP585_BUILTINS, (
                            f"PEP 585 subscripted builtin {sub.value.id}[...] requires Python 3.9+"
                        )

            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in sys.stdlib_module_names and top not in MODERN_STDLIB_ONLY, (
                        f"Non-Win7/non-stdlib import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                assert top in sys.stdlib_module_names and top not in MODERN_STDLIB_ONLY, (
                    f"Non-Win7/non-stdlib import: {node.module}"
                )


def test_r3_html_hta_win7_es5_and_css_compat():
    for fname in ("index.html", "zoe_hospital_kiosk.html", "zoe_hospital_kiosk.hta"):
        text = (ZOE_DIR / fname).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in text
        assert '<meta charset="utf-8" />' in text
        assert '<meta http-equiv="X-UA-Compatible" content="IE=edge" />' in text
        assert "NOT FOR CLINICAL" in text.upper()
        assert "SIMULATED / EDUCATIONAL ONLY" in text.upper()

        # Zero external CDN or remote asset references
        assert not re.search(r'(?:src|href)\s*=\s*["\'](?:https?:)?//', text, flags=re.IGNORECASE), (
            f"External URL found in {fname}"
        )
        assert "@import" not in text.lower(), f"@import forbidden in {fname}"

        for css in _extract_styles(text):
            assert not re.search(r"display\s*:\s*grid", css, flags=re.IGNORECASE), f"CSS Grid forbidden in {fname}"
            assert not re.search(r"display\s*:\s*flex", css, flags=re.IGNORECASE), f"CSS Flexbox forbidden in {fname}"
            assert "var(--" not in css, f"CSS custom property var(--*) forbidden in {fname}"
            assert "clamp(" not in css.lower(), f"CSS clamp() forbidden in {fname}"

    hta_text = (ZOE_DIR / "zoe_hospital_kiosk.hta").read_text(encoding="utf-8")
    assert "<HTA:APPLICATION" in hta_text
    assert "ZoeHospitalKiosk.commandLine" not in hta_text

    # Strict ES5 scan across both HTML and HTA kiosks
    es6_patterns = [
        r"`",
        r"\b(let|const|class|extends|super|import|export|async|await|yield|Symbol|Proxy|Reflect|WeakMap|WeakSet|Map|Set|Promise|fetch|URLSearchParams)\b",
        r"=>",
        r"\.\.\.",
        r"for\s*\([^)]*\bof\b",
        r"Math\.log2",
        r"\.(includes|startsWith|endsWith|repeat|padStart|padEnd|classList)\b",
        r"Object\.(assign|entries|values|keys)\b",
        r"Array\.(from|isArray)\b",
        r",\s*[\}\]]",
    ]

    for fname in ("zoe_hospital_kiosk.html", "zoe_hospital_kiosk.hta"):
        scripts = _extract_scripts((ZOE_DIR / fname).read_text(encoding="utf-8"))
        assert len(scripts) >= 1
        for script in scripts:
            code_only = _strip_js_comments_and_strings(script)
            for pat in es6_patterns:
                m = re.search(pat, code_only)
                assert m is None, f"Forbidden ES6+/IE11-incompatible construct {pat!r} matched {m.group(0)!r} in {fname}"


def test_r3_node_vm_kiosk_execution(tmp_path: Path):
    node_bin = _find_node_bin()
    for idx, fname in enumerate(("zoe_hospital_kiosk.html", "zoe_hospital_kiosk.hta")):
        scripts = _extract_scripts((ZOE_DIR / fname).read_text(encoding="utf-8"))
        combined_js = "\n".join(scripts)

        harness = r"""
const vm = require("vm");
const fs = require("fs");
const code = fs.readFileSync(process.argv[2], "utf8");

function makeEl(id) {
  return {
    id: id,
    value: id === "tauSelect" ? "0.10" : "ZOE TEST",
    checked: id === "chk0" || id === "chk1",
    className: "",
    style: {},
    textContent: "",
    innerText: "",
    innerHTML: "",
    addEventListener: function () {}
  };
}
const els = {};
const sandbox = {
  Math: Math,
  JSON: JSON,
  Object: Object,
  Array: Array,
  String: String,
  Number: Number,
  Error: Error,
  parseFloat: parseFloat,
  isNaN: isNaN,
  document: {
    getElementById: function (id) {
      if (!els[id]) { els[id] = makeEl(id); }
      return els[id];
    }
  },
  window: null,
  navigator: { userAgent: "MSIE 9.0; Windows NT 6.1" }
};
sandbox.window = sandbox;
vm.runInNewContext(code, sandbox, { filename: process.argv[2] });

const K = sandbox.ZoeHospitalKiosk;
if (!K) { throw new Error("Missing ZoeHospitalKiosk global"); }

const msg1 = K.selectCommTile(2);
const msg2 = K.addCustomCommNote("Quiet comfort drill");
const br = K.textToBrailleMatrix("ZOE WIN7");
if (br.brailleLines.length !== 2) { throw new Error("Expected 2 Braille rows"); }
if (br.clinical_use !== false || br.executed !== false) { throw new Error("Braille non-clinical invariant failed"); }

// Strict > tau inequality test matching src/fieldglass/metrics.py
const strict3 = K.aTau({ a: 0.5, b: 0.25, c: 0.15, d: 0.10 }, 0.10);
const strict0 = K.aTau({ a: 0.5, b: 0.25, c: 0.15, d: 0.10 }, 0.50);
if (strict3 !== 3 || strict0 !== 0) { throw new Error("Strict aTau inequality failed: " + strict3 + "," + strict0); }

const ch = K.causalChiasm(
  { deep_shadow: 0.1, ink_linework: 0.2, dark_midtone: 0.3, botanical_mid: 0.4 },
  { deep_shadow: 0.2, ink_linework: 0.2, dark_midtone: 0.3, botanical_mid: 0.3 },
  0.15,
  4
);
if (ch.contract !== "fieldglass-causal-chiasm/v1") { throw new Error("Bad contract"); }
if (ch.executed !== false || ch.sentience_claimed !== false || ch.clinical_use !== false || ch.tokens_used !== 0) {
  throw new Error("Chiasm safety flags failed");
}

const chkBefore = K.getChecklistSummary();
const chkAfter = K.resetChecklist();
if (chkBefore.verified_count !== 2 || chkAfter.verified_count !== 0) {
  throw new Error("Checklist toggle/reset failed");
}
K.switchTab(1);
K.clearCommLog();

console.log(JSON.stringify({
  ok: true,
  msg1: msg1,
  msg2: msg2,
  brailleCols: br.cols,
  chiasmGlyph: ch.presence_glyph,
  checklistBefore: chkBefore.verified_count,
  checklistAfter: chkAfter.verified_count
}));
"""
        script_tmp = tmp_path / f"_vm_check_{idx}.js"
        harness_tmp = tmp_path / f"_vm_harness_{idx}.cjs"
        script_tmp.write_text(combined_js, encoding="utf-8")
        harness_tmp.write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            [node_bin, str(harness_tmp), str(script_tmp)],
            capture_output=True,
            text=True,
            check=True,
        )
        res = json.loads(proc.stdout.strip())
        assert res["ok"] is True
        assert res["brailleCols"] > 0
        assert res["chiasmGlyph"] in ("^_^", "??", "~")


def test_r3_win7_server_selftest_and_live_loopback():
    # 1. Run --self-test under cp1252 (simulates Windows 7 cmd.exe codepage)
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONIOENCODING": "cp1252"}
    self_proc = subprocess.run(
        ["/usr/bin/python3", str(SERVER_PATH), "--self-test"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "SELF-TEST OK" in self_proc.stdout
    assert "\x1b[" not in self_proc.stdout and "\x1b[" not in self_proc.stderr

    # 2. Verify non-loopback host rejection
    bad_proc = subprocess.run(
        ["/usr/bin/python3", str(SERVER_PATH), "--host", "0.0.0.0", "--no-browser"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert bad_proc.returncode != 0
    assert "Loopback host required" in bad_proc.stderr

    # 3. Live ephemeral loopback HTTP/1.1 test
    srv_proc = subprocess.Popen(
        ["/usr/bin/python3", str(SERVER_PATH), "--port", "0", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert srv_proc.stdout is not None
        url = ""
        for _ in range(10):
            line = srv_proc.stdout.readline()
            if not line:
                break
            if line.startswith("ZOE_HOSPITAL_URL="):
                url = line.split("=", 1)[1].strip()
                break
        assert url.startswith("http://127.0.0.1:"), f"Did not receive loopback URL, got: {url!r}"
        parsed = urllib.parse.urlparse(url)
        host, port = parsed.hostname, parsed.port
        assert host == "127.0.0.1" and port is not None

        for path in (
            "/",
            "/index.html",
            "/zoe_hospital_kiosk.html",
            "/zoe_hospital_kiosk.hta",
            "/api/health",
            "/api/status",
            "/api/chiasm?tau=0.10",
            "/api/braille?text=HELLO",
            "/api/manifest",
        ):
            conn = http.client.HTTPConnection(host, port, timeout=3)
            conn.request("GET", path)
            resp = conn.getresponse()
            body = resp.read()
            cl_header = resp.getheader("Content-Length")
            conn.close()
            assert resp.status == 200, f"GET {path} returned {resp.status}"
            assert cl_header is not None and int(cl_header) == len(body)
            if path.startswith("/api/"):
                data = json.loads(body.decode("utf-8"))
                assert data.get("clinical_use") is False
                assert data.get("executed") is False

        # POST /api/metrics check
        conn = http.client.HTTPConnection(host, port, timeout=3)
        post_raw = json.dumps({"tau": 0.10, "distribution": [0.5, 0.25, 0.15, 0.10]}).encode("utf-8")
        conn.request("POST", "/api/metrics", body=post_raw, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        assert resp.status == 200
        met = json.loads(body.decode("utf-8"))
        assert met["a_tau"] == 3  # strict > excludes 0.10
        assert met["clinical_use"] is False and met["executed"] is False and met["tokens_used"] == 0

        # Path traversal rejection check
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", "/../../README.md")
        resp = conn.getresponse()
        resp.read()
        conn.close()
        assert resp.status == 404
    finally:
        srv_proc.terminate()
        srv_proc.wait(timeout=5)

    # 4. --once flag test
    once_proc = subprocess.Popen(
        ["/usr/bin/python3", str(SERVER_PATH), "--port", "0", "--once", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert once_proc.stdout is not None
        url = ""
        for _ in range(10):
            line = once_proc.stdout.readline()
            if line.startswith("ZOE_HOSPITAL_URL="):
                url = line.split("=", 1)[1].strip()
                break
        parsed = urllib.parse.urlparse(url)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=3)
        conn.request("GET", "/api/health")
        resp = conn.getresponse()
        resp.read()
        conn.close()
        assert resp.status == 200
        rc = once_proc.wait(timeout=5)
        assert rc == 0
    finally:
        if once_proc.poll() is None:
            once_proc.terminate()
            once_proc.wait(timeout=5)


def test_r3_batch_launcher_and_zip_bundle():
    bat_raw = (ZOE_DIR / "launch_win7.bat").read_bytes()
    assert b"\r\n" in bat_raw
    assert b"\n" not in bat_raw.replace(b"\r\n", b"")
    bat_txt = bat_raw.decode("ascii")
    assert "py -3" in bat_txt
    assert "python " in bat_txt
    assert "mshta.exe" in bat_txt
    assert "zoe_hospital_kiosk.hta" in bat_txt
    assert "zoe_hospital_kiosk.html" in bat_txt

    zip_path = ZOE_DIR / "zoe_hospital_win7_bundle.zip"
    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.testzip() is None
        names = sorted(zf.namelist())
        assert names == sorted(BUNDLE_MEMBERS)
        for name in names:
            assert not name.startswith("/") and ".." not in name
            assert zf.read(name) == (ZOE_DIR / name).read_bytes()

        # Verify every manifest.json file entry and index.html local relative asset is inside the ZIP
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        for entry in manifest["files"]:
            assert entry["path"] in names, f"Manifest file missing from ZIP: {entry['path']}"

        index_html = zf.read("index.html").decode("utf-8")
        for rel in re.findall(r'(?:href|src)="([^"]+)"', index_html):
            if rel.startswith("../") or rel == "zoe_hospital_win7_bundle.zip":
                continue
            assert rel in names, f"index.html link missing from ZIP: {rel}"


def test_r3_node_vm_ie7_json_undefined_fallback(tmp_path: Path):
    node_bin = _find_node_bin()
    for idx, fname in enumerate(("zoe_hospital_kiosk.html", "zoe_hospital_kiosk.hta")):
        scripts = _extract_scripts((ZOE_DIR / fname).read_text(encoding="utf-8"))
        combined_js = "\n".join(scripts)

        harness = r"""
const vm = require("vm");
const fs = require("fs");
const code = fs.readFileSync(process.argv[2], "utf8");

function makeEl(id) {
  return {
    id: id,
    value: id === "tauSelect" ? "0.10" : "ZOE IE7",
    checked: id === "chk0" || id === "chk1",
    className: "",
    style: {},
    innerText: "",
    innerHTML: "",
    attachEvent: function () {}
  };
}
const els = {};
let xhrSentArg = "NOT_CALLED";
function MockXHR() {
  this.readyState = 0;
  this.status = 0;
  this.responseText = "";
  this.onreadystatechange = null;
}
MockXHR.prototype.open = function () {};
MockXHR.prototype.send = function (arg) {
  xhrSentArg = arg;
  this.readyState = 4;
  this.status = 200;
  this.responseText = '{"ok":true,"clinical_use":false,"min_windows_version":"Windows 7 SP1 (NT 6.1)"}';
  if (typeof this.onreadystatechange === "function") {
    this.onreadystatechange();
  }
};

const sandbox = {
  Math: Math,
  JSON: undefined,
  Object: Object,
  Array: Array,
  String: String,
  Number: Number,
  Error: Error,
  parseFloat: parseFloat,
  isNaN: isNaN,
  isFinite: isFinite,
  XMLHttpRequest: MockXHR,
  location: { protocol: "http:" },
  document: {
    getElementById: function (id) {
      if (!els[id]) { els[id] = makeEl(id); }
      return els[id];
    }
  },
  window: null,
  navigator: { userAgent: "MSIE 7.0; Windows NT 6.1" }
};
sandbox.window = sandbox;
vm.runInNewContext(code, sandbox, { filename: process.argv[2] });

const K = sandbox.ZoeHospitalKiosk;
if (!K) { throw new Error("Missing ZoeHospitalKiosk global"); }
if (els.panelComm.style.display !== "block" || els.panelChecklist.style.display !== "none") {
  throw new Error("switchTab(0) did not complete during wireUiEvents");
}
if (xhrSentArg !== null) {
  throw new Error("Expected xhr.send(null), got: " + String(xhrSentArg));
}
const chkParsed = JSON.parse(els.checklistJsonBox.innerText);
if (chkParsed.verified_count !== 2 || chkParsed.clinical_use !== false || chkParsed.executed !== false) {
  throw new Error("Fallback JSON serializer produced unexpected payload");
}
const sumAfter = K.getChecklistSummary();
if (sumAfter.verified_count !== 2) { throw new Error("getChecklistSummary failed with JSON undefined"); }
console.log(JSON.stringify({ ok: true, statusText: els.loopbackStatus.innerText, verified: chkParsed.verified_count }));
"""
        script_tmp = tmp_path / f"_vm_ie7_{idx}.js"
        harness_tmp = tmp_path / f"_vm_ie7_harness_{idx}.cjs"
        script_tmp.write_text(combined_js, encoding="utf-8")
        harness_tmp.write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            [node_bin, str(harness_tmp), str(script_tmp)],
            capture_output=True,
            text=True,
            check=True,
        )
        res = json.loads(proc.stdout.strip())
        assert res["ok"] is True
        assert res["verified"] == 2
        assert "fallback" in res["statusText"].lower()


def test_r3_post_metrics_validation_and_unzipped_svg(tmp_path: Path):
    def _strict_json_loads(raw_text: str) -> dict:
        def _bad_const(tok: str) -> None:
            raise ValueError(f"Non-RFC-8259 JSON constant: {tok}")

        return json.loads(raw_text, parse_constant=_bad_const)

    bundle_dir = tmp_path / "unzipped_bundle"
    with zipfile.ZipFile(ZOE_DIR / "zoe_hospital_win7_bundle.zip", "r") as zf:
        zf.extractall(bundle_dir)

    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONIOENCODING": "cp1252"}
    srv_proc = subprocess.Popen(
        ["/usr/bin/python3", str(bundle_dir / "zoe_hospital_win7.py"), "--port", "0", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert srv_proc.stdout is not None
        url = ""
        for _ in range(10):
            line = srv_proc.stdout.readline()
            if not line:
                break
            if line.startswith("ZOE_HOSPITAL_URL="):
                url = line.split("=", 1)[1].strip()
                break
        assert url.startswith("http://127.0.0.1:")
        parsed = urllib.parse.urlparse(url)
        host, port = parsed.hostname, parsed.port
        assert host == "127.0.0.1" and port is not None

        # 1. Unzipped bundle serves chiasm_tomography.svg cleanly (200 OK)
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", "/chiasm_tomography.svg")
        resp = conn.getresponse()
        svg_body = resp.read().decode("utf-8")
        conn.close()
        assert resp.status == 200
        assert "<svg" in svg_body

        # 2. Invalid POST /api/metrics payloads must return HTTP 400 + valid RFC-8259 JSON
        bad_payloads = [
            json.dumps({"tau": 0.1, "distribution": {"a": "oops", "b": 0.5}}),
            json.dumps({"tau": 0.1, "distribution": {"a": 0.5, "b": 0.5}, "future": {"a": "bad"}}),
            json.dumps({"tau": 0.1, "distribution": {"a": 0.5, "b": 0.5}, "future": {}}),
            json.dumps({"tau": 0.1, "distribution": {"a": 0.5, "b": 0.5}, "future": [0.5, 0.5]}),
            json.dumps({"tau": "nan", "distribution": {"a": 0.5, "b": 0.5}}),
            json.dumps({"tau": "inf", "distribution": {"a": 0.5, "b": 0.5}}),
            json.dumps({"tau": 0.1, "distribution": {"a": "nan", "b": 0.5}}),
            json.dumps({"tau": 0.1, "distribution": {"a": "inf", "b": 0.5}}),
            '{"tau": NaN, "distribution": {"a": 0.5, "b": 0.5}}',
            '{"tau": 0.1, "distribution": {"a": Infinity, "b": 0.5}}',
            json.dumps({"tau": -0.5, "distribution": {"a": 0.5, "b": 0.5}}),
            json.dumps({"tau": 1.5, "distribution": {"a": 0.5, "b": 0.5}}),
            json.dumps({"tau": 0.1, "distribution": {"a": -5.0, "b": 10.0}}),
            json.dumps({"tau": 0.1, "distribution": {"a": -5.0, "b": -10.0}}),
            json.dumps({"tau": 0.1, "distribution": {"a": 0.0, "b": 0.0}}),
            json.dumps({"tau": 0.1, "distribution": {}}),
            json.dumps({"tau": 0.1, "distribution": []}),
            json.dumps({"tau": 0.1, "distribution": [0.5, "bad"]}),
            json.dumps({"tau": 0.1, "distribution": {"a": 0.5, "b": 0.5}, "future": {"a": -1.0, "b": 2.0}}),
            json.dumps({"tau": 0.1, "distribution": {"a": 0.5, "b": 0.5}, "future": {"a": 0.0, "b": 0.0}}),
        ]
        for raw_json in bad_payloads:
            conn = http.client.HTTPConnection(host, port, timeout=3)
            conn.request(
                "POST",
                "/api/metrics",
                body=raw_json.encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            resp = conn.getresponse()
            body_text = resp.read().decode("utf-8")
            cl = resp.getheader("Content-Length")
            conn.close()
            assert resp.status == 400, f"Expected 400 for {raw_json}, got {resp.status}: {body_text}"
            assert cl is not None and int(cl) == len(body_text.encode("utf-8"))
            err_data = _strict_json_loads(body_text)
            assert err_data.get("ok") is False
            assert isinstance(err_data.get("error"), str) and len(err_data["error"]) > 0

        # 3. Valid POST /api/metrics with zero-weight item alongside positive weight + valid future dict
        conn = http.client.HTTPConnection(host, port, timeout=3)
        ok_body = json.dumps(
            {
                "tau": 0.10,
                "distribution": {"a": 0.0, "b": 1.0},
                "future": {"a": 0.25, "b": 0.75},
            }
        ).encode("utf-8")
        conn.request("POST", "/api/metrics", body=ok_body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        body_text = resp.read().decode("utf-8")
        conn.close()
        assert resp.status == 200
        ok_data = _strict_json_loads(body_text)
        assert ok_data["ok"] is True
        assert ok_data["chiasm"] is not None
        assert ok_data["clinical_use"] is False and ok_data["executed"] is False
    finally:
        srv_proc.terminate()
        srv_proc.wait(timeout=5)


def test_r3_invariants_non_clinical_and_gps_metadata():
    for json_name in ("manifest.json", "chiasm_report.json", "summary.json"):
        data = json.loads((ZOE_DIR / json_name).read_text(encoding="utf-8"))
        assert data["contract"] == "fieldglass-causal-chiasm/v1"
        assert data["executed"] is False
        assert data["sentience_claimed"] is False
        assert data["tokens_used"] == 0
        assert data["clinical_use"] is False
        assert data["educational_simulation_only"] is True
        assert data["clinical_certification_claimed"] is False
        assert data["min_windows_version"] == "Windows 7 SP1 (NT 6.1)"
        assert "NOT FOR CLINICAL" in data["disclaimer"].upper()
        assert len(data["report_sha256"]) == 64
        assert data["report_sha256"] == _sha256_seal(data), f"SHA-256 seal mismatch in {json_name}"

    manifest = json.loads((ZOE_DIR / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        raw = (ZOE_DIR / entry["path"]).read_bytes()
        assert len(raw) == entry["bytes"]
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]

    svg_txt = (ZOE_DIR / "chiasm_tomography.svg").read_text(encoding="utf-8")
    assert "<svg" in svg_txt and "Non-Clinical" in svg_txt

    preview_path = ZOE_DIR / "preview.png"
    with Image.open(preview_path) as im:
        assert im.size == (1280, 720)

    exif_proc = subprocess.run(
        ["exiftool", "-j", "-GPS:all", str(preview_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    exif_rows = json.loads(exif_proc.stdout)
    assert len(exif_rows) == 1
    gps_keys = [k for k in exif_rows[0].keys() if k != "SourceFile"]
    assert gps_keys == [], f"Unexpected GPS metadata on preview.png: {gps_keys}"
