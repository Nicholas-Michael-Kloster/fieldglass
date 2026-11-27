"""Automated verification suite for Milestone M2 (R2 Five Structured Improvement Dossiers)."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from defusedxml import ElementTree as DefusedET
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
DOCS_IMP = REPO_ROOT / "docs" / "improvements"

if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from build_r2_improvements import build_all  # noqa: E402

SUBJECT_SLUGS = ("chatgpt", "anthropic", "grok", "spacex", "claire-grimes")
MAX_REPO_FILE_BYTES = 50 * 1024 * 1024
MAX_PNG_BYTES = 5 * 1024 * 1024


class _LinkAndTagInspector(HTMLParser):
    """Parse HTML to extract href/src links, embedded JSON scripts, and tag balance."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.tag_stack: list[str] = []
        self.void_tags = {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        }
        self.in_json_script = False
        self.json_chunks: list[str] = []
        self.json_blobs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t not in self.void_tags:
            self.tag_stack.append(t)
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        for attr in ("href", "src"):
            if attr in attr_map:
                self.links.append((t, attr_map[attr]))
        if t == "script" and attr_map.get("type", "").lower() == "application/json":
            self.in_json_script = True
            self.json_chunks = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "script" and self.in_json_script:
            self.json_blobs.append("".join(self.json_chunks))
            self.in_json_script = False
            self.json_chunks = []
        if t not in self.void_tags and self.tag_stack and self.tag_stack[-1] == t:
            self.tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.in_json_script:
            self.json_chunks.append(data)


def test_r2_directory_and_file_layout():
    assert DOCS_IMP.is_dir()
    for fname in ("index.html", "hub_overview.svg", "preview.png", "summary.json"):
        assert (DOCS_IMP / fname).is_file(), f"missing hub file {fname}"

    for slug in SUBJECT_SLUGS:
        sdir = DOCS_IMP / slug
        assert sdir.is_dir(), f"missing subject dir {slug}"
        expected = (
            "index.html",
            "architecture.svg",
            "preview.png",
            "chiasm.svg",
            "chiasm_report.json",
            "data.json",
            "summary.json",
            f"{slug}_braille.txt",
            f"{slug}_braille.json",
            f"{slug}_braille_preview.png",
        )
        for fname in expected:
            assert (sdir / fname).is_file(), f"missing {slug}/{fname}"


def test_r2_chiasm_reports_and_hash_integrity():
    for slug in SUBJECT_SLUGS:
        sdir = DOCS_IMP / slug
        rep_path = sdir / "chiasm_report.json"
        chiasm_svg = sdir / "chiasm.svg"
        rep = json.loads(rep_path.read_text(encoding="utf-8"))

        assert rep["contract"] == "fieldglass-causal-chiasm/v1"
        assert rep["executed"] is False
        assert rep["sentience_claimed"] is False
        assert rep["tokens_used"] == 0
        assert rep["episode_count"] == 24
        assert rep["nexus_sec"] == 12
        assert len(rep["per_episode_a004"]) == 24
        assert len(rep["per_episode_a010"]) == 24
        assert all(15 <= v <= 145 for v in rep["per_episode_a004"])
        assert all(8 <= v <= 46 for v in rep["per_episode_a010"])

        expected_scene_sha = hashlib.sha256(chiasm_svg.read_bytes()).hexdigest()
        assert rep["scene_sha256"] == expected_scene_sha

        claimed_sha = rep["report_sha256"]
        assert re.fullmatch(r"[0-9a-f]{64}", claimed_sha)
        check_obj = dict(rep)
        check_obj.pop("report_sha256")
        recomputed = hashlib.sha256(
            json.dumps(check_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert claimed_sha == recomputed


def test_r2_data_and_summary_contracts():
    hub = json.loads((DOCS_IMP / "summary.json").read_text(encoding="utf-8"))
    assert hub["schema_version"] == "fieldglass-improvements-hub/v1"
    assert hub["milestone"] == "M2"
    assert hub["subject_count"] == 5
    assert hub["total_improvements"] == 25
    assert hub["executed"] is False
    assert hub["sentience_claimed"] is False
    assert hub["tokens_used"] == 0
    assert (REPO_ROOT / hub["index_html"]).is_file()
    assert (REPO_ROOT / hub["preview_png"]).is_file()
    assert (REPO_ROOT / hub["hub_overview_svg"]).is_file()

    seen_ids: set[str] = set()
    for slug in SUBJECT_SLUGS:
        sdir = DOCS_IMP / slug
        data = json.loads((sdir / "data.json").read_text(encoding="utf-8"))
        summary = json.loads((sdir / "summary.json").read_text(encoding="utf-8"))

        assert data["schema_version"] == "fieldglass-r2-dossier/v1"
        assert data["executed"] is False
        assert data["sentience_claimed"] is False
        assert data["tokens_used"] == 0
        imps = data["improvements"]
        assert len(imps) == 5
        for imp in imps:
            assert imp["id"] not in seen_ids
            seen_ids.add(imp["id"])
            for field in (
                "title", "short_title", "current_gap", "proposed_architecture",
                "fieldglass_grounding", "concrete_deliverable", "risks_and_mitigations",
                "verification_method",
            ):
                val = imp[field].strip()
                assert len(val) >= 12
                assert "TODO" not in val and "TBD" not in val and "placeholder" not in val.lower()
            assert len(imp["kpis"]) >= 1
            for kpi in imp["kpis"]:
                assert kpi["metric"] and kpi["baseline"] and kpi["target"]

        assert summary["schema_version"] == "fieldglass-summary/v1"
        assert summary["milestone"] == "M2"
        assert summary["slug"] == slug
        assert summary["improvement_count"] == 5
        assert len(summary["top_improvements"]) == 5
        assert len(summary["kpis"]) == 5
        assert summary["clinical_use"] is False
        assert summary["executed"] is False
        assert summary["sentience_claimed"] is False
        assert summary["tokens_used"] == 0
        for key in (
            "index_html", "preview_png", "braille_preview_png",
            "architecture_svg", "chiasm_svg", "chiasm_report", "data_json", "summary_json",
        ):
            assert (REPO_ROOT / summary[key]).is_file(), f"{slug} summary {key} missing"


def test_r2_html_self_contained_and_links_valid():
    html_files = [DOCS_IMP / "index.html", *[DOCS_IMP / slug / "index.html" for slug in SUBJECT_SLUGS]]
    external_pat = re.compile(r"(?:https?:)?//", re.IGNORECASE)

    for hf in html_files:
        raw = hf.read_text(encoding="utf-8")
        assert "@import" not in raw.lower()
        assert not re.search(r"url\(\s*['\"]?(?:https?:)?//", raw, re.IGNORECASE)

        parser = _LinkAndTagInspector()
        parser.feed(raw)
        parser.close()
        assert parser.tag_stack == [], f"unbalanced HTML tags in {hf}: {parser.tag_stack}"
        assert len(parser.json_blobs) >= 1, f"missing embedded JSON in {hf}"
        for blob in parser.json_blobs:
            json.loads(blob)

        for tag, link in parser.links:
            assert not external_pat.match(link.strip()), f"external URL in {hf} <{tag}>: {link}"
            clean = link.split("#", 1)[0].strip()
            if not clean or clean.startswith("data:"):
                assert not external_pat.search(clean), f"external URL inside data URI in {hf}: {clean}"
                continue
            target = (hf.parent / clean).resolve()
            assert target.is_file(), f"broken relative link in {hf}: {link} -> {target}"


def test_r2_svgs_well_formed_xml():
    svgs = [
        DOCS_IMP / "hub_overview.svg",
        *[DOCS_IMP / slug / "architecture.svg" for slug in SUBJECT_SLUGS],
        *[DOCS_IMP / slug / "chiasm.svg" for slug in SUBJECT_SLUGS],
    ]
    for sp in svgs:
        root = DefusedET.fromstring(sp.read_text(encoding="utf-8"))
        assert root.tag.endswith("svg")


def _rects_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 < bx2 and bx1 < ax2 and ay1 < by2 and by1 < ay2


def test_r2_architecture_svg_geometry_no_overlap():
    panel_x1, panel_y1, panel_x2, panel_y2 = 30.0, 106.0, 1370.0, 520.0
    for slug in SUBJECT_SLUGS:
        svg_path = DOCS_IMP / slug / "architecture.svg"
        root = DefusedET.fromstring(svg_path.read_text(encoding="utf-8"))
        nodes: list[tuple[float, float, float, float]] = []
        edge_labels: list[tuple[float, float, float, float]] = []
        for elem in root.iter():
            if not elem.tag.endswith("rect"):
                continue
            role = elem.attrib.get("data-role")
            if role not in ("node", "edge-label"):
                continue
            x = float(elem.attrib["x"])
            y = float(elem.attrib["y"])
            w = float(elem.attrib["width"])
            h = float(elem.attrib["height"])
            box = (x, y, x + w, y + h)
            assert box[0] >= panel_x1 and box[2] <= panel_x2, f"{slug} {role} out of X panel: {box}"
            assert box[1] >= panel_y1 and box[3] <= panel_y2, f"{slug} {role} out of Y panel: {box}"
            if role == "node":
                nodes.append(box)
            else:
                edge_labels.append(box)

        assert len(nodes) >= 6, f"{slug} expected >=6 nodes, got {len(nodes)}"
        assert len(edge_labels) >= 7, f"{slug} expected >=7 edge-labels, got {len(edge_labels)}"

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                assert not _rects_overlap(nodes[i], nodes[j]), f"{slug} node overlap: {nodes[i]} vs {nodes[j]}"

        for i in range(len(edge_labels)):
            for j in range(i + 1, len(edge_labels)):
                assert not _rects_overlap(edge_labels[i], edge_labels[j]), (
                    f"{slug} edge-label overlap: {edge_labels[i]} vs {edge_labels[j]}"
                )

        for nb in nodes:
            for eb in edge_labels:
                assert not _rects_overlap(nb, eb), f"{slug} node vs edge-label overlap: {nb} vs {eb}"


def test_r2_braille_bundles_valid():
    for slug in SUBJECT_SLUGS:
        sdir = DOCS_IMP / slug
        txt = (sdir / f"{slug}_braille.txt").read_text(encoding="utf-8")
        payload = json.loads((sdir / f"{slug}_braille.json").read_text(encoding="utf-8"))
        png = sdir / f"{slug}_braille_preview.png"

        assert payload["cols"] == 72
        assert payload["rows"] > 8
        lines = payload["lines"]
        assert len(lines) == payload["rows"]
        all_chars = [ch for ln in lines for ch in ln]
        assert all(0x2800 <= ord(ch) <= 0x28FF for ch in all_chars)
        non_blank = sum(1 for ch in all_chars if ord(ch) > 0x2800)
        solid = sum(1 for ch in all_chars if ord(ch) == 0x28FF)
        assert non_blank > 50, f"{slug} braille unexpectedly blank"
        assert solid < len(all_chars) * 0.5, f"{slug} braille unexpectedly solid"
        assert any(ln in txt for ln in lines[:3])

        with Image.open(png) as im:
            im.verify()


def test_r2_media_hygiene_size_and_zero_gps():
    for p in DOCS_IMP.rglob("*"):
        if p.is_file():
            assert p.stat().st_size < MAX_REPO_FILE_BYTES, f"{p} exceeds 50 MB"

    pngs = sorted(DOCS_IMP.rglob("*.png"))
    assert len(pngs) == 11  # 1 hub + 5 arch + 5 braille
    for png in pngs:
        assert png.stat().st_size < MAX_PNG_BYTES, f"{png} exceeds 5 MB"
        with Image.open(png) as im:
            im.verify()
        with Image.open(png) as im:
            exif = im.getexif()
            assert len(exif) == 0, f"unexpected EXIF tags in {png}: {dict(exif)}"

    exiftool = shutil.which("exiftool")
    if exiftool:
        out = subprocess.check_output(
            [exiftool, "-j", "-GPS:all", *[str(p) for p in pngs]],
            text=True,
        )
        records = json.loads(out)
        assert len(records) == len(pngs)
        for rec in records:
            gps_keys = [k for k in rec if "GPS" in k.upper()]
            assert gps_keys == [], f"GPS metadata found in {rec.get('SourceFile')}: {gps_keys}"


def test_r2_builder_determinism(tmp_path: Path):
    fake_docs = tmp_path / "docs"
    fake_docs.mkdir()
    res = build_all(fake_docs)
    assert res["subject_count"] == 5
    assert res["total_improvements"] == 25

    rebuilt_root = fake_docs / "improvements"
    committed_files = sorted(p.relative_to(DOCS_IMP) for p in DOCS_IMP.rglob("*") if p.is_file())
    rebuilt_files = sorted(p.relative_to(rebuilt_root) for p in rebuilt_root.rglob("*") if p.is_file())
    assert committed_files == rebuilt_files
    assert len(committed_files) == 54

    mismatches: list[str] = []
    for rel in committed_files:
        c_sha = hashlib.sha256((DOCS_IMP / rel).read_bytes()).hexdigest()
        r_sha = hashlib.sha256((rebuilt_root / rel).read_bytes()).hexdigest()
        if c_sha != r_sha:
            mismatches.append(f"{rel}: {c_sha} != {r_sha}")
    assert mismatches == [], f"Non-deterministic outputs: {mismatches}"
