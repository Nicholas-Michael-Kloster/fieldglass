"""Self-check suite (@pytest.mark.selfcheck): paired positive & negative mutant tests for all validators."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import threading
import urllib.request
import zipfile

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Inches
import pytest

from fieldglass.showcase import make_range_handler
from validators import (
    extract_html_scripts_and_local_js,
    render_pptx_with_libreoffice,
    validate_chiasm_invariants,
    validate_es5_win7_html,
    validate_exiftool_no_gps,
    validate_file_size_under_50mb,
    validate_html_document,
    validate_js_execution_node,
    validate_nonclinical_framing,
    validate_pptx_deck,
    validate_py37_win7_script,
    validate_relative_links_in_html,
    validate_svg_document,
)

pytestmark = pytest.mark.selfcheck


def test_selfcheck_py37_win7_script_positive_and_mutants() -> None:
    valid_src = (
        "from http.server import HTTPServer, SimpleHTTPRequestHandler\n"
        "from typing import Dict, Optional\n\n"
        "def validate_loopback_host(h: str) -> bool:\n"
        "    return h == '127.0.0.1'\n\n"
        "def serve(host: str = '127.0.0.1', port: int = 8777) -> Optional[Dict[str, int]]:\n"
        "    # comment mentioning \\x1b should not trigger false positive\n"
        "    assert not validate_loopback_host('0.0.0.0')\n"
        "    msg = 'Simulated educational hospital kiosk ready'\n"
        "    return {'port': port} if host == '127.0.0.1' else None\n"
    )
    validate_py37_win7_script(valid_src, require_loopback=True)

    mutants = {
        "walrus_38": "host = '127.0.0.1'\nif (n := len(host)) > 0:\n    pass\n",
        "match_310": "host = '127.0.0.1'\nmatch host:\n    case '127.0.0.1':\n        pass\n",
        "bitor_310": "def f(x: int | str) -> None:\n    pass\n_h = '127.0.0.1'\n",
        "async_vararg_bitor_310": "async def f(*args: int | str) -> None:\n    pass\n_h = '127.0.0.1'\n",
        "async_kwarg_bitor_310": "async def f(**kwargs: int | str) -> None:\n    pass\n_h = '127.0.0.1'\n",
        "isinstance_bitor_310": "_h = '127.0.0.1'\nok = isinstance(1, int | str)\n",
        "issubclass_bitor_310": "_h = '127.0.0.1'\nok = issubclass(int, dict | list)\n",
        "pep585_39": "def f(items: list[int]) -> dict[str, int]:\n    return {}\n_h = '127.0.0.1'\n",
        "debug_fstring_38": "x = '127.0.0.1'\ns = f'{x=}'\n",
        "post37_stdlib": "import tomllib\n_h = '127.0.0.1'\n",
        "third_party_import": "import numpy\n_h = '127.0.0.1'\n",
        "raw_ansi": "_h = '127.0.0.1'\nmsg = '\x1b[31mRED'\n",
        "escaped_ansi": "_h = '127.0.0.1'\nmsg = r'\\x1b[31mRED'\n",
        "wildcard_bind": "srv = ('0.0.0.0', 8777)\n",
        "wildcard_host_var": "DEFAULT_HOST = '0.0.0.0'\n",
        "wildcard_bind_addr_evasion": (
            "from http.server import HTTPServer, SimpleHTTPRequestHandler\n"
            "bind_addr = '0.0.0.0'\n"
            "# default is not 127.0.0.1\n"
            "srv = HTTPServer((bind_addr, 8777), SimpleHTTPRequestHandler)\n"
        ),
        "comment_only_loopback": "# 127.0.0.1 only in comment\ndef hello():\n    return 'ok'\n",
        "missing_loopback": "def hello():\n    return 'ok'\n",
    }
    for name, src in mutants.items():
        with pytest.raises(AssertionError, match="."):
            validate_py37_win7_script(src, require_loopback=True)
            pytest.fail(f"Mutant {name!r} unexpectedly passed validate_py37_win7_script")


def test_selfcheck_es5_win7_html_positive_and_mutants(tmp_path: Path) -> None:
    valid_html = tmp_path / "valid_win7.html"
    valid_html.write_text(
        """<!doctype html>
<html>
<head>
<title>Zoe Hospital Win7 Educational Kiosk</title>
<style>
  body { background: #f4efe4; color: #1d2633; font-family: Tahoma, Arial, sans-serif; }
  table.panel { width: 100%; border-collapse: collapse; }
</style>
</head>
<body>
  <h1>Zoe Hospital Educational Sandbox</h1>
  <p>Simulated educational monitor only. Not for clinical use or patient diagnosis.</p>
  <button type="button" onclick="return computeStep(10, 20);">Step</button>
  <script>
    // ES6 tokens inside comment: let const => `tpl` class fetch()
    var fakeText = "let const => `tpl` class fetch()";
    var re = /['"]/;
    function computeStep(a, b) {
      return (a + b) / 2;
    }
    function helper(x, y, z) { return x + y + z; }
    var validObj = {
      a: helper(1, 2, 3),
      nested: true ? { k: 1 } : { k: 2 },
      get val() { return 42; }
    };
    var out = computeStep(10, 20);
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )
    validate_es5_win7_html(valid_html, require_script=True)

    bad_scripts = {
        "let_kw": "<script>let x = 1;</script>",
        "const_kw": "<script>const x = 1;</script>",
        "arrow_fn": "<script>var fn = function() { return [1].map(x => x + 1); };</script>",
        "template_lit": "<script>var s = `hello ${1}`;</script>",
        "class_kw": "<script>class Widget {}</script>",
        "fetch_call": "<script>function load(){ return fetch('/a'); }</script>",
        "syntax_err": "<script>var x = ;</script>",
        "param_destr_obj": "<script>function f({a}) { return a; }</script>",
        "param_destr_arr": "<script>function f(x, [a]) { return x; }</script>",
        "computed_prop": "<script>var k = 'x'; var o = { [k]: 1 };</script>",
        "shorthand_prop": "<script>function f(a) { return { a, b: 1 }; }</script>",
        "shorthand_method": "<script>var o = { m(x) { return x + 1; } };</script>",
        "onclick_tpl": '<script>var ok = 1;</script><button onclick="var s = `hi ${1}`;">Go</button>',
        "onclick_arrow": '<script>var ok = 1;</script><button onclick="var f = () => 1;">Run</button>',
        "onclick_syntax_err": '<script>var ok = 1;</script><button onclick="var x = ;">Err</button>',
    }
    for name, script_tag in bad_scripts.items():
        p = tmp_path / f"bad_{name}.html"
        p.write_text(
            f"<html><body><p>Simulated educational kiosk content for Windows 7 verification check.</p>{script_tag}</body></html>",
            encoding="utf-8",
        )
        with pytest.raises(AssertionError):
            validate_es5_win7_html(p, require_script=True)

    # Also verify extract_html_scripts_and_local_js + validate_js_execution_node catches onclick syntax error
    bad_evt_node = tmp_path / "bad_evt_node.html"
    bad_evt_node.write_text(
        '<html><body><p>Simulated educational content.</p><button onclick="var x = ;">Err</button></body></html>',
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        validate_js_execution_node(extract_html_scripts_and_local_js(bad_evt_node), label="bad_evt_node")

    bad_css = {
        "css_grid": "body { display: grid; }",
        "css_var": "body { color: var(--accent); }",
        "css_clamp": "h1 { font-size: clamp(1rem, 2vw, 2rem); }",
    }
    for name, css_rule in bad_css.items():
        p = tmp_path / f"bad_css_{name}.html"
        p.write_text(
            f"<html><head><style>{css_rule}</style></head>"
            "<body><p>Simulated educational kiosk content for Windows 7 verification check.</p>"
            "<script>var ok = 1;</script></body></html>",
            encoding="utf-8",
        )
        with pytest.raises(AssertionError):
            validate_es5_win7_html(p, require_script=True)


def test_selfcheck_exiftool_no_gps_positive_and_mutant(tmp_path: Path) -> None:
    clean_png = tmp_path / "clean.png"
    img = Image.new("RGB", (64, 64), (40, 80, 120))
    img.save(clean_png)
    validate_exiftool_no_gps([clean_png])

    gps_png = tmp_path / "gps_tainted.png"
    shutil.copyfile(clean_png, gps_png)
    subprocess.run(
        ["exiftool", "-overwrite_original", "-GPSLatitude=38.9", "-GPSLongitude=-94.6", str(gps_png)],
        capture_output=True,
        text=True,
        check=True,
    )
    with pytest.raises(AssertionError, match="GPS/location metadata"):
        validate_exiftool_no_gps([gps_png])

    # Verify embedded .pptx media GPS detection too
    pptx_clean = tmp_path / "clean.pptx"
    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6]).shapes.add_picture(str(clean_png), Inches(1), Inches(1))
    prs.save(str(pptx_clean))
    validate_exiftool_no_gps([pptx_clean], pptx_extract_dir=tmp_path / "ext_clean")

    pptx_dirty = tmp_path / "dirty.pptx"
    with zipfile.ZipFile(pptx_clean, "r") as zin, zipfile.ZipFile(pptx_dirty, "w") as zout:
        for item in zin.infolist():
            if item.filename.startswith("ppt/media/"):
                zout.writestr(item.filename, gps_png.read_bytes())
            else:
                zout.writestr(item, zin.read(item.filename))
    with pytest.raises(AssertionError, match="GPS/location metadata"):
        validate_exiftool_no_gps([pptx_dirty], pptx_extract_dir=tmp_path / "ext_dirty")

    # B10: Duplicate basename collision across ppt/media/sub1/img.png (GPS) and ppt/media/sub2/img.png (clean)
    pptx_collision = tmp_path / "collision.pptx"
    with zipfile.ZipFile(pptx_clean, "r") as zin, zipfile.ZipFile(pptx_collision, "w") as zout:
        for item in zin.infolist():
            if not item.filename.startswith("ppt/media/"):
                zout.writestr(item, zin.read(item.filename))
        zout.writestr("ppt/media/sub1/img.png", gps_png.read_bytes())
        zout.writestr("ppt/media/sub2/img.png", clean_png.read_bytes())
    with pytest.raises(AssertionError, match="GPS/location metadata"):
        validate_exiftool_no_gps([pptx_collision], pptx_extract_dir=tmp_path / "ext_collision")


def test_selfcheck_file_size_under_50mb_positive_and_sparse_mutant(tmp_path: Path) -> None:
    small = tmp_path / "small.bin"
    small.write_bytes(b"ok" * 100)
    assert validate_file_size_under_50mb(small) == 200

    oversized = tmp_path / "oversized_sparse.bin"
    with oversized.open("wb") as f:
        f.truncate(50 * 1024 * 1024)
    with pytest.raises(AssertionError, match="limit"):
        validate_file_size_under_50mb(oversized)


def test_selfcheck_html_cdn_svg_and_broken_link_positive_and_mutants(tmp_path: Path) -> None:
    sub = tmp_path / "page.html"
    sub.write_text("<html><body><h1 id='sec'>Target Section</h1><p>Valid linked target page content.</p></body></html>", encoding="utf-8")
    svg = tmp_path / "chart.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"><rect width="100" height="40" fill="#123"/></svg>',
        encoding="utf-8",
    )
    validate_svg_document(svg)

    good = tmp_path / "index.html"
    good.write_text(
        "<!doctype html><html><body>"
        "<h1>Observatory Specimen</h1>"
        "<p>Self-contained offline specimen documentation with local assets and valid links.</p>"
        "<img src='chart.svg' alt='chart' />"
        "<a href='page.html#sec'>Details</a>"
        "</body></html>",
        encoding="utf-8",
    )
    validate_html_document(good, min_visible_chars=40, forbid_external_anchors=True)
    assert validate_relative_links_in_html(good, docs_root=tmp_path) == 2

    cdn_html = tmp_path / "cdn.html"
    cdn_html.write_text(
        "<html><body><p>Valid long enough visible text content for HTML validator check.</p>"
        "<script src='https://cdn.example.com/lib.js'></script></body></html>",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="external CDN"):
        validate_html_document(cdn_html, min_visible_chars=20)

    css_cdn = tmp_path / "css_cdn.html"
    css_cdn.write_text(
        "<html><head><style>body{background:url('https://cdn.example.com/bg.png');}</style></head>"
        "<body><p>Valid long enough visible text content for HTML validator check.</p></body></html>",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="external CDN"):
        validate_html_document(css_cdn, min_visible_chars=20)

    # B9: srcset external CDN URL (even when local src is clean)
    srcset_cdn = tmp_path / "srcset_cdn.html"
    srcset_cdn.write_text(
        "<html><body><p>Valid long enough visible text content for srcset HTML validator check.</p>"
        "<img src='chart.svg' srcset='chart.svg 1x, https://cdn.example.com/hi.png 2x' alt='img' /></body></html>",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="external CDN"):
        validate_html_document(srcset_cdn, min_visible_chars=20)

    broken_link = tmp_path / "broken.html"
    broken_link.write_text(
        "<html><body><p>Valid long enough visible text content for link check.</p>"
        "<a href='missing.html'>Broken</a></body></html>",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="broken relative links"):
        validate_relative_links_in_html(broken_link, docs_root=tmp_path)


def test_selfcheck_chiasm_and_nonclinical_positive_and_mutants() -> None:
    valid_report = {
        "contract": "fieldglass-causal-chiasm/v1",
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
        "report_sha256": "a" * 64,
        "clinical_use": False,
        "educational_simulation_only": True,
        "clinical_certification_claimed": False,
        "disclaimer": "Strictly simulated and educational only; not for clinical use.",
    }
    validate_chiasm_invariants(valid_report)
    summary_variant = dict(valid_report, contract="fieldglass-r1-summary/v1")
    validate_chiasm_invariants(summary_variant, require_contract=False, require_sha256=False)
    validate_nonclinical_framing(
        data_or_path=valid_report,
        text="Simulated educational sandbox; not clinically certified and not for patient diagnosis.",
    )
    validate_nonclinical_framing(
        text="Simulated educational sandbox; NOT FDA cleared for clinical diagnosis."
    )

    for bad_patch in (
        {"executed": True},
        {"sentience_claimed": True},
        {"tokens_used": 1},
        {"tokens_used": False},
        {"report_sha256": "abc123"},
        {"contract": "wrong/v0"},
    ):
        mutated = dict(valid_report, **bad_patch)
        with pytest.raises(AssertionError):
            validate_chiasm_invariants(mutated)

    for bad_patch in (
        {"clinical_use": True},
        {"educational_simulation_only": False},
        {"clinical_certification_claimed": True},
        {"disclaimer": ""},
    ):
        mutated = dict(valid_report, **bad_patch)
        with pytest.raises(AssertionError):
            validate_nonclinical_framing(data_or_path=mutated)

    for bad_text in (
        "Simulated training tool that is FDA approved for patient diagnosis.",
        # B1: hyphenated non-* prefix must NOT act as negation
        "Simulated non-invasive hospital monitor that is FDA cleared for clinical diagnosis.",
        # B2: hyphenated FDA-cleared and phrase 'cleared for clinical use'
        "Simulated monitor; FDA-cleared for clinical use.",
        "Simulated monitor that is cleared for clinical use.",
        # B3: comma-separated earlier negation must NOT mask subsequent claim
        "Simulated tool, not for children, FDA cleared for clinical diagnosis.",
    ):
        with pytest.raises(AssertionError, match="unnegated clinical"):
            validate_nonclinical_framing(text=bad_text)


def test_selfcheck_pptx_libreoffice_pdftoppm_positive_and_blank_mutant(tmp_path: Path) -> None:
    good_pptx = tmp_path / "good.pptx"
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    tb = s1.shapes.add_textbox(Inches(1), Inches(1), Inches(10), Inches(3))
    tb.text_frame.text = "Fieldglass Observatory: MS-DOS, Flight Simulator, Simulated Medical Equipment, Software, Zoe Hospital"
    # Add a contrasting colored rectangle so rendered pixel std is clearly > 5.0
    img_p = tmp_path / "badge.png"
    im = Image.new("RGB", (200, 120), (20, 40, 80))
    d = ImageDraw.Draw(im)
    d.rectangle([20, 20, 180, 100], fill=(240, 195, 90))
    im.save(img_p)
    s1.shapes.add_picture(str(img_p), Inches(1), Inches(4))
    prs.save(str(good_pptx))

    validate_pptx_deck(good_pptx, required_topics=("MS-DOS", "Zoe Hospital"))
    res = render_pptx_with_libreoffice(good_pptx, tmp_path / "render_good", min_std=5.0)
    assert res.slide_count == 1 and res.slide_stds[0] > 5.0

    blank_pptx = tmp_path / "with_blank.pptx"
    prs2 = Presentation()
    prs2.slide_width = Inches(13.333)
    prs2.slide_height = Inches(7.5)
    prs2.slides.add_slide(prs2.slide_layouts[6]).shapes.add_picture(str(img_p), Inches(1), Inches(1))
    prs2.slides.add_slide(prs2.slide_layouts[6])  # Completely blank white slide
    prs2.save(str(blank_pptx))

    with pytest.raises(AssertionError, match="blank/uniform rendered slides"):
        render_pptx_with_libreoffice(blank_pptx, tmp_path / "render_blank", min_std=5.0)


def test_selfcheck_node_vm_and_ephemeral_range_http(tmp_path: Path) -> None:
    html_p = tmp_path / "sim.html"
    html_p.write_text(
        """<html><body><div id="out"></div>
        <script>
          function stepSim(v) { return v * 2 + 1; }
          document.getElementById('out').textContent = String(stepSim(21));
        </script></body></html>""",
        encoding="utf-8",
    )
    scripts = extract_html_scripts_and_local_js(html_p)
    validate_js_execution_node(scripts, post_eval_js="if (stepSim(5) !== 11) throw new Error('bad math');")

    with pytest.raises(AssertionError, match="Node VM execution failed"):
        validate_js_execution_node(["nonExistentFunctionCall();"])

    sample = tmp_path / "deck.bin"
    sample.write_bytes(bytes(range(256)) * 2)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_range_handler(tmp_path))
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/deck.bin", headers={"Range": "bytes=0-31"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 206
            assert resp.read() == bytes(range(32))
    finally:
        srv.shutdown()
        srv.server_close()
