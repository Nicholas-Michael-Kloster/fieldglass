"""Pure, reusable opaque-box validators for Fieldglass Observatory E2E & selfcheck tests."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image
from pptx import Presentation

MAX_DOCS_BYTES = 50 * 1024 * 1024  # 52,428,800 bytes

DEFAULT_NODE_CANDIDATES = (
    shutil.which("node"),
    "/home/cowboy/.nvm/versions/node/v24.16.0/bin/node",
)

XML_NAMESPACE_URIS = frozenset(
    {
        "http://www.w3.org/2000/svg",
        "http://www.w3.org/1999/xhtml",
        "http://www.w3.org/1999/xlink",
        "http://www.w3.org/XML/1998/namespace",
        "http://www.w3.org/2000/xmlns/",
    }
)

POST_37_STDLIB_MODULES = frozenset(
    {
        "backports",
        "graphlib",
        "tomllib",
        "zoneinfo",
    }
)

POST_37_IMPORTLIB_SUBMODULES = frozenset({"importlib.metadata", "importlib.resources.abc"})

POST_37_TYPING_NAMES = frozenset(
    {
        "Annotated",
        "Concatenate",
        "Final",
        "Literal",
        "LiteralString",
        "Never",
        "NotRequired",
        "ParamSpec",
        "ParamSpecArgs",
        "ParamSpecKwargs",
        "Protocol",
        "Required",
        "Self",
        "TypeAlias",
        "TypeGuard",
        "TypeVarTuple",
        "TypedDict",
        "Unpack",
        "assert_never",
        "dataclass_transform",
        "override",
        "runtime_checkable",
    }
)

PEP585_BUILTIN_GENERICS = frozenset({"list", "dict", "set", "tuple", "frozenset", "type"})

GPS_TAG_RE = re.compile(r"(gps|latitude|longitude|altitude|coordinates|location)", re.I)

CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""", re.I | re.S)
CSS_IMPORT_RE = re.compile(r"""@import\s+(?:url\(\s*)?(['"])(.*?)\1""", re.I | re.S)
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)

EXTERNAL_URL_RE = re.compile(r"^\s*(?:https?:)?//", re.I)

ES6_KEYWORD_RE = re.compile(
    r"\b(?:let|const|class|extends|super|import|export|yield|async|await|"
    r"Promise|Map|Set|Symbol|Proxy|Reflect|WeakMap|WeakSet)\b"
)
ES6_FETCH_RE = re.compile(r"\bfetch\s*\(")
ES6_ARROW_RE = re.compile(r"=>")
ES6_SPREAD_RE = re.compile(r"\.\.\.")
ES6_OPTIONAL_CHAIN_RE = re.compile(r"\?\.")
ES6_NULLISH_RE = re.compile(r"\?\?")
ES6_EXP_RE = re.compile(r"\*\*")
ES6_FOR_OF_RE = re.compile(r"\bfor\s*\([^)]*\bof\b")
ES6_DESTRUCTURE_RE = re.compile(r"\bvar\s*[\{\[]")
ES6_PARAM_DESTRUCTURE_RE = re.compile(
    r"\bfunction(?:\s+[A-Za-z_$][A-Za-z0-9_$]*)?\s*\([^)]*[\{\[]"
)
ES6_DEFAULT_PARAM_RE = re.compile(r"\bfunction(?:\s+[A-Za-z_$][A-Za-z0-9_$]*)?\s*\([^)]*=")

NONCLINICAL_REQUIRED_RE = re.compile(
    r"\b(?:simulat\w*|educational|non[- ]?clinical|not\s+for\s+clinical)\b", re.I
)
CLINICAL_CLAIM_RE = re.compile(
    r"\b(?:fda[-\s]+(?:approved|cleared)|clinically\s+certified|"
    r"clinical\s+certification(?:\s+(?:achieved|granted|approved|claimed))?|"
    r"(?:approved|cleared)\s+for\s+(?:clinical|patient|diagnostic)\s+use|"
    r"intended\s+for\s+(?:patient\s+care|clinical\s+diagnosis)|"
    r"for\s+patient\s+diagnosis|diagnostic\s+medical\s+device)\b",
    re.I,
)
NEGATION_PREFIX_RE = re.compile(
    r"\b(?:not|no|never|non(?!-)|without|zero|neither|nor|cannot|can't)\b", re.I
)

ALLOWED_HTML_PLACEHOLDER_STUBS = re.compile(
    r"\b(?:lorem\s+ipsum|coming\s+soon|under\s+construction|todo:\s*replace)\b", re.I
)


def _find_node_bin() -> str:
    for cand in DEFAULT_NODE_CANDIDATES:
        if cand and Path(cand).is_file():
            return str(cand)
    raise FileNotFoundError("node binary not found on PATH or nvm path")


@dataclass
class ParsedHtmlAssets:
    scripts: list[str] = field(default_factory=list)
    event_handlers: list[tuple[str, str, str]] = field(default_factory=list)
    script_srcs: list[str] = field(default_factory=list)
    link_hrefs: list[str] = field(default_factory=list)
    img_srcs: list[str] = field(default_factory=list)
    a_hrefs: list[str] = field(default_factory=list)
    media_urls: list[tuple[str, str, str]] = field(default_factory=list)
    anchor_urls: list[tuple[str, str, str]] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    css_urls: list[str] = field(default_factory=list)
    anchor_ids: set[str] = field(default_factory=set)
    visible_text: str = ""
    has_html_tag: bool = False
    has_body_tag: bool = False
    has_hta_tag: bool = False


def _parse_srcset_urls(srcset_val: str) -> list[str]:
    """Parse HTML srcset attribute into individual candidate URLs (ignoring descriptors)."""
    urls: list[str] = []
    s = srcset_val.strip()
    i = 0
    n = len(s)
    while i < n:
        while i < n and (s[i].isspace() or s[i] == ","):
            i += 1
        if i >= n:
            break
        if s[i:].lower().startswith("data:"):
            start = i
            while i < n and not s[i].isspace():
                i += 1
            urls.append(s[start:i])
            while i < n and s[i] != ",":
                i += 1
        else:
            start = i
            while i < n and not s[i].isspace() and s[i] != ",":
                i += 1
            cand = s[start:i].rstrip(",")
            if cand:
                urls.append(cand)
            if i < n and s[i] != ",":
                while i < n and s[i] != ",":
                    i += 1
    return urls


@dataclass
class PptxRenderResult:
    pptx_path: Path
    pdf_path: Path
    slide_pngs: list[Path]
    slide_stds: list[float]
    slide_count: int


class _AssetHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._in_script = False
        self._script_has_src = False
        self._script_buf: list[str] = []
        self._in_style = False
        self._style_buf: list[str] = []
        self._suppress_text_depth = 0
        self._text_buf: list[str] = []
        self.assets = ParsedHtmlAssets()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t == "html":
            self.assets.has_html_tag = True
        elif t == "body":
            self.assets.has_body_tag = True
        elif t == "hta:application":
            self.assets.has_hta_tag = True

        if "id" in attr_map and attr_map["id"]:
            self.assets.anchor_ids.add(attr_map["id"])
        if "name" in attr_map and attr_map["name"] and t == "a":
            self.assets.anchor_ids.add(attr_map["name"])
        if "style" in attr_map and attr_map["style"]:
            self.assets.styles.append(attr_map["style"])

        for attr_k, attr_v in attrs:
            k_low = attr_k.lower()
            if attr_v and attr_v.strip() and re.fullmatch(r"on[a-z]{3,}", k_low):
                self.assets.event_handlers.append((t, k_low, attr_v))

        if attr_map.get("srcset"):
            for srcset_url in _parse_srcset_urls(attr_map["srcset"]):
                self.assets.media_urls.append((t, "srcset", srcset_url))

        if t == "script":
            self._in_script = True
            self._script_has_src = bool(attr_map.get("src"))
            self._script_buf = []
            if attr_map.get("src"):
                src_v = attr_map["src"]
                self.assets.script_srcs.append(src_v)
                self.assets.media_urls.append((t, "src", src_v))
            return

        if t == "style":
            self._in_style = True
            self._style_buf = []
            return

        if t in {"noscript", "template"}:
            self._suppress_text_depth += 1

        if t == "link" and attr_map.get("href"):
            href_v = attr_map["href"]
            self.assets.link_hrefs.append(href_v)
            self.assets.media_urls.append((t, "href", href_v))
        elif t == "img" and attr_map.get("src"):
            src_v = attr_map["src"]
            self.assets.img_srcs.append(src_v)
            self.assets.media_urls.append((t, "src", src_v))
        elif t in {"a", "area"} and "href" in attr_map:
            href_v = attr_map["href"]
            self.assets.a_hrefs.append(href_v)
            self.assets.anchor_urls.append((t, "href", href_v))
        elif t == "form" and attr_map.get("action"):
            self.assets.anchor_urls.append((t, "action", attr_map["action"]))
        else:
            for attr_name in ("src", "poster", "data", "href", "xlink:href"):
                if attr_name in attr_map and attr_map[attr_name]:
                    self.assets.media_urls.append((t, attr_name, attr_map[attr_name]))

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "script" and self._in_script:
            body = "".join(self._script_buf)
            if body.strip() and not self._script_has_src:
                self.assets.scripts.append(body)
            self._in_script = False
            self._script_has_src = False
            self._script_buf = []
        elif t == "style" and self._in_style:
            css_body = "".join(self._style_buf)
            if css_body.strip():
                self.assets.styles.append(css_body)
            self._in_style = False
            self._style_buf = []
        elif t in {"noscript", "template"} and self._suppress_text_depth > 0:
            self._suppress_text_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._script_buf.append(data)
        elif self._in_style:
            self._style_buf.append(data)
        elif self._suppress_text_depth == 0:
            self._text_buf.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_script:
            self._script_buf.append(f"&{name};")
        elif self._in_style:
            self._style_buf.append(f"&{name};")
        elif self._suppress_text_depth == 0:
            self._text_buf.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._in_script:
            self._script_buf.append(f"&#{name};")
        elif self._in_style:
            self._style_buf.append(f"&#{name};")
        elif self._suppress_text_depth == 0:
            self._text_buf.append(f"&#{name};")

    def finalize(self) -> ParsedHtmlAssets:
        if self._in_script and self._script_buf and not self._script_has_src:
            body = "".join(self._script_buf)
            if body.strip():
                self.assets.scripts.append(body)
        if self._in_style and self._style_buf:
            css_body = "".join(self._style_buf)
            if css_body.strip():
                self.assets.styles.append(css_body)
        for css in self.assets.styles:
            css_clean = CSS_COMMENT_RE.sub(" ", css)
            for m in CSS_URL_RE.finditer(css_clean):
                target = m.group(2).strip()
                if target:
                    self.assets.css_urls.append(target)
            for m in CSS_IMPORT_RE.finditer(css_clean):
                target = m.group(2).strip()
                if target:
                    self.assets.css_urls.append(target)
        raw_text = " ".join(self._text_buf)
        self.assets.visible_text = re.sub(r"\s+", " ", raw_text).strip()
        return self.assets


def parse_html_assets(html_text: str) -> ParsedHtmlAssets:
    """Parse HTML/HTA text into scripts, links, styles, anchor IDs, and visible text."""
    parser = _AssetHTMLParser()
    parser.feed(html_text)
    parser.close()
    return parser.finalize()


def _is_external_non_xmlns_url(url: str) -> bool:
    u = url.strip()
    if not u or u.startswith("data:") or u.startswith("blob:") or u.startswith("#"):
        return False
    if u in XML_NAMESPACE_URIS:
        return False
    return bool(EXTERNAL_URL_RE.match(u))


def validate_html_document(
    path: Path,
    min_visible_chars: int = 80,
    forbid_external_anchors: bool = False,
) -> ParsedHtmlAssets:
    """Validate HTML/HTA structure, non-placeholder content, and zero external CDN URLs."""
    assert path.is_file(), f"Missing HTML/HTA file: {path}"
    raw = path.read_text(encoding="utf-8")
    assert raw.strip(), f"Empty HTML/HTA file: {path}"
    lower = raw.lower()
    assert ("<html" in lower) or ("<!doctype" in lower) or ("<hta:application" in lower), (
        f"Missing root HTML/DOCTYPE/HTA tag in {path}"
    )

    assets = parse_html_assets(raw)
    assert len(assets.visible_text) >= min_visible_chars, (
        f"{path}: visible text too short ({len(assets.visible_text)} < {min_visible_chars})"
    )
    stub_match = ALLOWED_HTML_PLACEHOLDER_STUBS.search(assets.visible_text)
    assert stub_match is None, f"{path}: placeholder stub text detected: {stub_match.group(0)!r}"

    cdn_violations: list[str] = []
    for tag, attr, val in assets.media_urls:
        if _is_external_non_xmlns_url(val):
            cdn_violations.append(f"<{tag} {attr}={val!r}>")
    for css_url in assets.css_urls:
        if _is_external_non_xmlns_url(css_url):
            cdn_violations.append(f"CSS url/import {css_url!r}")
    if forbid_external_anchors:
        for tag, attr, val in assets.anchor_urls:
            if _is_external_non_xmlns_url(val):
                cdn_violations.append(f"<{tag} {attr}={val!r}>")

    assert not cdn_violations, f"{path}: external CDN/network URLs forbidden: {cdn_violations}"
    return assets


def validate_svg_document(path: Path) -> ET.Element:
    """Validate SVG XML structure and verify zero external asset/CDN URLs."""
    assert path.is_file(), f"Missing SVG file: {path}"
    raw = path.read_text(encoding="utf-8")
    assert raw.strip(), f"Empty SVG file: {path}"
    root = ET.fromstring(raw)
    assert root.tag.lower().endswith("svg"), f"{path}: root element is not <svg>: {root.tag}"

    violations: list[str] = []
    for elem in root.iter():
        for attr_k, attr_v in elem.attrib.items():
            k_low = attr_k.lower()
            if k_low == "xmlns" or k_low.startswith("xmlns:") or k_low.startswith("{http://www.w3.org/2000/xmlns/}"):
                continue
            if k_low.endswith("href") or k_low in {"src", "poster", "data"}:
                if _is_external_non_xmlns_url(attr_v):
                    violations.append(f"{elem.tag} {attr_k}={attr_v!r}")
            if k_low == "style" and attr_v:
                for m in CSS_URL_RE.finditer(attr_v):
                    if _is_external_non_xmlns_url(m.group(2)):
                        violations.append(f"style url({m.group(2)!r})")
        if elem.tag.lower().endswith("style") and elem.text:
            css_clean = CSS_COMMENT_RE.sub(" ", elem.text)
            for m in CSS_URL_RE.finditer(css_clean):
                if _is_external_non_xmlns_url(m.group(2)):
                    violations.append(f"<style> url({m.group(2)!r})")
            for m in CSS_IMPORT_RE.finditer(css_clean):
                if _is_external_non_xmlns_url(m.group(2)):
                    violations.append(f"<style> @import {m.group(2)!r}")
    assert not violations, f"{path}: external URLs found in SVG: {violations}"
    return root


def _load_json(data_or_path: dict | Path) -> tuple[dict, str]:
    if isinstance(data_or_path, Path):
        assert data_or_path.is_file(), f"Missing JSON file: {data_or_path}"
        data = json.loads(data_or_path.read_text(encoding="utf-8"))
        label = str(data_or_path)
    else:
        data = data_or_path
        label = "<dict>"
    assert isinstance(data, dict), f"{label}: expected JSON object, got {type(data).__name__}"
    return data, label


def validate_chiasm_invariants(
    data_or_path: dict | Path,
    require_contract: bool = True,
    require_sha256: bool = True,
) -> dict:
    """Validate fieldglass-causal-chiasm/v1 invariants without coupling to internal keys."""
    data, label = _load_json(data_or_path)
    if require_contract:
        assert data.get("contract") == "fieldglass-causal-chiasm/v1", (
            f"{label}: expected contract 'fieldglass-causal-chiasm/v1', got {data.get('contract')!r}"
        )
    assert data.get("executed") is False, f"{label}: executed must be False, got {data.get('executed')!r}"
    assert data.get("sentience_claimed") is False, (
        f"{label}: sentience_claimed must be False, got {data.get('sentience_claimed')!r}"
    )
    tokens = data.get("tokens_used")
    assert type(tokens) is int and tokens == 0, (
        f"{label}: tokens_used must be int 0, got {tokens!r} ({type(tokens).__name__})"
    )
    if require_sha256 or "report_sha256" in data:
        sha = data.get("report_sha256")
        assert isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha), (
            f"{label}: report_sha256 must be 64 lowercase hex chars, got {sha!r}"
        )
    return data


def _check_nonclinical_text(text: str, label: str) -> None:
    assert NONCLINICAL_REQUIRED_RE.search(text), (
        f"{label}: missing explicit simulated / educational / non-clinical framing"
    )
    for m in CLINICAL_CLAIM_RE.finditer(text):
        prefix = text[max(0, m.start() - 60) : m.start()]
        # Split on clause/sentence delimiters so earlier negation does not mask a later claim.
        clause_prefix = re.split(r"[,.;:!?\n]", prefix)[-1]
        if not NEGATION_PREFIX_RE.search(clause_prefix):
            raise AssertionError(
                f"{label}: unnegated clinical certification/diagnostic claim found: {m.group(0)!r}"
            )
    assert not re.search(r'"clinical_use"\s*:\s*true', text, re.I), (
        f"{label}: 'clinical_use: true' forbidden"
    )
    assert not re.search(r'"clinical_certification_claimed"\s*:\s*true', text, re.I), (
        f"{label}: 'clinical_certification_claimed: true' forbidden"
    )


def validate_nonclinical_framing(
    data_or_path: dict | Path | None = None,
    text: str | None = None,
    label: str = "content",
) -> dict | None:
    """Validate strict simulated/educational/non-clinical framing on JSON flags and/or text."""
    loaded: dict | None = None
    if data_or_path is not None:
        loaded, src_label = _load_json(data_or_path)
        assert loaded.get("clinical_use") is False, (
            f"{src_label}: clinical_use must be False, got {loaded.get('clinical_use')!r}"
        )
        assert loaded.get("educational_simulation_only") is True, (
            f"{src_label}: educational_simulation_only must be True, got {loaded.get('educational_simulation_only')!r}"
        )
        assert loaded.get("clinical_certification_claimed") is False, (
            f"{src_label}: clinical_certification_claimed must be False, got {loaded.get('clinical_certification_claimed')!r}"
        )
        disc = loaded.get("disclaimer")
        assert isinstance(disc, str) and len(disc.strip()) >= 15, (
            f"{src_label}: non-empty disclaimer (>=15 chars) required, got {disc!r}"
        )
        _check_nonclinical_text(disc, f"{src_label}[disclaimer]")
    if text is not None:
        _check_nonclinical_text(text, label)
    return loaded


def validate_py37_win7_script(
    path_or_source: Path | str,
    require_loopback: bool = True,
    allowed_local_modules: frozenset[str] = frozenset(),
) -> ast.Module:
    """Validate Python 3.7+ Win7 compatibility: AST, annotations, debug f-strings, stdlib-only, no ANSI, loopback."""
    if isinstance(path_or_source, Path):
        assert path_or_source.is_file(), f"Missing Python script: {path_or_source}"
        raw_bytes = path_or_source.read_bytes()
        label = str(path_or_source)
    else:
        raw_bytes = path_or_source.encode("utf-8")
        label = "<source>"

    for bad_byte, desc in ((b"\x1b", "ESC 0x1b"), (b"\x9b", "CSI 0x9b")):
        assert bad_byte not in raw_bytes, f"{label}: raw ANSI byte {desc} forbidden"

    src = raw_bytes.decode("utf-8")
    try:
        tree = ast.parse(src, filename=label, feature_version=(3, 7))
    except SyntaxError as exc:
        raise AssertionError(f"{label}: fails Python 3.7 AST parse: {exc}") from exc

    has_future_annotations = any(
        isinstance(stmt, ast.ImportFrom)
        and stmt.module == "__future__"
        and any(alias.name == "annotations" for alias in stmt.names)
        for stmt in tree.body
    )

    errors: list[str] = []
    type_union_names = frozenset(
        {
            "int",
            "str",
            "float",
            "bytes",
            "bytearray",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
            "frozenset",
            "object",
            "type",
            "complex",
            "memoryview",
            "range",
            "slice",
            "Exception",
            "BaseException",
        }
    )
    host_var_tokens = ("host", "addr", "bind", "ip", "listen", "server", "endpoint")
    server_call_names = frozenset(
        {
            "HTTPServer",
            "ThreadingHTTPServer",
            "TCPServer",
            "ThreadingTCPServer",
            "_ThreadingHTTPServer",
            "make_server",
            "bind",
            "serve",
        }
    )

    def _is_type_expr(node: ast.AST) -> bool:
        if isinstance(node, ast.Constant) and node.value is None:
            return True
        if isinstance(node, ast.Name):
            return node.id in type_union_names or (len(node.id) > 0 and node.id[0].isupper())
        if isinstance(node, ast.Attribute):
            return node.attr in type_union_names or (len(node.attr) > 0 and node.attr[0].isupper())
        if isinstance(node, ast.Subscript):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return _is_type_expr(node.left) or _is_type_expr(node.right)
        return False

    class _Py37Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.has_loopback_const = False
            self.wildcard_vars: set[str] = set()
            self._skip_loopback_const_ids: set[int] = set()

        def _is_wildcard_expr(self, node: ast.AST | None) -> bool:
            if node is None:
                return False
            if isinstance(node, ast.Constant) and node.value == "0.0.0.0":
                return True
            if isinstance(node, ast.Name) and node.id in self.wildcard_vars:
                return True
            return False

        def _inspect_annotation(self, ann: ast.AST | None, ctx_name: str) -> None:
            if ann is None:
                return
            for sub in ast.walk(ann):
                if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr):
                    errors.append(f"PEP 604 `|` union in {ctx_name} annotation (line {sub.lineno})")
                if not has_future_annotations and isinstance(sub, ast.Subscript):
                    if isinstance(sub.value, ast.Name) and sub.value.id in PEP585_BUILTIN_GENERICS:
                        errors.append(
                            f"PEP 585 `{sub.value.id}[...]` in {ctx_name} without postponed annotations (line {sub.lineno})"
                        )

        def visit_Expr(self, node: ast.Expr) -> None:
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                self._skip_loopback_const_ids.add(id(node.value))
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            for arg in (*node.args.args, *node.args.kwonlyargs):
                self._inspect_annotation(arg.annotation, f"arg {arg.arg}")
            if node.args.vararg:
                self._inspect_annotation(node.args.vararg.annotation, f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                self._inspect_annotation(node.args.kwarg.annotation, f"**{node.args.kwarg.arg}")
            self._inspect_annotation(node.returns, f"return of {node.name}")
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            for arg in (*node.args.args, *node.args.kwonlyargs):
                self._inspect_annotation(arg.annotation, f"arg {arg.arg}")
            if node.args.vararg:
                self._inspect_annotation(node.args.vararg.annotation, f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                self._inspect_annotation(node.args.kwarg.annotation, f"**{node.args.kwarg.arg}")
            self._inspect_annotation(node.returns, f"return of {node.name}")
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            self._inspect_annotation(node.annotation, "AnnAssign")
            if self._is_wildcard_expr(node.value) and isinstance(node.target, ast.Name):
                self.wildcard_vars.add(node.target.id)
                if any(tok in node.target.id.lower() for tok in host_var_tokens):
                    errors.append(f"Wildcard host assignment {node.target.id}='0.0.0.0' forbidden (line {node.lineno})")
            self.generic_visit(node)

        def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
            for val in node.values:
                if isinstance(val, ast.FormattedValue):
                    fv_seg = ast.get_source_segment(src, val) or ""
                    expr_seg = ast.get_source_segment(src, val.value) or ""
                    # In f"{x=}" or f"{(a==1)=:.2f}", '=' appears after expr_seg before ':!/}'
                    if expr_seg and expr_seg in fv_seg:
                        tail = fv_seg.split(expr_seg, 1)[1]
                        before_fmt = re.split(r"[:!}]", tail, maxsplit=1)[0]
                        if "=" in before_fmt:
                            errors.append(f"Python 3.8+ debug f-string `=` specifier (line {val.lineno})")
            self.generic_visit(node)

        def visit_Constant(self, node: ast.Constant) -> None:
            if isinstance(node.value, str):
                if "\x1b" in node.value or "\x9b" in node.value:
                    errors.append(f"ANSI escape character in string literal (line {node.lineno})")
                if re.search(r"\\(?:x1b|033|u001b|x9b)", node.value, re.I):
                    errors.append(f"Escaped ANSI sequence in string literal (line {node.lineno})")
                if id(node) not in self._skip_loopback_const_ids:
                    if "127.0.0.1" in node.value or node.value.strip().lower() == "localhost":
                        self.has_loopback_const = True
            self.generic_visit(node)

        def visit_Tuple(self, node: ast.Tuple) -> None:
            if len(node.elts) == 2 and self._is_wildcard_expr(node.elts[0]):
                errors.append(f"Wildcard bind tuple ('0.0.0.0', ...) forbidden (line {node.lineno})")
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            if self._is_wildcard_expr(node.value):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        self.wildcard_vars.add(tgt.id)
                        if any(tok in tgt.id.lower() for tok in host_var_tokens):
                            errors.append(f"Wildcard host assignment {tgt.id}='0.0.0.0' forbidden (line {node.lineno})")
                    elif isinstance(tgt, ast.Attribute) and any(tok in tgt.attr.lower() for tok in host_var_tokens):
                        errors.append(f"Wildcard host attribute {tgt.attr}='0.0.0.0' forbidden (line {node.lineno})")
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if isinstance(node.func, ast.Name) and node.func.id in {"isinstance", "issubclass"} and len(node.args) >= 2:
                for sub in ast.walk(node.args[1]):
                    if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr):
                        if _is_type_expr(sub.left) or _is_type_expr(sub.right):
                            errors.append(
                                f"PEP 604 `|` union inside {node.func.id}() call forbidden in Python 3.7 (line {sub.lineno})"
                            )

            if func_name in server_call_names:
                for arg in node.args:
                    if self._is_wildcard_expr(arg):
                        errors.append(f"Wildcard bind '0.0.0.0' in {func_name}() call forbidden (line {node.lineno})")
                for kw in node.keywords:
                    if self._is_wildcard_expr(kw.value):
                        errors.append(f"Wildcard bind '0.0.0.0' in {func_name}(..., {kw.arg}=...) forbidden (line {node.lineno})")
            for kw in node.keywords:
                if kw.arg and (
                    any(tok in kw.arg.lower() for tok in ("host", "addr", "bind"))
                    or (kw.arg == "default" and func_name == "add_argument")
                ):
                    if self._is_wildcard_expr(kw.value):
                        errors.append(f"Wildcard '0.0.0.0' in {func_name}({kw.arg}=...) forbidden (line {node.lineno})")
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                top = alias.name.split(".", 1)[0]
                if top in POST_37_STDLIB_MODULES or alias.name in POST_37_IMPORTLIB_SUBMODULES:
                    errors.append(f"Post-3.7 stdlib import {alias.name!r} (line {node.lineno})")
                elif top not in sys.stdlib_module_names and top not in allowed_local_modules:
                    errors.append(f"Non-stdlib / third-party import {alias.name!r} (line {node.lineno})")

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level and node.level > 0:
                return
            mod = node.module or ""
            top = mod.split(".", 1)[0]
            if top in POST_37_STDLIB_MODULES or mod in POST_37_IMPORTLIB_SUBMODULES:
                errors.append(f"Post-3.7 stdlib import from {mod!r} (line {node.lineno})")
            elif top not in sys.stdlib_module_names and top not in allowed_local_modules:
                errors.append(f"Non-stdlib / third-party import from {mod!r} (line {node.lineno})")
            if mod == "typing":
                for alias in node.names:
                    if alias.name in POST_37_TYPING_NAMES:
                        errors.append(f"Post-3.7 typing.{alias.name} (line {node.lineno})")

    visitor = _Py37Visitor()
    visitor.visit(tree)

    if require_loopback:
        if not visitor.has_loopback_const:
            errors.append("Expected explicit '127.0.0.1' / 'localhost' string constant in server AST")

    assert not errors, f"{label}: Windows 7 / Python 3.7 compatibility violations: {errors}"
    return tree


def _strip_js_comments_and_strings(js: str) -> str:
    """Strip // comments, /* */ comments, '...' / \"...\" literals, and /.../ regex literals cleanly."""
    out: list[str] = []
    n = len(js)
    i = 0
    prev_sig = ""  # last non-whitespace char or identifier-like marker for regex disambiguation
    regex_prev_chars = set("(=:,[!&|?{};\n")

    def _is_regex_start(idx: int) -> bool:
        if prev_sig == "" or prev_sig in regex_prev_chars:
            return True
        if prev_sig == "K":  # keyword like return / typeof / throw / case / in
            return True
        return False

    while i < n:
        ch = js[i]
        nxt = js[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "/":
            i += 2
            while i < n and js[i] != "\n":
                i += 1
            out.append(" ")
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < n and not (js[i] == "*" and js[i + 1] == "/"):
                i += 1
            i += 2
            out.append(" ")
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if js[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if js[i] == quote:
                    i += 1
                    break
                i += 1
            out.append('""')
            prev_sig = '"'
            continue
        if ch == "/" and _is_regex_start(i):
            i += 1
            in_class = False
            while i < n:
                c = js[i]
                if c == "\\" and i + 1 < n:
                    i += 2
                    continue
                if c == "[":
                    in_class = True
                elif c == "]" and in_class:
                    in_class = False
                elif c == "/" and not in_class:
                    i += 1
                    while i < n and js[i].isalpha():
                        i += 1
                    break
                elif c == "\n":
                    break
                i += 1
            out.append(" /rx/ ")
            prev_sig = "/"
            continue

        out.append(ch)
        if not ch.isspace():
            if ch.isalnum() or ch == "_":
                # Check if ending a regex-preceding keyword
                j = len(out) - 1
                word_chars: list[str] = []
                while j >= 0 and (out[j].isalnum() or out[j] == "_"):
                    word_chars.append(out[j])
                    j -= 1
                word = "".join(reversed(word_chars))
                if word in {"return", "typeof", "throw", "case", "in", "delete", "void", "else"}:
                    prev_sig = "K"
                else:
                    prev_sig = "I"
            else:
                prev_sig = ch
        elif ch == "\n":
            if prev_sig not in {"I", ")", "]"}:
                prev_sig = "\n"
        i += 1
    return "".join(out)


def _check_js_compile_node(code: str, label: str) -> None:
    node_bin = _find_node_bin()
    js_runner = "const fs=require('fs'), vm=require('vm'); new vm.Script(fs.readFileSync(0,'utf8'));"
    proc = subprocess.run(
        [node_bin, "-e", js_runner],
        input=code,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, f"{label}: JS syntax error in Node vm.Script:\n{proc.stderr}"


def _scan_es6_object_literals(stripped: str, expr_start: bool = False) -> list[str]:
    """Scan comment/string-stripped JS for ES6+ computed property keys, shorthand properties, and shorthand methods."""
    findings: list[str] = []
    n = len(stripped)
    i = 0
    prev_tok = "=" if expr_start else ""
    ternary_depth = 0
    obj_prev_tokens = {"=", "(", "[", ",", "?", "?:", "&&", "||", "!", "=>", "return", "throw", "yield"}

    def _find_matching_brace(start_idx: int) -> int:
        depth = 0
        j = start_idx
        while j < n:
            c = stripped[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return j
            j += 1
        return -1

    def _split_top_level_entries(body: str) -> list[str]:
        entries: list[str] = []
        buf: list[str] = []
        p_d = 0
        b_d = 0
        c_d = 0
        for ch in body:
            if ch == "(":
                p_d += 1
            elif ch == ")" and p_d > 0:
                p_d -= 1
            elif ch == "[":
                b_d += 1
            elif ch == "]" and b_d > 0:
                b_d -= 1
            elif ch == "{":
                c_d += 1
            elif ch == "}" and c_d > 0:
                c_d -= 1
            elif ch == "," and p_d == 0 and b_d == 0 and c_d == 0:
                entries.append("".join(buf))
                buf = []
                continue
            buf.append(ch)
        entries.append("".join(buf))
        return entries

    def _find_top_level_colon(entry: str) -> int:
        p_d = 0
        b_d = 0
        c_d = 0
        for idx, ch in enumerate(entry):
            if ch == "(":
                p_d += 1
            elif ch == ")" and p_d > 0:
                p_d -= 1
            elif ch == "[":
                b_d += 1
            elif ch == "]" and b_d > 0:
                b_d -= 1
            elif ch == "{":
                c_d += 1
            elif ch == "}" and c_d > 0:
                c_d -= 1
            elif ch == ":" and p_d == 0 and b_d == 0 and c_d == 0:
                return idx
        return -1

    while i < n:
        ch = stripped[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "{":
            is_obj = prev_tok in obj_prev_tokens
            if is_obj:
                end_idx = _find_matching_brace(i)
                if end_idx != -1:
                    inner = stripped[i + 1 : end_idx]
                    for raw_entry in _split_top_level_entries(inner):
                        entry = raw_entry.strip()
                        if not entry:
                            continue
                        colon_idx = _find_top_level_colon(entry)
                        if colon_idx != -1:
                            key_part = entry[:colon_idx].strip()
                            val_part = entry[colon_idx + 1 :].strip()
                            if key_part.startswith("["):
                                findings.append(f"ES6 computed property key ({key_part!r})")
                            findings.extend(_scan_es6_object_literals(val_part, expr_start=True))
                        else:
                            if entry.startswith("..."):
                                findings.append("ES6 spread property in object literal")
                            elif re.match(r"^(?:get|set)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*\(", entry):
                                findings.extend(_scan_es6_object_literals(entry, expr_start=False))
                            elif re.match(r"^(?:async\s+|\*\s*)?(?:[A-Za-z_$][A-Za-z0-9_$]*|\[[^\]]+\])\s*\(", entry):
                                findings.append(f"ES6 object shorthand/computed method ({entry[:32]!r})")
                            elif re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", entry):
                                findings.append(f"ES6 object shorthand property ({entry!r})")
                            else:
                                findings.extend(_scan_es6_object_literals(entry, expr_start=False))
                    i = end_idx + 1
                    prev_tok = "}"
                    continue
            prev_tok = "{"
            i += 1
            continue
        if ch == "?":
            ternary_depth += 1
            prev_tok = "?"
            i += 1
            continue
        if ch == ":" and ternary_depth > 0:
            ternary_depth -= 1
            prev_tok = "?:"
            i += 1
            continue
        if ch in (";", ")"):
            if ch == ";":
                ternary_depth = 0
            prev_tok = ch
            i += 1
            continue
        if stripped.startswith("=>", i):
            prev_tok = "=>"
            i += 2
            continue
        if stripped.startswith("&&", i) or stripped.startswith("||", i):
            prev_tok = stripped[i : i + 2]
            i += 2
            continue
        if ch.isalpha() or ch in ("_", "$"):
            start = i
            while i < n and (stripped[i].isalnum() or stripped[i] in ("_", "$")):
                i += 1
            prev_tok = stripped[start:i]
            continue
        prev_tok = ch
        i += 1

    return findings


def _scan_es5_js_violations(code: str, label: str) -> list[str]:
    errors: list[str] = []
    stripped = _strip_js_comments_and_strings(code)
    if "`" in stripped:
        errors.append(f"{label}: ES6 template literal backtick forbidden")
    for pat, desc in (
        (ES6_KEYWORD_RE, "ES6+ keyword"),
        (ES6_FETCH_RE, "ES6+ fetch()"),
        (ES6_ARROW_RE, "ES6 arrow function =>"),
        (ES6_SPREAD_RE, "ES6 spread/rest ..."),
        (ES6_OPTIONAL_CHAIN_RE, "ES2020 optional chaining ?."),
        (ES6_NULLISH_RE, "ES2020 nullish coalescing ??"),
        (ES6_EXP_RE, "ES2016 exponentiation **"),
        (ES6_FOR_OF_RE, "ES6 for..of loop"),
        (ES6_DESTRUCTURE_RE, "ES6 destructuring assignment"),
        (ES6_PARAM_DESTRUCTURE_RE, "ES6 parameter destructuring"),
        (ES6_DEFAULT_PARAM_RE, "ES6 default parameter"),
    ):
        m = pat.search(stripped)
        if m:
            errors.append(f"{label}: {desc} ({m.group(0)!r}) forbidden in Win7 ES5")
    for obj_msg in _scan_es6_object_literals(stripped):
        errors.append(f"{label}: {obj_msg} forbidden in Win7 ES5")
    return errors


def validate_es5_win7_html(path: Path, require_script: bool = True) -> ParsedHtmlAssets:
    """Validate ES5-only JS and IE8-IE11-safe CSS (no grid/clamp/CSS vars) in Win7 HTML/HTA."""
    assets = validate_html_document(path, min_visible_chars=60, forbid_external_anchors=True)

    scripts: list[tuple[str, str]] = [
        (f"{path}#script[{idx}]", body) for idx, body in enumerate(assets.scripts)
    ]
    for src_rel in assets.script_srcs:
        if src_rel.startswith(("data:", "http://", "https://", "//")):
            continue
        rel_path = (path.parent / src_rel.split("#", 1)[0].split("?", 1)[0]).resolve()
        assert rel_path.is_file(), f"{path}: referenced script {src_rel!r} not found at {rel_path}"
        scripts.append((str(rel_path), rel_path.read_text(encoding="utf-8")))

    if require_script:
        assert scripts, f"{path}: expected at least one ES5 <script> or linked .js file"

    js_errors: list[str] = []
    for label, code in scripts:
        _check_js_compile_node(code, label)
        js_errors.extend(_scan_es5_js_violations(code, label))

    for idx, (tag, attr_name, body) in enumerate(assets.event_handlers):
        evt_label = f"{path}#<{tag} {attr_name}>[{idx}]"
        wrapped = f"function __evt(event) {{\n{body}\n}}"
        _check_js_compile_node(wrapped, evt_label)
        js_errors.extend(_scan_es5_js_violations(body, evt_label))

    css_sources = list(assets.styles)
    for href_rel in assets.link_hrefs:
        if href_rel.lower().endswith(".css") and not _is_external_non_xmlns_url(href_rel):
            css_path = (path.parent / href_rel.split("#", 1)[0].split("?", 1)[0]).resolve()
            assert css_path.is_file(), f"{path}: referenced CSS {href_rel!r} missing"
            css_sources.append(css_path.read_text(encoding="utf-8"))

    css_errors: list[str] = []
    for idx, css in enumerate(css_sources):
        css_clean = CSS_COMMENT_RE.sub(" ", css)
        if re.search(r"display\s*:\s*(?:inline-)?grid\b", css_clean, re.I):
            css_errors.append(f"{path}#style[{idx}]: CSS Grid forbidden for Win7/IE compatibility")
        if re.search(r"\bclamp\s*\(", css_clean, re.I):
            css_errors.append(f"{path}#style[{idx}]: CSS clamp() forbidden for Win7/IE compatibility")
        if re.search(r"var\s*\(\s*--", css_clean, re.I):
            css_errors.append(f"{path}#style[{idx}]: CSS custom properties var(--*) forbidden for Win7/IE")

    all_errors = js_errors + css_errors
    assert not all_errors, f"{path}: Win7 ES5/CSS compatibility errors: {all_errors}"
    return assets


def validate_exiftool_no_gps(
    paths: list[Path] | tuple[Path, ...],
    pptx_extract_dir: Path | None = None,
) -> list[dict]:
    """Run exiftool -j -G1 -a -s across media files (and optional extracted .pptx media) and fail on GPS/location tags."""
    exiftool_bin = shutil.which("exiftool")
    assert exiftool_bin, "exiftool binary not found on PATH"

    scan_targets: list[Path] = []
    for p_idx, p in enumerate(paths):
        assert p.is_file(), f"Media path missing for exiftool scan: {p}"
        if p.suffix.lower() == ".pptx":
            assert pptx_extract_dir is not None, "pptx_extract_dir required when scanning .pptx"
            with zipfile.ZipFile(p, "r") as zf:
                for member in zf.namelist():
                    if member.startswith("ppt/media/") and not member.endswith("/"):
                        rel_parts = [part for part in Path(member).parts if part not in ("", ".", "..", "/")]
                        if not rel_parts:
                            continue
                        dest = (pptx_extract_dir / f"{p_idx}_{p.stem}").joinpath(*rel_parts)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(zf.read(member))
                        scan_targets.append(dest)
        else:
            scan_targets.append(p)

    if not scan_targets:
        return []

    records: list[dict] = []
    chunk_size = 100
    for start in range(0, len(scan_targets), chunk_size):
        chunk = scan_targets[start : start + chunk_size]
        proc = subprocess.run(
            [exiftool_bin, "-j", "-G1", "-a", "-s", *[str(x) for x in chunk]],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, f"exiftool failed ({proc.returncode}): {proc.stderr}"
        records.extend(json.loads(proc.stdout))

    violations: list[tuple[str, str, object]] = []
    for rec in records:
        src = str(rec.get("SourceFile", ""))
        for k, v in rec.items():
            if k == "SourceFile":
                continue
            if GPS_TAG_RE.search(k):
                violations.append((src, k, v))

    assert not violations, f"GPS/location metadata detected by exiftool: {violations}"
    return records


def validate_file_size_under_50mb(path: Path, limit_bytes: int = MAX_DOCS_BYTES) -> int:
    """Assert file exists and is strictly smaller than 50 MB (52,428,800 bytes)."""
    assert path.is_file(), f"Missing file for size check: {path}"
    size = path.stat().st_size
    assert size < limit_bytes, f"{path}: size {size} bytes >= limit {limit_bytes} bytes"
    return size


def _extract_shape_text(shape) -> list[str]:
    parts: list[str] = []
    if getattr(shape, "has_text_frame", False):
        txt = shape.text_frame.text.strip()
        if txt:
            parts.append(txt)
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                ct = cell.text.strip()
                if ct:
                    parts.append(ct)
    if getattr(shape, "shapes", None) is not None:
        for child in shape.shapes:
            parts.extend(_extract_shape_text(child))
    return parts


def validate_pptx_deck(
    pptx_path: Path,
    required_topics: list[str] | tuple[str, ...] | None = None,
    min_slides: int = 1,
) -> dict:
    """Parse .pptx via python-pptx, verify 16:9 geometry and topic coverage."""
    assert pptx_path.is_file(), f"Missing PPTX file: {pptx_path}"
    prs = Presentation(str(pptx_path))
    slide_count = len(prs.slides)
    assert slide_count >= min_slides, f"{pptx_path}: expected >= {min_slides} slides, got {slide_count}"
    ratio = float(prs.slide_width) / float(prs.slide_height)
    assert abs(ratio - (16.0 / 9.0)) < 0.05, (
        f"{pptx_path}: expected 16:9 geometry (~1.778), got {ratio:.4f}"
    )

    slide_texts: list[str] = []
    for slide in prs.slides:
        chunks: list[str] = []
        for shape in slide.shapes:
            chunks.extend(_extract_shape_text(shape))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            nt = slide.notes_slide.notes_text_frame.text.strip()
            if nt:
                chunks.append(nt)
        slide_texts.append("\n".join(chunks))

    full_text = "\n".join(slide_texts)
    if required_topics:
        low_full = full_text.lower()
        missing = [topic for topic in required_topics if topic.lower() not in low_full]
        assert not missing, f"{pptx_path}: missing required topics in slide text: {missing}"

    return {
        "slide_count": slide_count,
        "width": int(prs.slide_width),
        "height": int(prs.slide_height),
        "slide_texts": slide_texts,
        "full_text": full_text,
    }


def render_pptx_with_libreoffice(
    pptx_path: Path,
    out_dir: Path,
    min_std: float = 5.0,
) -> PptxRenderResult:
    """Convert .pptx -> PDF via LibreOffice (isolated UserInstallation) -> PNG via pdftoppm and verify non-blank slides."""
    lo_bin = shutil.which("libreoffice")
    ppm_bin = shutil.which("pdftoppm")
    assert lo_bin, "libreoffice binary not found on PATH"
    assert ppm_bin, "pdftoppm binary not found on PATH"
    assert pptx_path.is_file(), f"Missing PPTX file: {pptx_path}"

    prs = Presentation(str(pptx_path))
    expected_count = len(prs.slides)

    lo_profile = out_dir / "lo_profile"
    lo_out = out_dir / "lo_out"
    lo_profile.mkdir(parents=True, exist_ok=True)
    lo_out.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        [
            lo_bin,
            "--headless",
            "--nofirststartwizard",
            f"-env:UserInstallation=file://{lo_profile.resolve()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(lo_out.resolve()),
            str(pptx_path.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"LibreOffice conversion failed ({proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )

    pdf_path = lo_out / f"{pptx_path.stem}.pdf"
    assert pdf_path.is_file() and pdf_path.stat().st_size > 0, (
        f"Expected PDF output missing or empty at {pdf_path}"
    )

    ppm_prefix = lo_out / "slide"
    ppm_proc = subprocess.run(
        [ppm_bin, "-png", "-r", "100", str(pdf_path), str(ppm_prefix)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert ppm_proc.returncode == 0, f"pdftoppm failed ({ppm_proc.returncode}): {ppm_proc.stderr}"

    pngs = sorted(lo_out.glob("slide-*.png"))
    assert len(pngs) == expected_count, (
        f"{pptx_path}: rendered PNG count {len(pngs)} != slide count {expected_count}"
    )

    stds: list[float] = []
    blank_slides: list[tuple[int, float]] = []
    for idx, png_path in enumerate(pngs, start=1):
        with Image.open(png_path) as im:
            arr = np.asarray(im.convert("RGB"), dtype=np.float32)
        std = float(arr.std())
        stds.append(std)
        if std <= min_std:
            blank_slides.append((idx, std))

    assert not blank_slides, (
        f"{pptx_path}: blank/uniform rendered slides detected (std <= {min_std}): {blank_slides}"
    )
    return PptxRenderResult(
        pptx_path=pptx_path,
        pdf_path=pdf_path,
        slide_pngs=pngs,
        slide_stds=stds,
        slide_count=expected_count,
    )


_NODE_DOM_HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));

function makeClassList() {
  const set = new Set();
  return {
    add: function() { for (var i = 0; i < arguments.length; i++) set.add(arguments[i]); },
    remove: function() { for (var i = 0; i < arguments.length; i++) set.delete(arguments[i]); },
    toggle: function(c) { if (set.has(c)) { set.delete(c); return false; } set.add(c); return true; },
    contains: function(c) { return set.has(c); }
  };
}

function makeCtx2d() {
  const noop = function() {};
  return {
    fillStyle: '#000', strokeStyle: '#000', lineWidth: 1, font: '12px sans-serif',
    textAlign: 'left', textBaseline: 'alphabetic', globalAlpha: 1,
    beginPath: noop, closePath: noop, moveTo: noop, lineTo: noop, arc: noop,
    rect: noop, fillRect: noop, clearRect: noop, strokeRect: noop,
    fill: noop, stroke: noop, fillText: noop, strokeText: noop,
    save: noop, restore: noop, translate: noop, rotate: noop, scale: noop,
    setTransform: noop, setLineDash: noop, clip: noop,
    measureText: function(t) { return { width: String(t || '').length * 6 }; },
    createLinearGradient: function() { return { addColorStop: noop }; },
    createRadialGradient: function() { return { addColorStop: noop }; }
  };
}

function makeElem(tag, id) {
  const listeners = {};
  const attrs = {};
  const children = [];
  const el = {
    tagName: String(tag || 'DIV').toUpperCase(),
    id: id || '',
    value: '0',
    checked: false,
    disabled: false,
    innerHTML: '',
    textContent: '',
    innerText: '',
    className: '',
    width: 640,
    height: 360,
    style: {},
    dataset: {},
    children: children,
    childNodes: children,
    classList: makeClassList(),
    getContext: function(kind) { return kind === '2d' ? makeCtx2d() : {}; },
    appendChild: function(c) { children.push(c); return c; },
    removeChild: function(c) { return c; },
    insertBefore: function(c) { children.push(c); return c; },
    setAttribute: function(k, v) { attrs[k] = String(v); },
    getAttribute: function(k) { return Object.prototype.hasOwnProperty.call(attrs, k) ? attrs[k] : null; },
    removeAttribute: function(k) { delete attrs[k]; },
    addEventListener: function(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
    removeEventListener: function() {},
    dispatchEvent: function(ev) {
      const fns = listeners[ev && ev.type] || [];
      for (var i = 0; i < fns.length; i++) fns[i](ev);
    },
    querySelector: function() { return makeElem('div', ''); },
    querySelectorAll: function() { return []; },
    getElementsByTagName: function() { return []; },
    getElementsByClassName: function() { return []; },
    focus: function() {},
    blur: function() {},
    click: function() {},
    scrollIntoView: function() {},
    getBoundingClientRect: function() { return { left: 0, top: 0, width: 640, height: 360, right: 640, bottom: 360 }; }
  };
  return el;
}

const byId = {};
const docListeners = {};
const winListeners = {};
const storage = {};

const documentObj = {
  readyState: 'complete',
  body: makeElem('body', 'body'),
  head: makeElem('head', 'head'),
  documentElement: makeElem('html', 'html'),
  getElementById: function(id) {
    if (!Object.prototype.hasOwnProperty.call(byId, id)) byId[id] = makeElem('div', id);
    return byId[id];
  },
  querySelector: function(sel) {
    if (sel && sel.charAt(0) === '#') return documentObj.getElementById(sel.slice(1));
    return makeElem('div', '');
  },
  querySelectorAll: function() { return []; },
  getElementsByTagName: function() { return []; },
  getElementsByClassName: function() { return []; },
  createElement: function(tag) { return makeElem(tag, ''); },
  createElementNS: function(_ns, tag) { return makeElem(tag, ''); },
  createTextNode: function(txt) { return { nodeType: 3, textContent: String(txt || '') }; },
  addEventListener: function(ev, fn) { (docListeners[ev] = docListeners[ev] || []).push(fn); },
  removeEventListener: function() {}
};

const sandbox = {
  console: console,
  Math: Math,
  Date: Date,
  JSON: JSON,
  Array: Array,
  Object: Object,
  String: String,
  Number: Number,
  Boolean: Boolean,
  RegExp: RegExp,
  Error: Error,
  parseInt: parseInt,
  parseFloat: parseFloat,
  isNaN: isNaN,
  isFinite: isFinite,
  encodeURIComponent: encodeURIComponent,
  decodeURIComponent: decodeURIComponent,
  document: documentObj,
  navigator: { userAgent: 'FieldglassE2ENodeStub/1.0' },
  location: { href: 'http://127.0.0.1/', pathname: '/', search: '', hash: '' },
  localStorage: {
    getItem: function(k) { return Object.prototype.hasOwnProperty.call(storage, k) ? storage[k] : null; },
    setItem: function(k, v) { storage[k] = String(v); },
    removeItem: function(k) { delete storage[k]; }
  },
  sessionStorage: {
    getItem: function() { return null; },
    setItem: function() {},
    removeItem: function() {}
  },
  setTimeout: function() { return 1; },
  clearTimeout: function() {},
  setInterval: function() { return 1; },
  clearInterval: function() {},
  requestAnimationFrame: function() { return 1; },
  cancelAnimationFrame: function() {},
  alert: function() {},
  confirm: function() { return true; },
  addEventListener: function(ev, fn) { (winListeners[ev] = winListeners[ev] || []).push(fn); },
  removeEventListener: function() {},
  onload: null
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;

const ctx = vm.createContext(sandbox);
for (var i = 0; i < payload.scripts.length; i++) {
  vm.runInContext(payload.scripts[i], ctx, { filename: 'script_' + i + '.js' });
}
const domCbs = docListeners['DOMContentLoaded'] || [];
for (var j = 0; j < domCbs.length; j++) domCbs[j]({ type: 'DOMContentLoaded' });
const loadCbs = winListeners['load'] || [];
for (var k = 0; k < loadCbs.length; k++) loadCbs[k]({ type: 'load' });
if (typeof sandbox.onload === 'function') sandbox.onload({ type: 'load' });
if (payload.postEval) {
  vm.runInContext(payload.postEval, ctx, { filename: 'post_eval.js' });
}
"""


def validate_js_execution_node(
    scripts: list[str] | tuple[str, ...],
    post_eval_js: str = "",
    label: str = "js",
) -> None:
    """Execute extracted JS scripts inside Node vm.createContext with DOM stubs and assert zero runtime errors."""
    assert scripts, f"{label}: no scripts provided for Node execution"
    node_bin = _find_node_bin()
    payload = json.dumps({"scripts": list(scripts), "postEval": post_eval_js})
    proc = subprocess.run(
        [node_bin, "-e", _NODE_DOM_HARNESS],
        input=payload,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert proc.returncode == 0, (
        f"{label}: Node VM execution failed ({proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )


def extract_html_scripts_and_local_js(html_path: Path) -> list[str]:
    """Extract inline <script> blocks, local relative <script src> files, and inline on* event handlers from HTML/HTA."""
    assets = parse_html_assets(html_path.read_text(encoding="utf-8"))
    scripts = list(assets.scripts)
    for src_rel in assets.script_srcs:
        if _is_external_non_xmlns_url(src_rel) or src_rel.startswith("data:"):
            continue
        rel_path = (html_path.parent / src_rel.split("#", 1)[0].split("?", 1)[0]).resolve()
        assert rel_path.is_file(), f"{html_path}: missing linked script {src_rel!r}"
        scripts.append(rel_path.read_text(encoding="utf-8"))
    for idx, (_tag, _attr, body) in enumerate(assets.event_handlers):
        scripts.append(f"function __fieldglass_evt_{idx}(event) {{\n{body}\n}}")
    return scripts


def validate_relative_links_in_html(html_path: Path, docs_root: Path | None = None) -> int:
    """Verify every relative href/src/poster/data link inside an HTML/HTA file resolves on disk (and #fragments match)."""
    raw = html_path.read_text(encoding="utf-8")
    assets = parse_html_assets(raw)
    base_dir = html_path.parent
    checked = 0
    broken: list[str] = []

    all_refs = [val for _, _, val in assets.media_urls] + [val for _, _, val in assets.anchor_urls]
    for ref in all_refs:
        ref = ref.strip()
        if not ref or ref.startswith(("mailto:", "tel:", "javascript:", "data:", "blob:")):
            continue
        if _is_external_non_xmlns_url(ref):
            continue
        if ref.startswith("#"):
            frag = ref[1:]
            checked += 1
            if frag and frag not in assets.anchor_ids:
                broken.append(f"{ref} (missing anchor id)")
            continue
        path_part, _, frag = ref.partition("#")
        path_part = path_part.split("?", 1)[0]
        if not path_part:
            continue
        checked += 1
        target = (base_dir / path_part).resolve()
        if target.is_dir():
            if not (target / "index.html").is_file():
                broken.append(f"{ref} -> dir missing index.html")
                continue
        elif not target.is_file():
            broken.append(f"{ref} -> {target} not found")
            continue
        if docs_root is not None:
            try:
                target.relative_to(docs_root.resolve())
            except ValueError:
                broken.append(f"{ref} -> escapes docs_root ({target})")
        if frag and target.is_file() and target.suffix.lower() in {".html", ".htm", ".hta"}:
            target_assets = parse_html_assets(target.read_text(encoding="utf-8"))
            if frag not in target_assets.anchor_ids:
                broken.append(f"{ref} (missing #{frag} in {target.name})")

    assert not broken, f"{html_path}: broken relative links/anchors: {broken}"
    return checked


def free_loopback_port() -> int:
    """Allocate an ephemeral free TCP port on 127.0.0.1."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def launch_loopback_http_script(
    script_path: Path,
    timeout_sec: float = 10.0,
) -> tuple[subprocess.Popen[str], str, list[str]]:
    """Launch a loopback HTTP server script on an ephemeral 127.0.0.1 port and wait until HTTP 200."""
    import os
    import threading
    import time
    import urllib.request

    assert script_path.is_file(), f"Missing server script: {script_path}"
    help_proc = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    port = free_loopback_port()
    cmd = [sys.executable, str(script_path)]
    if help_proc.returncode == 0:
        if "--port" in help_proc.stdout:
            cmd.extend(["--port", str(port)])
        elif "-p" in help_proc.stdout:
            cmd.extend(["-p", str(port)])
        if "--host" in help_proc.stdout:
            cmd.extend(["--host", "127.0.0.1"])

    env = dict(os.environ)
    env["PORT"] = str(port)
    env["ZOE_HOSPITAL_PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        cmd,
        cwd=str(script_path.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    out_lines: list[str] = []
    discovered_port: list[int] = [port]

    def _drain_stdout() -> None:
        if proc.stdout is None:
            return
        for line in proc.stdout:
            out_lines.append(line)
            m = re.search(r"127\.0\.0\.1:(\d+)", line)
            if m:
                discovered_port[0] = int(m.group(1))

    t = threading.Thread(target=_drain_stdout, daemon=True)
    t.start()

    deadline = time.monotonic() + timeout_sec
    base_url = f"http://127.0.0.1:{discovered_port[0]}"
    ready = False
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        base_url = f"http://127.0.0.1:{discovered_port[0]}"
        try:
            with urllib.request.urlopen(base_url + "/", timeout=1.0) as resp:
                _ = resp.read()
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.15)

    if not ready:
        proc.terminate()
        try:
            _, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            _, stderr = proc.communicate(timeout=5)
        raise AssertionError(
            f"{script_path} did not serve HTTP 200 on {base_url} within {timeout_sec}s.\n"
            f"STDOUT: {''.join(out_lines)}\nSTDERR: {stderr}"
        )

    return proc, base_url, out_lines

