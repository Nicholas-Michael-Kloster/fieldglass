"""Tier 1: Opaque-box feature coverage tests (>= 5 per major feature area R1-R5)."""

from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

from PIL import Image
import pytest

from validators import (
    extract_html_scripts_and_local_js,
    validate_chiasm_invariants,
    validate_html_document,
    validate_js_execution_node,
    validate_nonclinical_framing,
    validate_pptx_deck,
    validate_relative_links_in_html,
    validate_svg_document,
)

pytestmark = pytest.mark.tier1

R1_MODULES = {
    "msdos": ("ms-dos", "8086", "640", "fat", "command.com", "dos"),
    "flight-sim": ("flight", "pitch", "roll", "yaw", "airspeed", "altitude", "hud"),
    "medical-sim": ("ecg", "spo2", "ventilator", "capnography", "infusion", "simulat"),
    "software": ("fieldglass", "chiasm", "filtration", "software", "a_tau", "observatory"),
}

R2_SUBJECTS = {
    "chatgpt": ("chatgpt", "openai"),
    "anthropic": ("anthropic", "claude"),
    "grok": ("grok", "xai"),
    "spacex": ("spacex", "starship", "falcon", "telemetry"),
    "claire-grimes": ("claire", "grimes"),
}


def _discover_preview_pngs(mod_dir: Path) -> list[Path]:
    return sorted({p for p in mod_dir.rglob("*preview*.png") if p.is_file()})


def _discover_chiasm_reports(mod_dir: Path) -> list[Path]:
    return sorted({p for p in mod_dir.rglob("*chiasm*report*.json") if p.is_file()})


# ---------------------------------------------------------------------------
# F1: MS-DOS Educational Simulator (5 tests)
# ---------------------------------------------------------------------------
def test_f1_msdos_index_html_valid_and_domain_content(docs_root: Path) -> None:
    assets = validate_html_document(docs_root / "msdos" / "index.html", min_visible_chars=120)
    low = assets.visible_text.lower()
    assert any(kw in low for kw in R1_MODULES["msdos"]), "MS-DOS page missing domain concepts"


def test_f1_msdos_summary_json_valid(docs_root: Path) -> None:
    summary = docs_root / "msdos" / "summary.json"
    data = validate_chiasm_invariants(summary, require_contract=False, require_sha256=False)
    assert any(k in data for k in ("title", "name", "slug", "topic")), "summary.json missing identity keys"


def test_f1_msdos_chiasm_report_valid(docs_root: Path) -> None:
    reports = _discover_chiasm_reports(docs_root / "msdos")
    assert reports, "Expected chiasm report JSON in docs/msdos/"
    for rep in reports:
        validate_chiasm_invariants(rep, require_contract=True, require_sha256=True)


def test_f1_msdos_visual_assets_valid(docs_root: Path) -> None:
    mod_dir = docs_root / "msdos"
    pngs = _discover_preview_pngs(mod_dir)
    assert pngs, "Expected preview PNG in docs/msdos/"
    for p in pngs:
        with Image.open(p) as im:
            assert im.width >= 64 and im.height >= 64, f"Too small preview PNG: {p}"
    for svg in sorted(mod_dir.rglob("*.svg")):
        validate_svg_document(svg)


def test_f1_msdos_interactive_js_executes(docs_root: Path) -> None:
    scripts = extract_html_scripts_and_local_js(docs_root / "msdos" / "index.html")
    validate_js_execution_node(scripts, label="docs/msdos/index.html")


# ---------------------------------------------------------------------------
# F2: Flight Simulator & Telemetry HUD (5 tests)
# ---------------------------------------------------------------------------
def test_f2_flight_sim_index_html_valid_and_domain_content(docs_root: Path) -> None:
    assets = validate_html_document(docs_root / "flight-sim" / "index.html", min_visible_chars=120)
    low = assets.visible_text.lower()
    assert sum(1 for kw in R1_MODULES["flight-sim"] if kw in low) >= 2, "Flight-sim missing domain terms"


def test_f2_flight_sim_summary_json_valid(docs_root: Path) -> None:
    summary = docs_root / "flight-sim" / "summary.json"
    data = validate_chiasm_invariants(summary, require_contract=False, require_sha256=False)
    assert any(k in data for k in ("title", "name", "slug", "topic")), "summary.json missing identity keys"


def test_f2_flight_sim_chiasm_report_valid(docs_root: Path) -> None:
    reports = _discover_chiasm_reports(docs_root / "flight-sim")
    assert reports, "Expected chiasm report JSON in docs/flight-sim/"
    for rep in reports:
        validate_chiasm_invariants(rep, require_contract=True, require_sha256=True)


def test_f2_flight_sim_visual_assets_valid(docs_root: Path) -> None:
    mod_dir = docs_root / "flight-sim"
    pngs = _discover_preview_pngs(mod_dir)
    assert pngs, "Expected preview PNG in docs/flight-sim/"
    for p in pngs:
        with Image.open(p) as im:
            assert im.width >= 64 and im.height >= 64, f"Too small preview PNG: {p}"
    for svg in sorted(mod_dir.rglob("*.svg")):
        validate_svg_document(svg)


def test_f2_flight_sim_interactive_js_executes(docs_root: Path) -> None:
    scripts = extract_html_scripts_and_local_js(docs_root / "flight-sim" / "index.html")
    validate_js_execution_node(scripts, label="docs/flight-sim/index.html")


# ---------------------------------------------------------------------------
# F3: Simulated Medical Equipment Sandbox (5 tests)
# ---------------------------------------------------------------------------
def test_f3_medical_sim_index_html_valid_and_nonclinical(docs_root: Path) -> None:
    html_path = docs_root / "medical-sim" / "index.html"
    assets = validate_html_document(html_path, min_visible_chars=120)
    validate_nonclinical_framing(text=assets.visible_text, label=str(html_path))
    low = assets.visible_text.lower()
    assert sum(1 for kw in R1_MODULES["medical-sim"] if kw in low) >= 2, "Medical-sim missing equipment terms"


def test_f3_medical_sim_summary_json_nonclinical(docs_root: Path) -> None:
    summary = docs_root / "medical-sim" / "summary.json"
    validate_chiasm_invariants(summary, require_contract=False, require_sha256=False)
    validate_nonclinical_framing(data_or_path=summary)


def test_f3_medical_sim_chiasm_report_valid_and_nonclinical(docs_root: Path) -> None:
    reports = _discover_chiasm_reports(docs_root / "medical-sim")
    assert reports, "Expected chiasm report JSON in docs/medical-sim/"
    for rep in reports:
        validate_chiasm_invariants(rep, require_contract=True, require_sha256=True)
        validate_nonclinical_framing(data_or_path=rep)


def test_f3_medical_sim_visual_assets_valid(docs_root: Path) -> None:
    mod_dir = docs_root / "medical-sim"
    pngs = _discover_preview_pngs(mod_dir)
    assert pngs, "Expected preview PNG in docs/medical-sim/"
    for p in pngs:
        with Image.open(p) as im:
            assert im.width >= 64 and im.height >= 64, f"Too small preview PNG: {p}"
    for svg in sorted(mod_dir.rglob("*.svg")):
        validate_svg_document(svg)


def test_f3_medical_sim_interactive_js_executes(docs_root: Path) -> None:
    scripts = extract_html_scripts_and_local_js(docs_root / "medical-sim" / "index.html")
    validate_js_execution_node(scripts, label="docs/medical-sim/index.html")


# ---------------------------------------------------------------------------
# F4: Software Systems Observatory (5 tests)
# ---------------------------------------------------------------------------
def test_f4_software_index_html_valid_and_domain_content(docs_root: Path) -> None:
    assets = validate_html_document(docs_root / "software" / "index.html", min_visible_chars=120)
    low = assets.visible_text.lower()
    assert sum(1 for kw in R1_MODULES["software"] if kw in low) >= 2, "Software page missing domain terms"


def test_f4_software_summary_json_valid(docs_root: Path) -> None:
    summary = docs_root / "software" / "summary.json"
    data = validate_chiasm_invariants(summary, require_contract=False, require_sha256=False)
    assert any(k in data for k in ("title", "name", "slug", "topic")), "summary.json missing identity keys"


def test_f4_software_chiasm_report_valid(docs_root: Path) -> None:
    reports = _discover_chiasm_reports(docs_root / "software")
    assert reports, "Expected chiasm report JSON in docs/software/"
    for rep in reports:
        validate_chiasm_invariants(rep, require_contract=True, require_sha256=True)


def test_f4_software_visual_assets_valid(docs_root: Path) -> None:
    mod_dir = docs_root / "software"
    pngs = _discover_preview_pngs(mod_dir)
    assert pngs, "Expected preview PNG in docs/software/"
    for p in pngs:
        with Image.open(p) as im:
            assert im.width >= 64 and im.height >= 64, f"Too small preview PNG: {p}"
    for svg in sorted(mod_dir.rglob("*.svg")):
        validate_svg_document(svg)


def test_f4_software_interactive_js_executes(docs_root: Path) -> None:
    scripts = extract_html_scripts_and_local_js(docs_root / "software" / "index.html")
    validate_js_execution_node(scripts, label="docs/software/index.html")


# ---------------------------------------------------------------------------
# F5: R2 Five Improvement Dossiers (1 hub + 5 tests * 5 subjects = 26 tests)
# ---------------------------------------------------------------------------
def test_f5_improvements_hub_index_valid_and_links_all_subjects(docs_root: Path) -> None:
    hub = docs_root / "improvements" / "index.html"
    assets = validate_html_document(hub, min_visible_chars=120)
    joined_hrefs = " ".join(assets.a_hrefs).lower()
    for subject in R2_SUBJECTS:
        assert subject in joined_hrefs, f"docs/improvements/index.html missing link to {subject!r}"
    validate_relative_links_in_html(hub, docs_root=docs_root)


@pytest.mark.parametrize("subject", sorted(R2_SUBJECTS))
def test_f5_subject_index_html_valid(docs_root: Path, subject: str) -> None:
    html_path = docs_root / "improvements" / subject / "index.html"
    assets = validate_html_document(html_path, min_visible_chars=180)
    low = assets.visible_text.lower()
    assert any(kw in low for kw in R2_SUBJECTS[subject]), f"{html_path} missing subject name {subject}"


@pytest.mark.parametrize("subject", sorted(R2_SUBJECTS))
def test_f5_subject_structured_improvements_present(docs_root: Path, subject: str) -> None:
    subj_dir = docs_root / "improvements" / subject
    html_raw = (subj_dir / "index.html").read_text(encoding="utf-8")
    assets = validate_html_document(subj_dir / "index.html", min_visible_chars=180)
    # Concrete structured proposals: headings/list items/cards plus improvement terminology
    structural_markers = len(re.findall(r"<(?:h[2-4]|li|tr|article|section)\b", html_raw, re.I))
    assert structural_markers >= 4, f"{subj_dir}: expected structured HTML sections/items (>=4), got {structural_markers}"
    assert re.search(r"\b(?:improv\w*|recommend\w*|proposal\w*|architect\w*|telemetry|metric)\b", assets.visible_text, re.I)


@pytest.mark.parametrize("subject", sorted(R2_SUBJECTS))
def test_f5_subject_summary_json_valid(docs_root: Path, subject: str) -> None:
    summary = docs_root / "improvements" / subject / "summary.json"
    data = validate_chiasm_invariants(summary, require_contract=False, require_sha256=False)
    assert any(k in data for k in ("title", "subject", "name", "slug", "improvements"))


@pytest.mark.parametrize("subject", sorted(R2_SUBJECTS))
def test_f5_subject_visual_assets_and_chiasm(docs_root: Path, subject: str) -> None:
    subj_dir = docs_root / "improvements" / subject
    pngs = _discover_preview_pngs(subj_dir)
    assert pngs, f"Expected preview PNG in {subj_dir}"
    for p in pngs:
        with Image.open(p) as im:
            assert im.width >= 64 and im.height >= 64, f"Too small preview PNG: {p}"
    for svg in sorted(subj_dir.rglob("*.svg")):
        validate_svg_document(svg)
    for rep in _discover_chiasm_reports(subj_dir):
        validate_chiasm_invariants(rep, require_contract=True, require_sha256=True)


@pytest.mark.parametrize("subject", sorted(R2_SUBJECTS))
def test_f5_subject_relative_links_resolve(docs_root: Path, subject: str) -> None:
    validate_relative_links_in_html(docs_root / "improvements" / subject / "index.html", docs_root=docs_root)


# ---------------------------------------------------------------------------
# F6: Zoe Hospital Edition — Windows 7-Era Non-Clinical (6 tests)
# ---------------------------------------------------------------------------
def test_f6_zoe_hospital_html_pages_valid_and_nonclinical(docs_root: Path) -> None:
    for fname in ("index.html", "zoe_hospital_kiosk.html"):
        p = docs_root / "zoe-hospital" / fname
        assets = validate_html_document(p, min_visible_chars=120, forbid_external_anchors=True)
        validate_nonclinical_framing(text=assets.visible_text, label=str(p))
        low = assets.visible_text.lower()
        assert "zoe" in low and ("hospital" in low or "windows 7" in low)


def test_f6_zoe_hospital_hta_valid_and_nonclinical(docs_root: Path) -> None:
    hta = docs_root / "zoe-hospital" / "zoe_hospital_kiosk.hta"
    assets = validate_html_document(hta, min_visible_chars=100, forbid_external_anchors=True)
    raw_low = hta.read_text(encoding="utf-8").lower()
    assert "<hta:application" in raw_low, "zoe_hospital_kiosk.hta missing <HTA:APPLICATION> declaration"
    validate_nonclinical_framing(text=assets.visible_text, label=str(hta))


def test_f6_zoe_hospital_win7_python_server_present(docs_root: Path) -> None:
    py_path = docs_root / "zoe-hospital" / "zoe_hospital_win7.py"
    assert py_path.is_file(), f"Missing {py_path}"
    src = py_path.read_text(encoding="utf-8")
    assert len(src.strip()) >= 200
    assert "127.0.0.1" in src
    validate_nonclinical_framing(text=src, label=str(py_path))


def test_f6_zoe_hospital_bat_and_zip_bundle_present(docs_root: Path) -> None:
    zh_dir = docs_root / "zoe-hospital"
    bat = zh_dir / "launch_win7.bat"
    zip_p = zh_dir / "zoe_hospital_win7_bundle.zip"
    assert bat.is_file() and bat.stat().st_size > 20
    assert zip_p.is_file() and zip_p.stat().st_size > 100
    with zipfile.ZipFile(zip_p, "r") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
    assert len(names) >= 3, f"Expected >= 3 files inside {zip_p}, got {names}"


def test_f6_zoe_hospital_json_reports_valid_and_nonclinical(docs_root: Path) -> None:
    zh_dir = docs_root / "zoe-hospital"
    for fname, req_sha in (("manifest.json", False), ("summary.json", False), ("chiasm_report.json", True)):
        p = zh_dir / fname
        validate_chiasm_invariants(p, require_contract=req_sha, require_sha256=req_sha)
        validate_nonclinical_framing(data_or_path=p)


def test_f6_zoe_hospital_preview_image_valid(docs_root: Path) -> None:
    pngs = _discover_preview_pngs(docs_root / "zoe-hospital")
    assert pngs, "Expected preview PNG in docs/zoe-hospital/"
    for p in pngs:
        with Image.open(p) as im:
            assert im.width >= 64 and im.height >= 64


# ---------------------------------------------------------------------------
# F7: PowerPoint Presentation (.pptx) (5 tests)
# ---------------------------------------------------------------------------
def test_f7_pptx_files_exist_and_open_cleanly(obs_root: Path, docs_root: Path) -> None:
    for pptx_p in (
        docs_root / "Fieldglass_Observatory_Expansion.pptx",
        obs_root / "Fieldglass_Observatory_Expansion.pptx",
    ):
        info = validate_pptx_deck(pptx_p, min_slides=8)
        assert info["slide_count"] >= 8


def test_f7_pptx_widescreen_16_9_geometry(obs_root: Path, docs_root: Path) -> None:
    for pptx_p in (
        docs_root / "Fieldglass_Observatory_Expansion.pptx",
        obs_root / "Fieldglass_Observatory_Expansion.pptx",
    ):
        info = validate_pptx_deck(pptx_p, min_slides=1)
        assert info["width"] > info["height"]


def test_f7_pptx_covers_all_r1_topics(docs_root: Path) -> None:
    info = validate_pptx_deck(
        docs_root / "Fieldglass_Observatory_Expansion.pptx",
        required_topics=("MS-DOS", "Flight", "Medical", "Software"),
    )
    assert info["slide_count"] >= 8


def test_f7_pptx_covers_all_r2_subjects(docs_root: Path) -> None:
    info = validate_pptx_deck(
        docs_root / "Fieldglass_Observatory_Expansion.pptx",
        required_topics=("ChatGPT", "Anthropic", "Grok", "SpaceX"),
    )
    low = info["full_text"].lower()
    assert "claire" in low or "grimes" in low, "PPTX missing R2 subject Claire / Grimes"


def test_f7_pptx_covers_r3_zoe_hospital_and_nonclinical(docs_root: Path) -> None:
    info = validate_pptx_deck(
        docs_root / "Fieldglass_Observatory_Expansion.pptx",
        required_topics=("Zoe", "Hospital", "Windows 7"),
    )
    validate_nonclinical_framing(text=info["full_text"], label="Fieldglass_Observatory_Expansion.pptx")


# ---------------------------------------------------------------------------
# F8: Observatory & Repository Integration (5 tests)
# ---------------------------------------------------------------------------
def test_f8_docs_index_links_all_new_deliverables(docs_root: Path) -> None:
    index_p = docs_root / "index.html"
    assets = validate_html_document(index_p, min_visible_chars=300)
    hrefs_joined = " ".join(assets.a_hrefs + [v for _, _, v in assets.media_urls]).lower()
    for expected in (
        "msdos",
        "flight-sim",
        "medical-sim",
        "software",
        "improvements",
        "zoe-hospital",
        "fieldglass_observatory_expansion.pptx",
    ):
        assert expected in hrefs_joined, f"docs/index.html missing link reference to {expected!r}"


def test_f8_readme_references_expansion_and_pptx(obs_root: Path) -> None:
    readme = obs_root / "README.md"
    assert readme.is_file()
    txt = readme.read_text(encoding="utf-8")
    low = txt.lower()
    for token in ("ms-dos", "flight", "medical", "software", "chatgpt", "anthropic", "grok", "spacex", "zoe", "fieldglass_observatory_expansion.pptx"):
        assert token in low, f"README.md missing reference to {token!r}"


def test_f8_core_fieldglass_modules_importable() -> None:
    import fieldglass
    import fieldglass.cli
    import fieldglass.metrics
    import fieldglass.overlay
    import fieldglass.plate
    import fieldglass.showcase

    assert hasattr(fieldglass.metrics, "a_tau")
    assert hasattr(fieldglass.showcase, "make_range_handler")
    assert hasattr(fieldglass.cli, "build_parser")


def test_f8_builder_scripts_exist_and_parse(obs_root: Path) -> None:
    examples = obs_root / "examples"
    builders = sorted(examples.glob("build_*.py"))
    assert len(builders) >= 4, f"Expected deterministic build scripts under {examples}, found {builders}"
    for b in builders:
        compile(b.read_text(encoding="utf-8"), str(b), "exec")


def test_f8_every_new_module_has_required_contract_files(docs_root: Path) -> None:
    module_dirs = [
        docs_root / "msdos",
        docs_root / "flight-sim",
        docs_root / "medical-sim",
        docs_root / "software",
        *(docs_root / "improvements" / s for s in R2_SUBJECTS),
        docs_root / "zoe-hospital",
    ]
    for mdir in module_dirs:
        assert (mdir / "index.html").is_file(), f"Missing index.html in {mdir}"
        assert (mdir / "summary.json").is_file(), f"Missing summary.json in {mdir}"
        assert _discover_preview_pngs(mdir), f"Missing preview PNG in {mdir}"
        json.loads((mdir / "summary.json").read_text(encoding="utf-8"))
