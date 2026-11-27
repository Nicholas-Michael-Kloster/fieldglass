"""Unit, contract, media-hygiene, and headless browser E2E tests for M1 R1 deliverables."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from fieldglass.metrics import (
    CONTRACT,
    a_tau,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)
from fieldglass.observatory_r1 import (
    FAT12_GEOMETRY,
    MSDOS8086Model,
    MSDOS_MEMORY_REGIONS,
    SUMMARY_CONTRACT,
    FlightSim6DOF,
    MedicalSandboxModel,
    SoftwareObservatoryModel,
    canonical_sha256,
    isa_density,
    seal_chiasm_report,
    verify_report_sha256,
)
from fieldglass.showcase import make_range_handler

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

DOMAINS: tuple[tuple[str, str], ...] = (
    ("msdos", "msdos"),
    ("flight-sim", "flight_sim"),
    ("medical-sim", "medical_sim"),
    ("software", "software"),
)


def test_msdos_8086_model_determinism_and_shell():
    conv = sum(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["area"] == "Conventional")
    uma = sum(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["area"] == "UMA")
    hma = sum(r["bytes"] for r in MSDOS_MEMORY_REGIONS if r["area"] == "HMA")
    assert conv == 655_360
    assert uma == 393_216
    assert hma == 65_520
    assert FAT12_GEOMETRY["total_sectors"] * FAT12_GEOMETRY["bytes_per_sector"] == 1_474_560

    dos = MSDOS8086Model()
    assert dos.phys_addr(0x0800, 0x0100, a20_enabled=True) == 0x08100
    assert dos.phys_addr(0xFFFF, 0x0020, a20_enabled=True) == 0x100010
    assert dos.phys_addr(0xFFFF, 0x0020, a20_enabled=False) == 0x00010

    assert any("6.22" in ln for ln in dos.run_command("VER")["output_lines"])
    assert any("FIELDGLS" in ln for ln in dos.run_command("DIR")["output_lines"])
    assert any("614,400" in ln for ln in dos.run_command("MEM")["output_lines"])
    assert any("1,474,560" in ln for ln in dos.run_command("CHKDSK")["output_lines"])
    assert any("HIMEM.SYS" in ln for ln in dos.run_command("TYPE CONFIG.SYS")["output_lines"])
    assert any("Ready." in ln for ln in dos.run_command("AUTOEXEC.BAT")["output_lines"])
    assert dos.run_command("CLS")["clear_screen"] is True
    assert any("DIR" in ln for ln in dos.run_command("HELP")["output_lines"])

    step0 = dos.run_command("STEP")
    assert step0["registers"]["AX"] == 0x0900
    assert any("AX=" in ln for ln in dos.run_command("REGS")["output_lines"])

    telem = dos.simulate_boot_telemetry()
    assert telem["episode_count"] == 12
    assert all(abs(sum(ep.values()) - 1.0) < 1e-12 for ep in telem["episodes"])
    assert telem["chiasm_nexus"]["executed"] is False


def test_flight_sim_6dof_physics_and_presets():
    assert isa_density(3000.0) < isa_density(0.0)

    sim_a = FlightSim6DOF()
    sim_b = FlightSim6DOF()
    sim_a.reset_preset("cruise")
    sim_b.reset_preset("cruise")
    for _ in range(10):
        ha = sim_a.step(0.1, throttle=0.72, pitch_cmd=0.0, roll_cmd=0.0)
        hb = sim_b.step(0.1, throttle=0.72, pitch_cmd=0.0, roll_cmd=0.0)
    assert ha == hb
    assert 40.0 < ha["airspeed_kt"] < 160.0
    assert all(math.isfinite(float(v)) for v in ha.values() if isinstance(v, (int, float)))

    sim_a.reset_preset("climb")
    alt_start = sim_a.alt_m
    for _ in range(20):
        hc = sim_a.step(0.1, throttle=0.95, pitch_cmd=0.35, roll_cmd=0.0)
    assert sim_a.alt_m > alt_start
    assert hc["vsi_fpm"] > 0.0

    sim_a.reset_preset("turn30")
    for _ in range(15):
        ht = sim_a.step(0.1, throttle=0.78, pitch_cmd=0.05, roll_cmd=0.72)
    assert abs(ht["roll_deg"]) > 15.0
    assert abs(ht["turn_rate_dps"]) > 0.5

    sortie = sim_a.simulate_sortie()
    assert sortie["episode_count"] == 16
    assert all(abs(sum(ep.values()) - 1.0) < 1e-12 for ep in sortie["episodes"])

    # Hardening regression: huge dt clamped, non-finite dt rejected, heading_deg < 360.0
    sim_edge = FlightSim6DOF()
    sim_edge.reset_preset("cruise")
    h_big = sim_edge.step(1e8, throttle=0.72)
    assert all(math.isfinite(float(v)) for v in h_big.values() if isinstance(v, (int, float)))
    assert h_big["alt_m"] >= 0.0
    with pytest.raises(ValueError, match="finite"):
        sim_edge.step(float("inf"), throttle=0.72)
    with pytest.raises(ValueError, match="finite"):
        sim_edge.step(float("nan"), throttle=0.72)

    sim_edge.psi = math.radians(359.996)
    h_wrap = sim_edge.hud()
    assert 0.0 <= h_wrap["heading_deg"] < 360.0
    assert h_wrap["heading_deg"] == 0.0


def test_medical_sandbox_optics_and_non_clinical_flags():
    def _assert_non_clinical(payload: dict):
        assert payload["clinical_use"] is False
        assert payload["educational_simulation_only"] is True
        assert payload["clinical_certification_claimed"] is False
        assert payload["executed"] is False
        assert payload["sentience_claimed"] is False
        assert payload["tokens_used"] == 0
        assert isinstance(payload.get("disclaimer"), str) and len(payload["disclaimer"]) > 15

    # R peak occurs at phi = 0.40 -> t = 0.40 * (60/72) = 1/3 s
    r_peak = MedicalSandboxModel.ecg_pqrst(1.0 / 3.0, hr_bpm=72.0)
    baseline = MedicalSandboxModel.ecg_pqrst(0.0, hr_bpm=72.0)
    assert r_peak > 1.0 and r_peak > baseline
    _assert_non_clinical(MedicalSandboxModel.ecg_trace(hr_bpm=72.0))

    ox = MedicalSandboxModel.spo2_beer_lambert(0.60, t_sec=0.18, hr_bpm=72.0)
    _assert_non_clinical(ox)
    assert 70.0 <= ox["spo2_pct"] <= 100.0
    assert abs(ox["spo2_pct"] - (110.0 - 25.0 * 0.60)) < 1e-6

    cap = MedicalSandboxModel.capnography_trace(rr_bpm=14.0, etco2_mmhg=38.0)
    _assert_non_clinical(cap)
    assert 34.0 <= cap["peak_mmhg"] <= 39.0
    assert MedicalSandboxModel.capnography_waveform(0.0, rr_bpm=14.0) == 0.0

    pv = MedicalSandboxModel.ventilator_pv_loop(
        compliance_ml_cmh2o=50.0, resistance_cmh2o_l_s=8.0, vt_ml=480.0, peep_cmh2o=5.0
    )
    _assert_non_clinical(pv)
    pt = pv["points"][20]
    expected_p = 5.0 + (pt["volume_ml"] / 50.0) + (8.0 * pt["flow_l_s"])
    assert abs(pt["pressure_cmh2o"] - expected_p) < 0.01

    inf = MedicalSandboxModel.infusion_rate_calc(5.0, 70.0, 1000.0)
    _assert_non_clinical(inf)
    assert abs(inf["rate_ml_hr"] - 21.0) < 1e-6

    telem = MedicalSandboxModel.simulate_telemetry()
    _assert_non_clinical(telem)
    assert telem["episode_count"] == 16

    # Hardening regression: fs_hz=0 guarded, invalid/non-finite infusion inputs raise ValueError
    ecg_zero_fs = MedicalSandboxModel.ecg_trace(hr_bpm=72.0, duration_sec=1.0, fs_hz=0)
    _assert_non_clinical(ecg_zero_fs)
    assert ecg_zero_fs["fs_hz"] == 1
    assert len(ecg_zero_fs["lead_ii_mv"]) >= 16
    assert all(math.isfinite(v) for v in ecg_zero_fs["lead_ii_mv"])

    cap_zero_fs = MedicalSandboxModel.capnography_trace(rr_bpm=14.0, etco2_mmhg=38.0, duration_sec=2.0, fs_hz=0)
    _assert_non_clinical(cap_zero_fs)
    assert len(cap_zero_fs["co2_mmhg"]) >= 16
    assert all(math.isfinite(v) for v in cap_zero_fs["co2_mmhg"])

    with pytest.raises(ValueError):
        MedicalSandboxModel.ecg_trace(fs_hz=float("nan"))
    with pytest.raises(ValueError):
        MedicalSandboxModel.capnography_trace(duration_sec=float("inf"))
    with pytest.raises(ValueError):
        MedicalSandboxModel.infusion_rate_calc(5.0, 70.0, 0.0)
    with pytest.raises(ValueError):
        MedicalSandboxModel.infusion_rate_calc(5.0, 70.0, -10.0)
    with pytest.raises(ValueError):
        MedicalSandboxModel.infusion_rate_calc(5.0, 70.0, 1000.0, drop_factor_gtt_ml=0)
    with pytest.raises(ValueError):
        MedicalSandboxModel.infusion_rate_calc(float("nan"), 70.0, 1000.0)


def test_software_observatory_metrics_and_sha256_seal():
    # Exact boundary p == tau must be excluded (strict p > tau)
    dist = {"a": 0.50, "b": 0.25, "c": 0.15, "d": 0.10}
    res = SoftwareObservatoryModel.evaluate_repertoire(dist, tau=0.10)
    vec = [res["normalized"][k] for k in sorted(res["normalized"])]
    assert res["a_tau"] == a_tau(vec, 0.10) == 3
    assert abs(res["shannon_h1"] - shannon_h1(vec)) < 1e-5
    assert abs(res["renyi_h2"] - renyi_h2(vec)) < 1e-5
    assert abs(res["quartic_purity_m4"] - quartic_purity_m4(vec)) < 1e-5

    sealed = seal_chiasm_report({"slug": "unit", "value": 42})
    assert verify_report_sha256(sealed) is True
    assert SoftwareObservatoryModel.verify_chiasm_bundle(sealed)["valid"] is True

    tampered = dict(sealed)
    tampered["value"] = 43
    assert verify_report_sha256(tampered) is False
    assert SoftwareObservatoryModel.verify_chiasm_bundle(tampered)["valid"] is False

    matrix = SoftwareObservatoryModel.WIN7_MODERN_MATRIX
    assert len(matrix) >= 5
    joined = json.dumps(matrix)
    assert "ES5" in joined and "3.7" in joined


def test_r1_docs_artifacts_schemas_and_sha256_seals():
    for dir_name, slug in DOMAINS:
        ddir = DOCS / dir_name
        assert ddir.is_dir(), f"Missing directory {ddir}"
        required = [
            ddir / "index.html",
            ddir / "preview.png",
            ddir / "summary.json",
            ddir / "chiasm_report.json",
            ddir / f"{slug}_chiasm.svg",
            ddir / f"{slug}_plate.svg",
            ddir / f"{slug}_braille.txt",
            ddir / f"{slug}_braille.json",
            ddir / f"{slug}_braille_preview.png",
        ]
        for fpath in required:
            assert fpath.is_file(), f"Missing artifact {fpath}"
            assert fpath.stat().st_size < 52_428_800, f"File exceeds 50 MB: {fpath}"

        prev = ddir / "preview.png"
        assert prev.stat().st_size < 5_242_880
        with Image.open(prev) as im:
            assert im.size == (1600, 900)
            assert im.mode == "RGB"

        summary = json.loads((ddir / "summary.json").read_text(encoding="utf-8"))
        assert summary["contract"] == SUMMARY_CONTRACT
        assert summary["executed"] is False
        assert summary["sentience_claimed"] is False
        assert summary["tokens_used"] == 0

        report = json.loads((ddir / "chiasm_report.json").read_text(encoding="utf-8"))
        assert report["contract"] == CONTRACT
        assert report["executed"] is False
        assert report["sentience_claimed"] is False
        assert report["tokens_used"] == 0
        assert len(report["report_sha256"]) == 64
        assert report["report_sha256"] == canonical_sha256(report)
        assert verify_report_sha256(report) is True

        if dir_name == "medical-sim":
            for doc_obj in (summary, report):
                assert doc_obj["clinical_use"] is False
                assert doc_obj["educational_simulation_only"] is True
                assert doc_obj["clinical_certification_claimed"] is False
                assert "NOT FOR CLINICAL" in doc_obj["disclaimer"].upper()
            html_txt = (ddir / "index.html").read_text(encoding="utf-8")
            assert "NOT FOR CLINICAL" in html_txt.upper()
            plate_txt = (ddir / f"{slug}_plate.svg").read_text(encoding="utf-8")
            assert "NOT FOR CLINICAL" in plate_txt.upper()


def test_r1_svg_and_braille_validity():
    for dir_name, slug in DOMAINS:
        ddir = DOCS / dir_name
        for svg_name in (f"{slug}_chiasm.svg", f"{slug}_plate.svg"):
            root = ET.fromstring((ddir / svg_name).read_text(encoding="utf-8"))
            assert root.tag.endswith("svg")

        br_json = json.loads((ddir / f"{slug}_braille.json").read_text(encoding="utf-8"))
        lines = br_json["lines"]
        assert len(lines) >= 8
        widths = {len(row) for row in lines}
        assert len(widths) == 1 and next(iter(widths)) == br_json["cols"]
        assert all(0x2800 <= ord(ch) <= 0x28FF for row in lines for ch in row)
        assert any(ord(ch) > 0x2800 for row in lines for ch in row)

        br_txt = (ddir / f"{slug}_braille.txt").read_text(encoding="utf-8")
        assert any(0x2800 < ord(ch) <= 0x28FF for ch in br_txt)


def test_r1_zero_external_cdns_and_zero_gps_metadata():
    forbidden_re = re.compile(
        r'(<script[^>]+src=["\']https?://|<link[^>]+href=["\']https?://|'
        r'<img[^>]+src=["\']https?://|url\(["\']?https?://|@import\s+["\']?https?://|'
        r'unpkg\.com|jsdelivr\.net|googleapis\.com|gstatic\.com|cdnjs\.cloudflare\.com)',
        re.IGNORECASE,
    )
    pngs: list[Path] = []
    for dir_name, slug in DOMAINS:
        ddir = DOCS / dir_name
        for txt_file in (ddir / "index.html", ddir / f"{slug}_chiasm.svg", ddir / f"{slug}_plate.svg"):
            content = txt_file.read_text(encoding="utf-8")
            assert not forbidden_re.search(content), f"External CDN/resource URL found in {txt_file}"
        pngs.extend(sorted(ddir.glob("*.png")))

    for png in pngs:
        with Image.open(png) as im:
            exif = im.getexif()
            assert 0x8825 not in exif, f"GPSInfo EXIF tag present in {png}"

    if shutil.which("exiftool"):
        out = subprocess.check_output(["exiftool", "-j", "-GPS:all", *[str(p) for p in pngs]], text=True)
        meta = json.loads(out)
        for item in meta:
            gps_keys = [k for k in item.keys() if k != "SourceFile"]
            assert gps_keys == [], f"GPS metadata found by exiftool: {item}"


def test_r1_html_js_syntax_and_headless_runtime():
    node = shutil.which("node")
    for dir_name, _ in DOMAINS:
        html_txt = (DOCS / dir_name / "index.html").read_text(encoding="utf-8")
        scripts = re.findall(r"<script>(.*?)</script>", html_txt, flags=re.S)
        assert len(scripts) == 1
        if node:
            proc = subprocess.run([node, "--check", "-"], input=scripts[0], text=True, capture_output=True)
            assert proc.returncode == 0, f"JS syntax error in {dir_name}: {proc.stderr}"

    sec_site = "/home/cowboy/security-tools/lib/python3.14/site-packages"
    if Path(sec_site).is_dir() and sec_site not in sys.path:
        sys.path.insert(0, sec_site)
    playwright_mod = pytest.importorskip("playwright.sync_api")
    chrome_path = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome_path:
        pytest.skip("No Chrome/Chromium binary available for headless Playwright verification.")

    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_range_handler(DOCS))
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        with playwright_mod.sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=chrome_path, headless=True, args=["--no-sandbox"])
            try:
                for dir_name, _ in DOMAINS:
                    page = browser.new_page()
                    errors: list[str] = []
                    page.on("pageerror", lambda err: errors.append(str(err)))
                    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

                    page.goto(f"http://127.0.0.1:{port}/{dir_name}/index.html", wait_until="load")

                    if dir_name == "msdos":
                        page.click("button[data-cmd='DIR']")
                        page.click("button[data-cmd='STEP']")
                        term_txt = page.inner_text("#dosTerm")
                        assert "FIELDGLS.TXT" in term_txt
                        assert "STEP #0" in term_txt
                        # Step #1 (MOV DX,0140h), #2 (INT 21h), #3 (ADD AX,002Ah -> AX=094Eh, PF=1)
                        for _ in range(3):
                            page.click("#stepBtn")
                        flags_txt = page.inner_text("#flagsReadout")
                        assert "PF=1" in flags_txt
                        assert "CF=0" in flags_txt and "ZF=0" in flags_txt and "SF=0" in flags_txt
                    elif dir_name == "flight-sim":
                        page.click("button[data-preset='climb']")
                        page.click("#stepFlightBtn")
                        assert page.inner_text("#flightPhaseBadge") == "CLIMB"
                        # Exercise high-alpha stall regime cleanly without NaN/errors
                        page.fill("#thrSlider", "0")
                        page.dispatch_event("#thrSlider", "input")
                        page.fill("#pitSlider", "100")
                        page.dispatch_event("#pitSlider", "input")
                        page.click("#stepFlightBtn")
                        assert "NaN" not in page.inner_text("#sixPackGrid")
                    elif dir_name == "medical-sim":
                        page.fill("#infDose", "10")
                        page.dispatch_event("#infDose", "input")
                        assert "42.00 mL/hr" in page.inner_text("#infOut")
                        # Hardening regression: 0 or negative concentration shows validation error, not 21000/21B
                        page.fill("#infConc", "0")
                        page.dispatch_event("#infConc", "input")
                        out_zero = page.inner_text("#infOut")
                        assert "Concentration must be > 0" in out_zero
                        assert "21000.00" not in out_zero
                        page.fill("#infConc", "-5")
                        page.dispatch_event("#infConc", "input")
                        assert "Concentration must be > 0" in page.inner_text("#infOut")
                    elif dir_name == "software":
                        page.click("#verifyShaBtn")
                        assert "SHA-256 VERIFIED" in page.inner_text("#shaBadge")
                        page.fill("#tauSlider", "20")
                        page.dispatch_event("#tauSlider", "input")
                        assert "0.20" in page.inner_text("#tauReadout")
                        assert "JSON.parse" in page.inner_text("body")

                    assert errors == [], f"Runtime errors on {dir_name}: {errors}"
                    page.close()
            finally:
                browser.close()
    finally:
        srv.shutdown()
        srv.server_close()
