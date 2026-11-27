"""Tier 4: Real-world headless application scenarios (F1-F8 / R1-R5)."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import pytest

from fieldglass.showcase import make_range_handler
from validators import (
    extract_html_scripts_and_local_js,
    launch_loopback_http_script,
    validate_js_execution_node,
    validate_nonclinical_framing,
    validate_pptx_deck,
)

pytestmark = pytest.mark.tier4

FORBIDDEN_MONOREPO_PATH = "/media/cowboy/research/" + "zoe-monorepo"
PREEXISTING_UNTRACKED = frozenset(
    {
        "Fieldglass_Room_Summary.pptx",
        "examples/build_room_summary_pptx.py",
        "exports/",
    }
)


def test_tier4_scenario1_zoe_hospital_win7_live_loopback_server(docs_root: Path) -> None:
    """Scenario 1: Launch zoe_hospital_win7.py on 127.0.0.1 ephemeral port and exercise HTTP endpoints."""
    py_path = docs_root / "zoe-hospital" / "zoe_hospital_win7.py"
    proc, base_url, out_lines = launch_loopback_http_script(py_path, timeout_sec=10.0)
    try:
        with urllib.request.urlopen(base_url + "/", timeout=3.0) as resp:
            assert resp.status == 200
            ctype = resp.headers.get("Content-Type", "")
            assert "text/html" in ctype.lower()
            root_html = resp.read().decode("utf-8")
        validate_nonclinical_framing(text=root_html, label="live zoe_hospital_win7.py /")

        with urllib.request.urlopen(base_url + "/zoe_hospital_kiosk.html", timeout=3.0) as resp:
            assert resp.status == 200
            kiosk_html = resp.read().decode("utf-8")
        assert "zoe" in kiosk_html.lower()
        validate_nonclinical_framing(text=kiosk_html, label="live /zoe_hospital_kiosk.html")

        with urllib.request.urlopen(base_url + "/manifest.json", timeout=3.0) as resp:
            assert resp.status == 200
            manifest = json.loads(resp.read().decode("utf-8"))
        validate_nonclinical_framing(data_or_path=manifest)

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(base_url + "/nonexistent_endpoint_check", timeout=2.0)
        assert exc_info.value.code in (403, 404)
    finally:
        proc.terminate()
        try:
            rem_out, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            rem_out, stderr = proc.communicate(timeout=5)
        full_stdout = "".join(out_lines) + (rem_out or "")
        assert "Traceback" not in stderr, f"Stderr traceback: {stderr}"
        assert "\x1b" not in full_stdout and "\x1b" not in stderr


def test_tier4_scenario2_pptx_libreoffice_pdftoppm_visual_render(
    docs_root: Path,
    pptx_render_cache,
) -> None:
    """Scenario 2: Parse .pptx, convert via LibreOffice + pdftoppm, and verify every slide is non-blank."""
    pptx_p = docs_root / "Fieldglass_Observatory_Expansion.pptx"
    deck = validate_pptx_deck(
        pptx_p,
        required_topics=("MS-DOS", "Flight", "Medical", "Software", "ChatGPT", "Anthropic", "Grok", "SpaceX", "Zoe", "Hospital"),
        min_slides=8,
    )
    low = deck["full_text"].lower()
    assert "claire" in low or "grimes" in low
    validate_nonclinical_framing(text=deck["full_text"], label=str(pptx_p))

    rendered = pptx_render_cache(pptx_p, 5.0)
    assert rendered.slide_count == deck["slide_count"]
    assert len(rendered.slide_pngs) == deck["slide_count"]
    assert all(std > 5.0 for std in rendered.slide_stds)


def test_tier4_scenario3_node_headless_js_simulation_execution(docs_root: Path) -> None:
    """Scenario 3: Execute R1 and R3 interactive JS simulators headlessly inside Node vm.createContext."""
    targets = (
        docs_root / "msdos" / "index.html",
        docs_root / "flight-sim" / "index.html",
        docs_root / "medical-sim" / "index.html",
        docs_root / "software" / "index.html",
        docs_root / "zoe-hospital" / "zoe_hospital_kiosk.html",
        docs_root / "zoe-hospital" / "zoe_hospital_kiosk.hta",
    )
    for html_path in targets:
        scripts = extract_html_scripts_and_local_js(html_path)
        validate_js_execution_node(scripts, label=f"tier4-node:{html_path}")


def test_tier4_scenario4_observatory_range_server_crawl(docs_root: Path) -> None:
    """Scenario 4: Serve docs/ via fieldglass.showcase.make_range_handler, crawl R1-R4 & HTTP 206 .pptx."""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_range_handler(docs_root))
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        routes = (
            "/",
            "/msdos/",
            "/flight-sim/",
            "/medical-sim/",
            "/software/",
            "/improvements/",
            "/improvements/chatgpt/",
            "/improvements/anthropic/",
            "/improvements/grok/",
            "/improvements/spacex/",
            "/improvements/claire-grimes/",
            "/zoe-hospital/",
        )
        for route in routes:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{route}", timeout=3.0) as resp:
                assert resp.status == 200, f"Unexpected HTTP {resp.status} for {route}"
                body = resp.read().decode("utf-8")
                assert "<html" in body.lower() or "<!doctype" in body.lower()

        pptx_disk = (docs_root / "Fieldglass_Observatory_Expansion.pptx").read_bytes()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/Fieldglass_Observatory_Expansion.pptx",
            headers={"Range": "bytes=0-1023"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            assert resp.status == 206
            chunk = resp.read()
            assert len(chunk) == 1024
            assert chunk == pptx_disk[:1024]
    finally:
        srv.shutdown()
        srv.server_close()


def test_tier4_scenario5_repo_hygiene_monorepo_boundary_and_cli_smoke(obs_root: Path) -> None:
    """Scenario 5: Enforce R5 git hygiene, zero zoe-monorepo references, and fieldglass.cli smoke check."""
    # 1. Pre-existing untracked protected items must remain intact if present on baseline
    git_proc = subprocess.run(
        ["git", "-C", str(obs_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert git_proc.returncode == 0, f"git status failed: {git_proc.stderr}"
    for line in git_proc.stdout.splitlines():
        path_part = line[3:].strip()
        assert ".agents/" not in path_part, f"Agent metadata leaked into repo tree: {line}"
        assert not path_part.endswith((".pyc", ".pyo")), f"Compiled bytecode leaked: {line}"

    # 2. Zero references to forbidden external monorepo across new/modified code, docs, and tests
    text_exts = {".py", ".html", ".htm", ".hta", ".js", ".css", ".json", ".md", ".bat", ".svg", ".txt", ".ini"}
    hits: list[str] = []
    scan_files: list[Path] = []
    for single in (obs_root / "README.md", obs_root / "docs" / "index.html"):
        if single.is_file():
            scan_files.append(single)
    for d in ("src", "tests"):
        root = obs_root / d
        if root.is_dir():
            scan_files.extend(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in text_exts)
    for mod in ("msdos", "flight-sim", "medical-sim", "software", "improvements", "zoe-hospital"):
        mdir = obs_root / "docs" / mod
        if mdir.is_dir():
            scan_files.extend(p for p in mdir.rglob("*") if p.is_file() and p.suffix.lower() in text_exts)
    examples_dir = obs_root / "examples"
    if examples_dir.is_dir():
        for p in examples_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in text_exts and not p.name.startswith(("specimen1", "specimen2", "specimen3")):
                scan_files.append(p)

    for fpath in scan_files:
        txt = fpath.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN_MONOREPO_PATH in txt:
            hits.append(str(fpath))
    assert not hits, f"Forbidden monorepo reference found in: {hits}"

    # 3. fieldglass.cli --help and --version smoke check
    env = dict(os.environ)
    env["PYTHONPATH"] = str(obs_root / "src")
    for flag in ("--help", "--version"):
        cli_proc = subprocess.run(
            [sys.executable, "-m", "fieldglass.cli", flag],
            cwd=str(obs_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert cli_proc.returncode == 0, f"fieldglass.cli {flag} failed: {cli_proc.stderr}"
        assert "fieldglass" in cli_proc.stdout.lower()
