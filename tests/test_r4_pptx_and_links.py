"""Automated verification suite for Milestone M4 (R4 PPTX, docs/index.html, README.md, and R5 gates)."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

# Conditional sys.path bootstrap so bare /usr/bin/python3 can import python-pptx
_SECTOOLS_SITE = Path("/home/cowboy/security-tools/lib/python3.14/site-packages")
if importlib.util.find_spec("pptx") is None and _SECTOOLS_SITE.is_dir():
    sys.path.insert(0, str(_SECTOOLS_SITE))

import numpy as np
from PIL import Image
from pptx import Presentation

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
BUILDER_PY = REPO_ROOT / "examples" / "build_observatory_r1_r4_pptx.py"
DOCS_PPTX = DOCS / "Fieldglass_Observatory_Expansion.pptx"
ROOT_PPTX = REPO_ROOT / "Fieldglass_Observatory_Expansion.pptx"

MAX_FILE_BYTES = 50 * 1024 * 1024
EXPECTED_SLIDES = 16
R2_SLUGS = ("chatgpt", "anthropic", "grok", "spacex", "claire-grimes")
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".mp4", ".mov", ".webp", ".gif", ".mp3"}


class _ObservatoryHTMLInspector(HTMLParser):
    """Validate HTML tag balance, absence of scripts, ids, and href/src links."""

    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__()
        self.tag_stack: list[str] = []
        self.unmatched_end_tags: list[str] = []
        self.script_count = 0
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t == "script":
            self.script_count += 1
        if t not in self.VOID_TAGS:
            self.tag_stack.append(t)
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if attr_map.get("id"):
            self.ids.add(attr_map["id"])
        for attr in ("href", "src"):
            if attr in attr_map:
                self.links.append((t, attr_map[attr]))

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self.VOID_TAGS:
            return
        if self.tag_stack and self.tag_stack[-1] == t:
            self.tag_stack.pop()
        else:
            self.unmatched_end_tags.append(t)


def test_r4_pptx_exists_identical_and_under_50mb() -> None:
    assert BUILDER_PY.is_file(), f"Missing builder: {BUILDER_PY}"
    builder_src = BUILDER_PY.read_text(encoding="utf-8")
    assert "/home/cowboy/security-tools/lib/python3.14/site-packages" in builder_src
    assert 'find_spec("pptx")' in builder_src or "find_spec('pptx')" in builder_src
    assert "TemporaryDirectory" in builder_src
    assert "/tmp/" not in builder_src

    assert DOCS_PPTX.is_file(), f"Missing {DOCS_PPTX}"
    assert ROOT_PPTX.is_file(), f"Missing {ROOT_PPTX}"

    docs_size = DOCS_PPTX.stat().st_size
    root_size = ROOT_PPTX.stat().st_size
    assert 0 < docs_size < MAX_FILE_BYTES
    assert 0 < root_size < MAX_FILE_BYTES

    docs_sha = hashlib.sha256(DOCS_PPTX.read_bytes()).hexdigest()
    root_sha = hashlib.sha256(ROOT_PPTX.read_bytes()).hexdigest()
    assert docs_sha == root_sha, "docs/ and root .pptx copies must be byte-identical"


def _extract_slide_text(slide) -> str:
    chunks: list[str] = []
    for shp in slide.shapes:
        if shp.has_text_frame:
            chunks.append(shp.text_frame.text)
        if shp.has_table:
            for row in shp.table.rows:
                for cell in row.cells:
                    chunks.append(cell.text)
    if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
        chunks.append(slide.notes_slide.notes_text_frame.text)
    return "\n".join(chunks)


def test_r4_pptx_opens_covers_all_topics_and_disclaimers(tmp_path: Path) -> None:
    prs = Presentation(str(DOCS_PPTX))
    assert abs(prs.slide_width.inches - 13.333) < 0.05
    assert abs(prs.slide_height.inches - 7.5) < 0.05
    assert len(prs.slides) == EXPECTED_SLIDES

    slide_texts = [_extract_slide_text(s) for s in prs.slides]
    full_text = "\n".join(slide_texts)
    full_lower = full_text.lower()

    # R1 coverage
    for kw in ("ms-dos", "8086", "flight", "6-dof", "medical", "software"):
        assert kw in full_lower, f"Missing R1 keyword '{kw}' in presentation"

    # R2 dedicated slides + coverage
    for kw in ("chatgpt", "anthropic", "grok", "spacex", "claire", "grimes"):
        assert kw in full_lower, f"Missing R2 subject '{kw}' in presentation"
    for idx, subj_kw in ((7, "cgpt-01"), (8, "anth-01"), (9, "grok-01"), (10, "spx-01"), (11, "grimes-01")):
        assert subj_kw in slide_texts[idx].lower(), f"Expected dedicated slide {idx + 1} to cover {subj_kw}"

    # R3 Zoe Hospital (Win7) coverage
    for kw in ("zoe hospital", "windows 7", "mshta.exe", "zoe_hospital_win7.py"):
        assert kw in full_lower, f"Missing R3 keyword '{kw}' in presentation"

    # Non-clinical disclaimers & epistemic invariants
    assert "not for clinical" in full_lower
    assert "simulated" in full_lower
    assert "educational" in full_lower
    assert "clinical_use=false" in full_lower
    assert "executed=false" in full_lower
    assert "tokens_used=0" in full_lower

    # Embedded ppt/media/* images decode cleanly and have 0 GPS EXIF tags
    media_dir = tmp_path / "pptx_media"
    media_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with zipfile.ZipFile(DOCS_PPTX) as zf:
        for member in zf.namelist():
            if member.startswith("ppt/media/") and not member.endswith("/"):
                out = media_dir / Path(member).name
                out.write_bytes(zf.read(member))
                extracted.append(out)
                if out.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                    with Image.open(out) as im:
                        im.verify()
                    with Image.open(out) as im:
                        assert 0x8825 not in im.getexif(), f"GPS IFD found in {member}"

    assert len(extracted) >= 12
    exif_out = subprocess.check_output(
        ["exiftool", "-j", "-GPS:all", *(str(p) for p in extracted)],
        text=True,
    )
    records = json.loads(exif_out)
    for rec in records:
        gps_keys = [k for k in rec if k != "SourceFile" and "GPS" in k.upper()]
        assert not gps_keys, f"GPS metadata found in embedded media {rec}"


def test_r4_pptx_libreoffice_pdf_and_pdftoppm_render(tmp_path: Path) -> None:
    subprocess.run(
        [
            "/usr/bin/libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(tmp_path), str(DOCS_PPTX),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pdf_path = tmp_path / f"{DOCS_PPTX.stem}.pdf"
    assert pdf_path.is_file() and pdf_path.stat().st_size > 0

    subprocess.run(
        [
            "/usr/bin/pdftoppm", "-png", "-r", "100",
            str(pdf_path), str(tmp_path / "slide"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pngs = sorted(tmp_path.glob("slide-*.png"))
    assert len(pngs) == EXPECTED_SLIDES, f"Expected {EXPECTED_SLIDES} rendered slides, got {len(pngs)}"
    for png in pngs:
        with Image.open(png) as im:
            assert im.mode == "RGB"
            arr = np.asarray(im)
            assert arr.shape[0] > 400 and arr.shape[1] > 700
            assert float(arr.std()) > 5.0, f"Rendered slide appears blank: {png.name}"


def test_r4_docs_index_html_preservation_and_zero_broken_links() -> None:
    index_path = DOCS / "index.html"
    html = index_path.read_text(encoding="utf-8")

    inspector = _ObservatoryHTMLInspector()
    inspector.feed(html)
    inspector.close()

    assert inspector.tag_stack == [], f"Unclosed tags in docs/index.html: {inspector.tag_stack}"
    assert inspector.unmatched_end_tags == [], f"Unmatched end tags: {inspector.unmatched_end_tags}"
    assert inspector.script_count == 0, "docs/index.html must remain pure HTML/CSS with 0 <script> tags"

    # Preserve all 29 specimens + how-it-works + new R1-R4 sections
    for n in range(1, 30):
        assert f"specimen-{n}" in inspector.ids, f"Missing preserved #specimen-{n}"
    for sec in ("how-it-works", "observatory-r4", "observatory-r1", "observatory-r2", "observatory-r3"):
        assert sec in inspector.ids, f"Missing section #{sec}"

    hrefs = {val for _, val in inspector.links}
    required_links = {
        "Fieldglass_Observatory_Expansion.pptx",
        "msdos/index.html",
        "flight-sim/index.html",
        "medical-sim/index.html",
        "software/index.html",
        "improvements/index.html",
        "zoe-hospital/index.html",
        "zoe-hospital/zoe_hospital_win7_bundle.zip",
        *(f"improvements/{slug}/index.html" for slug in R2_SLUGS),
    }
    missing = required_links - hrefs
    assert not missing, f"Missing required Observatory links in docs/index.html: {sorted(missing)}"

    # Check every href/src resolves locally and forbid external CDNs
    allowed_external_prefixes = (
        "https://github.com/Nicholas-Michael-Kloster/",
    )
    for tag, target in inspector.links:
        if target.startswith("#"):
            assert target[1:] in inspector.ids, f"Broken anchor link {target} on <{tag}>"
        elif target.startswith(("http://", "https://")):
            assert target.startswith(allowed_external_prefixes), f"Disallowed external link {target}"
        else:
            rel = target.split("#", 1)[0].split("?", 1)[0]
            resolved = (DOCS / rel).resolve()
            assert resolved.is_relative_to(DOCS.resolve()), f"Escaping link {target}"
            assert resolved.exists(), f"Broken local link in docs/index.html: {target}"

    # Explicit non-clinical disclaimers near medical-sim and zoe-hospital sections
    lower_html = html.lower()
    assert "strictly simulated / educational only" in lower_html
    assert "not for clinical, diagnostic, or patient-care use" in lower_html
    assert "no clinical certification claimed" in lower_html


def test_r4_readme_documentation_and_constraints() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    lower = readme.lower()

    for required in (
        "fieldglass_observatory_expansion.pptx",
        "ms-dos",
        "flight",
        "medical",
        "software",
        "chatgpt",
        "anthropic",
        "grok",
        "spacex",
        "claire",
        "grimes",
        "zoe hospital",
        "windows 7",
        "not for clinical",
        "/usr/bin/python3",
        "50 mb",
        "-map_metadata -1",
        "git add -a",
        "zoe-monorepo",
        "git data api",
    ):
        assert required in lower, f"Missing '{required}' documentation in README.md"


def test_r4_docs_tree_size_and_zero_gps_gate() -> None:
    media_files: list[Path] = []
    all_files = [p for p in DOCS.rglob("*") if p.is_file()]
    assert len(all_files) > 750

    for path in all_files:
        size = path.stat().st_size
        assert size < MAX_FILE_BYTES, f"File exceeds 50 MB gate ({size} B): {path}"
        if path.suffix.lower() in MEDIA_EXTS:
            media_files.append(path)
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                with Image.open(path) as im:
                    assert 0x8825 not in im.getexif(), f"GPS IFD found via PIL in {path}"

    assert len(media_files) >= 475
    batch_size = 100
    for start in range(0, len(media_files), batch_size):
        batch = media_files[start:start + batch_size]
        out = subprocess.check_output(
            ["exiftool", "-j", "-GPS:all", *(str(p) for p in batch)],
            text=True,
        )
        records = json.loads(out)
        for rec in records:
            gps_keys = [k for k in rec if k != "SourceFile" and "GPS" in k.upper()]
            assert not gps_keys, f"GPS metadata found by exiftool: {rec}"
