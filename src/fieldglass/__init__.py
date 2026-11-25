"""Fieldglass — Phone-to-Telemetry & Specimen Field Instrument.

Turn any real-world video or photo into:
  1. Laplacian focus-scored 4K frames
  2. Perspective-deskewed, illumination-cleaned archival prints
  3. Contour-traced scalable vector SVGs & 2x4 Unicode Braille specimens
  4. Real-time Kloster A_tau(p_t) telemetry overlay videos
  5. Causal Chiasm & Persistent Filtration Tomography reports + SVGs
  6. Local loopback & USB-ADB interactive phone showcases (0 cloud tokens)
"""

from __future__ import annotations

from .metrics import (
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
from .plate import (
    clean_illumination,
    extract_sharpest_frame,
    image_to_braille,
    perspective_deskew,
    render_braille_preview_png,
    trace_ink_to_svg,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "TONAL_STATES",
    "a_tau",
    "shannon_h1",
    "renyi_h2",
    "quartic_purity_m4",
    "normalize_dist",
    "luminance_to_8state",
    "causal_chiasm",
    "persistent_filtration_tomography",
    "extract_sharpest_frame",
    "perspective_deskew",
    "clean_illumination",
    "trace_ink_to_svg",
    "image_to_braille",
    "render_braille_preview_png",
]
