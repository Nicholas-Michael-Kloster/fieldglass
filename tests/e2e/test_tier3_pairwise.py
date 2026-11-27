"""Tier 3: Pairwise cross-module link integrity, parity, and baseline regression tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pytest

from validators import validate_pptx_deck, validate_relative_links_in_html

pytestmark = pytest.mark.tier3

NEW_MODULE_DIRS = (
    "msdos",
    "flight-sim",
    "medical-sim",
    "software",
    "improvements",
    "improvements/chatgpt",
    "improvements/anthropic",
    "improvements/grok",
    "improvements/spacex",
    "improvements/claire-grimes",
    "zoe-hospital",
)

MODULE_SUMMARY_TOPIC_MAP = {
    "msdos": ("ms-dos", "msdos"),
    "flight-sim": ("flight",),
    "medical-sim": ("medical",),
    "software": ("software",),
    "improvements/chatgpt": ("chatgpt",),
    "improvements/anthropic": ("anthropic",),
    "improvements/grok": ("grok",),
    "improvements/spacex": ("spacex",),
    "improvements/claire-grimes": ("claire", "grimes"),
    "zoe-hospital": ("zoe", "hospital"),
}


def test_tier3_docs_index_html_all_links_and_anchors_resolve(docs_root: Path) -> None:
    index_p = docs_root / "index.html"
    checked = validate_relative_links_in_html(index_p, docs_root=docs_root)
    assert checked >= 500, f"Expected full specimen + expansion link set (>=500), got {checked}"


@pytest.mark.parametrize("rel_dir", NEW_MODULE_DIRS)
def test_tier3_module_index_relative_links_resolve(docs_root: Path, rel_dir: str) -> None:
    index_p = docs_root / rel_dir / "index.html"
    checked = validate_relative_links_in_html(index_p, docs_root=docs_root)
    assert checked >= 1, f"Expected >= 1 relative asset/nav link in {index_p}"


def test_tier3_readme_relative_links_resolve(obs_root: Path) -> None:
    readme = obs_root / "README.md"
    assert readme.is_file(), f"Missing {readme}"
    txt = readme.read_text(encoding="utf-8")

    md_links = re.findall(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", txt)
    html_links = re.findall(r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", txt, re.I)

    broken: list[str] = []
    checked = 0
    for target in md_links + html_links:
        t = target.strip()
        if not t or t.startswith(("http://", "https://", "//", "#", "mailto:")):
            continue
        path_part = t.split("#", 1)[0].split("?", 1)[0]
        if not path_part:
            continue
        checked += 1
        resolved = (obs_root / path_part).resolve()
        if not (resolved.is_file() or (resolved.is_dir() and (resolved / "index.html").is_file())):
            broken.append(t)

    assert checked >= 10, f"Expected >= 10 relative links in README.md, got {checked}"
    assert not broken, f"README.md contains broken relative links: {broken}"
    assert "Fieldglass_Observatory_Expansion.pptx" in txt


def test_tier3_summary_json_vs_pptx_slide_text_consistency(docs_root: Path) -> None:
    deck = validate_pptx_deck(docs_root / "Fieldglass_Observatory_Expansion.pptx", min_slides=8)
    deck_low = deck["full_text"].lower()

    for rel_dir, expected_tokens in MODULE_SUMMARY_TOPIC_MAP.items():
        summary_p = docs_root / rel_dir / "summary.json"
        assert summary_p.is_file(), f"Missing {summary_p}"
        summary = json.loads(summary_p.read_text(encoding="utf-8"))
        assert isinstance(summary, dict) and summary
        assert any(tok in deck_low for tok in expected_tokens), (
            f"PPTX slide text missing topic from {summary_p} ({expected_tokens})"
        )


def test_tier3_docs_pptx_and_root_pptx_parity(obs_root: Path, docs_root: Path) -> None:
    docs_pptx = docs_root / "Fieldglass_Observatory_Expansion.pptx"
    root_pptx = obs_root / "Fieldglass_Observatory_Expansion.pptx"

    docs_info = validate_pptx_deck(docs_pptx, min_slides=8)
    root_info = validate_pptx_deck(root_pptx, min_slides=8)

    assert docs_info["slide_count"] == root_info["slide_count"]
    assert docs_info["slide_texts"] == root_info["slide_texts"]

    docs_sha = hashlib.sha256(docs_pptx.read_bytes()).hexdigest()
    root_sha = hashlib.sha256(root_pptx.read_bytes()).hexdigest()
    assert docs_sha == root_sha, f"PPTX mismatch between docs/ ({docs_sha}) and root ({root_sha})"


def test_tier3_zoe_hospital_zip_manifest_bat_disk_parity(docs_root: Path) -> None:
    zh = docs_root / "zoe-hospital"
    manifest_p = zh / "manifest.json"
    zip_p = zh / "zoe_hospital_win7_bundle.zip"
    bat_p = zh / "launch_win7.bat"

    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    manifest_str = json.dumps(manifest).lower()
    bat_txt = bat_p.read_text(encoding="utf-8")

    core_files = (
        "zoe_hospital_win7.py",
        "zoe_hospital_kiosk.html",
        "zoe_hospital_kiosk.hta",
        "launch_win7.bat",
    )
    for fname in core_files:
        assert (zh / fname).is_file(), f"Missing {zh / fname}"
        assert fname.lower() in manifest_str, f"{fname} not listed in manifest.json"

    assert "zoe_hospital_win7.py" in bat_txt or "zoe_hospital_kiosk.hta" in bat_txt

    with zipfile.ZipFile(zip_p, "r") as zf:
        entries = {Path(n).name: n for n in zf.namelist() if not n.endswith("/")}
        for fname in core_files:
            assert fname in entries, f"{fname} missing from {zip_p}"
            assert zf.read(entries[fname]) == (zh / fname).read_bytes(), (
                f"Zip entry {entries[fname]} differs from disk file {zh / fname}"
            )


def test_tier3_baseline_fieldglass_unit_tests_pass_without_regression(obs_root: Path) -> None:
    import os

    baseline_test = obs_root / "tests" / "test_fieldglass.py"
    assert baseline_test.is_file(), f"Missing baseline test file: {baseline_test}"

    env = dict(os.environ)
    src_path = str(obs_root / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(baseline_test), "-q"],
        cwd=str(obs_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"Baseline tests/test_fieldglass.py failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    )
    assert "5 passed" in proc.stdout, f"Expected 5 passed in baseline suite, got:\n{proc.stdout}"
