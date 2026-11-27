"""Tier 2: Boundary, compatibility, media/size, non-clinical, and negative-input tests."""

from __future__ import annotations

from pathlib import Path
import subprocess
import urllib.error
import urllib.request
import zipfile

import pytest

from fieldglass.metrics import (
    TONAL_STATES,
    a_tau,
    causal_chiasm,
    luminance_to_8state,
    normalize_dist,
    persistent_filtration_tomography,
)
from fieldglass.showcase import make_range_handler
from validators import (
    MAX_DOCS_BYTES,
    extract_html_scripts_and_local_js,
    launch_loopback_http_script,
    validate_chiasm_invariants,
    validate_es5_win7_html,
    validate_exiftool_no_gps,
    validate_file_size_under_50mb,
    validate_html_document,
    validate_js_execution_node,
    validate_nonclinical_framing,
    validate_pptx_deck,
    validate_py37_win7_script,
    validate_svg_document,
)

pytestmark = pytest.mark.tier2

MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".avi", ".mkv"}
R1_SLUGS = ("msdos", "flight-sim", "medical-sim", "software")
R2_SLUGS = ("chatgpt", "anthropic", "grok", "spacex", "claire-grimes")
NEW_MODULE_GROUPS = (
    "msdos",
    "flight-sim",
    "medical-sim",
    "software",
    "improvements",
    "zoe-hospital",
)


# ---------------------------------------------------------------------------
# 1. File Size < 50 MB Gate (F1-F8 / R5)
# ---------------------------------------------------------------------------
def test_tier2_all_docs_files_strictly_under_50mb(docs_root: Path) -> None:
    assert docs_root.is_dir(), f"Missing docs directory: {docs_root}"
    all_files = sorted(p for p in docs_root.rglob("*") if p.is_file())
    assert len(all_files) > 0, "docs/ contains no files"
    for fpath in all_files:
        validate_file_size_under_50mb(fpath, limit_bytes=MAX_DOCS_BYTES)


def test_tier2_root_pptx_strictly_under_50mb(obs_root: Path) -> None:
    validate_file_size_under_50mb(obs_root / "Fieldglass_Observatory_Expansion.pptx", limit_bytes=MAX_DOCS_BYTES)


# ---------------------------------------------------------------------------
# 2. Zero GPS / Location Metadata via exiftool (F1-F8 / R5)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("group", NEW_MODULE_GROUPS)
def test_tier2_module_media_zero_gps_exiftool(docs_root: Path, group: str) -> None:
    gdir = docs_root / group
    assert gdir.is_dir(), f"Missing module group directory: {gdir}"
    media = sorted(p for p in gdir.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTS)
    assert media, f"Expected at least 1 media file under {gdir}"
    validate_exiftool_no_gps(media)


def test_tier2_all_docs_media_zero_gps_exiftool(docs_root: Path) -> None:
    media = sorted(p for p in docs_root.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTS)
    assert media, "Expected media files under docs/"
    validate_exiftool_no_gps(media)


def test_tier2_pptx_embedded_media_zero_gps_exiftool(obs_root: Path, docs_root: Path, tmp_path: Path) -> None:
    for pptx_p in (
        docs_root / "Fieldglass_Observatory_Expansion.pptx",
        obs_root / "Fieldglass_Observatory_Expansion.pptx",
    ):
        validate_exiftool_no_gps([pptx_p], pptx_extract_dir=tmp_path)


# ---------------------------------------------------------------------------
# 3. Zero External CDN / Network Dependencies (F1-F6, F8)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("group", NEW_MODULE_GROUPS)
def test_tier2_module_html_and_svg_zero_external_cdn(docs_root: Path, group: str) -> None:
    gdir = docs_root / group
    assert gdir.is_dir(), f"Missing module group directory: {gdir}"
    htmls = sorted(p for p in gdir.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".htm", ".hta"})
    assert htmls, f"Expected HTML/HTA files under {gdir}"
    for hp in htmls:
        validate_html_document(hp, min_visible_chars=60, forbid_external_anchors=(group == "zoe-hospital"))
    for svg in sorted(gdir.rglob("*.svg")):
        validate_svg_document(svg)


def test_tier2_docs_index_html_zero_external_cdn_assets(docs_root: Path) -> None:
    validate_html_document(docs_root / "index.html", min_visible_chars=300, forbid_external_anchors=False)


# ---------------------------------------------------------------------------
# 4. Causal Chiasm Invariants & Boundary Validation (F1-F6)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("slug", R1_SLUGS)
def test_tier2_r1_json_reports_chiasm_invariants(docs_root: Path, slug: str) -> None:
    mdir = docs_root / slug
    reports = sorted(mdir.rglob("*chiasm*report*.json"))
    assert reports, f"Missing chiasm report in {mdir}"
    for rp in reports:
        validate_chiasm_invariants(rp, require_contract=True, require_sha256=True)
    validate_chiasm_invariants(mdir / "summary.json", require_contract=False, require_sha256=False)


@pytest.mark.parametrize("subject", R2_SLUGS)
def test_tier2_r2_subject_json_chiasm_invariants(docs_root: Path, subject: str) -> None:
    sdir = docs_root / "improvements" / subject
    assert sdir.is_dir(), f"Missing R2 subject directory: {sdir}"
    summary_p = sdir / "summary.json"
    assert summary_p.is_file(), f"Missing summary.json in {sdir}"
    validated_reports: list[Path] = [summary_p]
    validate_chiasm_invariants(summary_p, require_contract=False, require_sha256=False)
    for rp in sorted(sdir.rglob("*chiasm*report*.json")):
        validate_chiasm_invariants(rp, require_contract=True, require_sha256=True)
        validated_reports.append(rp)
    assert len(validated_reports) >= 1, f"No JSON chiasm reports validated in {sdir}"


def test_tier2_r3_zoe_hospital_json_chiasm_invariants(docs_root: Path) -> None:
    zh = docs_root / "zoe-hospital"
    validate_chiasm_invariants(zh / "chiasm_report.json", require_contract=True, require_sha256=True)
    validate_chiasm_invariants(zh / "manifest.json", require_contract=False, require_sha256=False)
    validate_chiasm_invariants(zh / "summary.json", require_contract=False, require_sha256=False)


# ---------------------------------------------------------------------------
# 5. Strict Non-Clinical Framing Gate (F3, F6, F7)
# ---------------------------------------------------------------------------
def test_tier2_medical_sim_all_artifacts_strictly_nonclinical(docs_root: Path) -> None:
    mdir = docs_root / "medical-sim"
    assert mdir.is_dir(), f"Missing medical-sim directory: {mdir}"
    json_files = sorted(mdir.rglob("*.json"))
    assert json_files, f"Expected JSON artifacts under {mdir}"
    for jp in json_files:
        if jp.name in {"summary.json", "manifest.json"} or "chiasm" in jp.name.lower():
            validate_nonclinical_framing(data_or_path=jp)
        else:
            validate_nonclinical_framing(text=jp.read_text(encoding="utf-8"), label=str(jp))
    html_files = sorted(mdir.rglob("*.html"))
    assert html_files, f"Expected HTML artifacts under {mdir}"
    for hp in html_files:
        assets = validate_html_document(hp, min_visible_chars=100)
        validate_nonclinical_framing(text=assets.visible_text, label=str(hp))


def test_tier2_zoe_hospital_all_artifacts_strictly_nonclinical(docs_root: Path) -> None:
    zh = docs_root / "zoe-hospital"
    assert zh.is_dir(), f"Missing zoe-hospital directory: {zh}"
    json_files = sorted(zh.rglob("*.json"))
    assert json_files, f"Expected JSON artifacts under {zh}"
    for jp in json_files:
        if jp.name in {"summary.json", "manifest.json"} or "chiasm" in jp.name.lower():
            validate_nonclinical_framing(data_or_path=jp)
        else:
            validate_nonclinical_framing(text=jp.read_text(encoding="utf-8"), label=str(jp))
    html_files = sorted(p for p in zh.rglob("*") if p.suffix.lower() in {".html", ".hta"})
    assert html_files, f"Expected HTML/HTA artifacts under {zh}"
    for hp in html_files:
        assets = validate_html_document(hp, min_visible_chars=80, forbid_external_anchors=True)
        validate_nonclinical_framing(text=assets.visible_text, label=str(hp))


def test_tier2_pptx_strictly_nonclinical_framing(docs_root: Path) -> None:
    info = validate_pptx_deck(docs_root / "Fieldglass_Observatory_Expansion.pptx", min_slides=8)
    validate_nonclinical_framing(text=info["full_text"], label="Fieldglass_Observatory_Expansion.pptx")


# ---------------------------------------------------------------------------
# 6. Windows 7-Era Compatibility Gate (F6)
# ---------------------------------------------------------------------------
def test_tier2_zoe_hospital_win7_python_ast_ansi_loopback(docs_root: Path) -> None:
    py_path = docs_root / "zoe-hospital" / "zoe_hospital_win7.py"
    validate_py37_win7_script(py_path, require_loopback=True)


@pytest.mark.parametrize("fname", ("index.html", "zoe_hospital_kiosk.html", "zoe_hospital_kiosk.hta"))
def test_tier2_zoe_hospital_es5_and_ie_safe_css(docs_root: Path, fname: str) -> None:
    validate_es5_win7_html(docs_root / "zoe-hospital" / fname, require_script=(fname != "index.html"))


def test_tier2_zoe_hospital_launch_bat_win7_hygiene(docs_root: Path) -> None:
    bat_path = docs_root / "zoe-hospital" / "launch_win7.bat"
    raw = bat_path.read_bytes()
    assert b"\x1b" not in raw and b"\x9b" not in raw, "ANSI escape bytes forbidden in launch_win7.bat"
    txt = raw.decode("utf-8", errors="strict")
    assert "zoe_hospital_win7.py" in txt or "zoe_hospital_kiosk.hta" in txt
    assert "/tmp/" not in txt and "rm -rf" not in txt and "sudo " not in txt


# ---------------------------------------------------------------------------
# 7. Negative & Boundary Input Tests (F1-F4, F6, F7, F8)
# ---------------------------------------------------------------------------
def test_tier2_zoe_hospital_server_rejects_traversal_and_unknown_routes(docs_root: Path) -> None:
    py_path = docs_root / "zoe-hospital" / "zoe_hospital_win7.py"
    proc, base_url, out_lines = launch_loopback_http_script(py_path, timeout_sec=10.0)
    try:
        for bad_path in ("/../../../etc/passwd", "/..%2f..%2fetc/passwd", "/nonexistent_route_404_check"):
            try:
                with urllib.request.urlopen(base_url + bad_path, timeout=2.0) as resp:
                    raise AssertionError(f"Expected 403/404 for {bad_path}, got HTTP {resp.status}")
            except urllib.error.HTTPError as herr:
                assert herr.code in (400, 403, 404), f"Unexpected HTTP {herr.code} for {bad_path}"
                body = herr.read().decode("utf-8", errors="replace")
                assert "root:x:0:0" not in body
    finally:
        proc.terminate()
        try:
            rem_out, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            rem_out, stderr = proc.communicate(timeout=5)
        full_stdout = "".join(out_lines) + (rem_out or "")
        assert "Traceback" not in stderr, f"Unexpected traceback on stderr: {stderr}"
        assert "\x1b" not in full_stdout and "\x1b" not in stderr


def test_tier2_r1_simulators_js_boundary_execution(docs_root: Path) -> None:
    for slug in R1_SLUGS:
        scripts = extract_html_scripts_and_local_js(docs_root / slug / "index.html")
        validate_js_execution_node(
            scripts,
            post_eval_js="if (typeof document.body.click === 'function') document.body.click();",
            label=f"tier2-boundary:{slug}",
        )


def test_tier2_pptx_zip_integrity_and_nonzero_media(docs_root: Path) -> None:
    pptx_p = docs_root / "Fieldglass_Observatory_Expansion.pptx"
    validate_pptx_deck(pptx_p, min_slides=8)
    with zipfile.ZipFile(pptx_p, "r") as zf:
        infos = zf.infolist()
        names = {i.filename for i in infos}
        assert "[Content_Types].xml" in names
        media_entries = [i for i in infos if i.filename.startswith("ppt/media/") and not i.is_dir()]
        assert media_entries, "Expected embedded ppt/media/* assets inside .pptx"
        for entry in media_entries:
            assert entry.file_size > 0, f"Zero-byte embedded media in PPTX: {entry.filename}"


def test_tier2_fieldglass_metrics_boundary_invariants() -> None:
    assert a_tau([0.5, 0.25, 0.25], 0.25) == 1
    assert a_tau([0.5, 0.25, 0.25], 0.50) == 0
    with pytest.raises(ValueError):
        normalize_dist({})
    with pytest.raises(ValueError):
        luminance_to_8state([1.0] * 10)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        persistent_filtration_tomography([])
    dist = {s: 1.0 for s in TONAL_STATES}
    ch = causal_chiasm(dist, dist, tau=0.10)
    assert ch["executed"] is False and ch["sentience_claimed"] is False


def test_tier2_showcase_range_handler_invalid_range_returns_416(tmp_path: Path) -> None:
    from http.server import ThreadingHTTPServer
    import threading

    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"ABCD" * 10)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_range_handler(tmp_path))
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/sample.bin", headers={"Range": "bytes=999-1200"})
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=3)
        assert exc_info.value.code == 416
    finally:
        srv.shutdown()
        srv.server_close()
