"""Shared pytest configuration, CLI options, and cached fixtures for Fieldglass E2E tests."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Callable

import pytest

E2E_DIR = Path(__file__).resolve().parent
REPO_ROOT = E2E_DIR.parent.parent
SRC_DIR = REPO_ROOT / "src"
SEC_TOOLS_SITE_PACKAGES = Path("/home/cowboy/security-tools/lib/python3.14/site-packages")

for _extra in (SRC_DIR, SEC_TOOLS_SITE_PACKAGES):
    _extra_str = str(_extra)
    if _extra.is_dir() and _extra_str not in sys.path:
        sys.path.insert(0, _extra_str)

from validators import PptxRenderResult, render_pptx_with_libreoffice  # noqa: E402


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--obs-root",
        action="store",
        default=None,
        help="Override Observatory repository root (defaults to FIELDGLASS_E2E_ROOT or /home/cowboy/fieldglass).",
    )


def pytest_configure(config: pytest.Config) -> None:
    markers = [
        "tier1: Tier 1 opaque-box happy-path feature coverage tests",
        "tier2: Tier 2 boundary, compatibility, media, size, and negative-input tests",
        "tier3: Tier 3 pairwise cross-module, link, archive, and regression tests",
        "tier4: Tier 4 end-to-end headless scenario tests",
        "selfcheck: Pre-M1-M4 positive and negative validator self-check tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


@pytest.fixture(scope="session")
def obs_root(request: pytest.FixtureRequest) -> Path:
    cli_val = request.config.getoption("--obs-root")
    env_val = os.environ.get("FIELDGLASS_E2E_ROOT")
    raw = cli_val or env_val or "/home/cowboy/fieldglass"
    return Path(raw).expanduser().resolve()


@pytest.fixture(scope="session")
def docs_root(obs_root: Path) -> Path:
    return obs_root / "docs"


@pytest.fixture(scope="session")
def pptx_render_cache(
    tmp_path_factory: pytest.TempPathFactory,
) -> Callable[[Path, float], PptxRenderResult]:
    """Session-cached LibreOffice PDF + pdftoppm slide PNG renderer using tmp_path_factory."""
    cache_root = tmp_path_factory.mktemp("pptx_lo_render_cache")
    cache: dict[tuple[str, int, int, float], PptxRenderResult] = {}

    def _render(pptx_path: Path, min_std: float = 5.0) -> PptxRenderResult:
        resolved = pptx_path.resolve()
        st = resolved.stat()
        key = (str(resolved), st.st_mtime_ns, st.st_size, float(min_std))
        if key not in cache:
            slot = cache_root / f"deck_{len(cache)}"
            slot.mkdir(parents=True, exist_ok=True)
            cache[key] = render_pptx_with_libreoffice(resolved, slot, min_std=min_std)
        return cache[key]

    return _render
