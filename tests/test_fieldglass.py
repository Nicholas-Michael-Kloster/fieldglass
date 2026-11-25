"""Unit & integration tests for Fieldglass."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

from fieldglass.metrics import (
    TONAL_STATES,
    a_tau,
    causal_chiasm,
    luminance_to_8state,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)
from fieldglass.overlay import write_chiasm_svg
from fieldglass.plate import (
    clean_illumination,
    ink_to_braille_lines,
    laplacian_sharpness,
    perspective_deskew,
    render_braille_preview_png,
    trace_ink_to_svg,
)
from fieldglass.showcase import make_range_handler


def test_kloster_metrics_strict_inequality():
    # Exact boundary p_i == tau must be EXCLUDED (strict > tau)
    p = np.array([0.5, 0.25, 0.15, 0.10])
    assert a_tau(p, 0.10) == 3
    assert a_tau(p, 0.15) == 2
    assert a_tau(p, 0.50) == 0
    assert abs(shannon_h1(np.array([0.5, 0.5])) - 1.0) < 1e-9
    assert abs(renyi_h2(np.array([0.5, 0.5])) - 1.0) < 1e-9
    assert quartic_purity_m4(np.array([1.0, 0.0])) == 1.0


def test_causal_chiasm_and_filtration_tomography():
    past = normalize_dist({s: 1.0 + i for i, s in enumerate(TONAL_STATES)})
    future = normalize_dist({s: 2.0 + (7 - i) for i, s in enumerate(TONAL_STATES)})
    assert abs(sum(past.values()) - 1.0) < 1e-12
    ch = causal_chiasm(past, future, tau=0.10, horizon=5)
    assert ch["executed"] is False
    assert ch["sentience_claimed"] is False
    assert ch["presence_glyph"] in ("^_^", "??", "~")
    assert ch["effective_information_bits"] is not None

    eps = [past, future, past]
    tomo = persistent_filtration_tomography(eps, invariant_tau=0.12)
    assert tomo["episode_count"] == 3
    assert len(tomo["filtration_surface"]) == 3
    assert len(tomo["structural_invariants"]) >= 1


def test_luminance_to_8state_sums_to_one():
    p256 = np.ones(256, dtype=np.float64) / 256.0
    d = luminance_to_8state(p256)
    assert set(d.keys()) == set(TONAL_STATES)
    assert abs(sum(d.values()) - 1.0) < 1e-12


def test_plate_pipeline_end_to_end(tmp_path: Path):
    # Synthesize a botanical-like test drawing with uneven illumination gradient
    img = Image.new("RGB", (320, 420), (220, 210, 190))
    arr = np.asarray(img, dtype=np.float32)
    grad = np.linspace(0.75, 1.05, 320)[None, :, None]
    img = Image.fromarray((arr * grad).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.line([(160, 40), (160, 360)], fill=(25, 22, 20), width=5)
    d.ellipse([90, 140, 230, 240], outline=(25, 22, 20), width=4)

    assert laplacian_sharpness(img) > 0.0
    warped = perspective_deskew(img, [(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95)], out_size=(240, 320))
    assert warped.size == (240, 320)

    ink, archival, bw = clean_illumination(warped, sigma=18.0)
    assert ink.shape == (320, 240)
    assert archival.size == (240, 320) and bw.size == (240, 320)
    assert float(ink.max()) > 0.5

    svg_p = trace_ink_to_svg(ink, tmp_path / "specimen.svg", title="TEST SPECIMEN", vec_width=180)
    assert svg_p.is_file() and "<svg" in svg_p.read_text(encoding="utf-8")

    lines = ink_to_braille_lines(ink, cols=32)
    assert len(lines) > 8
    assert all(len(r) == 32 for r in lines)
    assert any(ord(ch) > 0x2800 for r in lines for ch in r)

    prev_p = render_braille_preview_png(lines, tmp_path / "braille.png")
    assert prev_p.is_file() and prev_p.stat().st_size > 1000


def test_chiasm_svg_and_range_server(tmp_path: Path):
    past = normalize_dist({s: 1.0 for s in TONAL_STATES})
    ch = causal_chiasm(past, past, tau=0.10)
    tomo = persistent_filtration_tomography([past, past], invariant_tau=0.08)
    svg = write_chiasm_svg(
        tmp_path / "ch.svg",
        title="TEST CHIASM",
        subtitle="unit test",
        chiasm=ch,
        tomography=tomo,
        per_sec_a004=[80, 90],
        per_sec_a010=[15, 20],
        nexus_sec=1,
    )
    assert svg.is_file() and "<svg" in svg.read_text(encoding="utf-8")

    # Test HTTP 206 Partial Content Range response
    sample = tmp_path / "clip.bin"
    sample.write_bytes(bytes(range(256)) * 4)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_range_handler(tmp_path))
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/clip.bin", headers={"Range": "bytes=10-29"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 206
            body = resp.read()
            assert len(body) == 20
            assert body == bytes(range(10, 30))
    finally:
        srv.shutdown()
        srv.server_close()
