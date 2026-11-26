"""Kloster A_tau(p) Operational Metacognition, Causal Chiasm, and Persistent Filtration Tomography.

Implements:
    A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]
alongside Shannon H1, Renyi H2, quartic purity M4^(1/4), Causal Chiasm decussation,
and Persistent Filtration Tomography F(t, tau) = A_tau(p_t).

Zero cloud tokens ($0.00), pure NumPy + Python stdlib, mathematical parity with
`guiai.gem.chiasm` in Nicholas-Michael-Kloster/zoe.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

CONTRACT = "fieldglass-causal-chiasm/v1"
DEFAULT_THRESHOLDS = (0.04, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50)

TONAL_STATES: tuple[str, ...] = (
    "deep_shadow",       # Luminance 0..31
    "ink_linework",      # Luminance 32..63
    "dark_midtone",      # Luminance 64..95
    "botanical_mid",     # Luminance 96..127
    "warm_sepia",        # Luminance 128..159
    "aged_paper",        # Luminance 160..191
    "bright_cream",      # Luminance 192..223
    "paper_highlight",   # Luminance 224..255
)


def a_tau(p: np.ndarray | Sequence[float], tau: float) -> int:
    """Strict superlevel-set accessible volume: A_tau(p) = sum_x 1[p(x) > tau]."""
    arr = np.asarray(p, dtype=np.float64)
    return int(np.sum(arr > float(tau)))


def shannon_h1(p: np.ndarray | Sequence[float]) -> float:
    """Shannon entropy H_1(p) in bits."""
    arr = np.asarray(p, dtype=np.float64)
    nz = arr[arr > 0]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def renyi_h2(p: np.ndarray | Sequence[float]) -> float:
    """Collision / Renyi order-2 entropy H_2(p) = -log2(sum p_i^2) in bits."""
    arr = np.asarray(p, dtype=np.float64)
    return float(-math.log2(max(float(np.sum(arr * arr)), 1e-12)))


def quartic_purity_m4(p: np.ndarray | Sequence[float]) -> float:
    """Quartic purity M_4^(1/4)(p) = (sum p_i^4)^(1/4)."""
    arr = np.asarray(p, dtype=np.float64)
    return float(np.sum(arr ** 4) ** 0.25)


def normalize_dist(d: Dict[str, float]) -> Dict[str, float]:
    """Normalize a state->weight dictionary so float64 values sum strictly to 1.0."""
    if not d:
        raise ValueError("distribution cannot be empty")
    clean = {k: max(float(v), 1e-9) for k, v in d.items()}
    total = sum(clean.values())
    norm = {k: v / total for k, v in clean.items()}
    max_k = max(norm, key=lambda k: norm[k])
    others = sum(v for k, v in norm.items() if k != max_k)
    norm[max_k] = 1.0 - others
    return norm


def luminance_to_8state(p256: np.ndarray) -> Dict[str, float]:
    """Aggregate a 256-bin luminance histogram into the 8 interpretable tonal states."""
    arr = np.asarray(p256, dtype=np.float64)
    if arr.shape[0] != 256:
        raise ValueError(f"expected 256-bin luminance distribution, got {arr.shape}")
    buckets = {
        name: float(arr[idx * 32 : (idx + 1) * 32].sum())
        for idx, name in enumerate(TONAL_STATES)
    }
    return normalize_dist(buckets)


def relative_entropy_bits(p: Dict[str, float], q: Dict[str, float]) -> float:
    """KL divergence D_KL(p || q) in bits over shared state keys."""
    p_n = normalize_dist(p)
    q_n = normalize_dist(q)
    total = 0.0
    for k, pv in p_n.items():
        qv = max(q_n.get(k, 1e-12), 1e-12)
        if pv > 0.0:
            total += pv * math.log2(pv / qv)
    return float(max(0.0, total))


def accessible_set(dist: Dict[str, float], tau: float) -> List[str]:
    """Return sorted states strictly exceeding threshold tau."""
    d = normalize_dist(dist)
    return sorted(k for k, v in d.items() if v > float(tau))


def causal_chiasm(
    past_likelihoods: Dict[str, float],
    future_forecast: Dict[str, float],
    tau: float = 0.10,
    horizon: int = 1,
) -> Dict[str, Any]:
    """Compute the Causal Chiasm Decussation Operator across past and future cones."""
    past = normalize_dist(past_likelihoods)
    future = normalize_dist(future_forecast)
    past_states = accessible_set(past, tau)
    future_states = accessible_set(future, tau)
    past_vol = len(past_states)
    future_vol = len(future_states)
    delta_vol = future_vol - past_vol

    ei_bits = relative_entropy_bits(future, past) if set(past) == set(future) else None
    future_boxed_in = (future_vol <= 1) and (past_vol > 1)
    if future_boxed_in:
        glyph = "??"
        meaning = "ambiguity alert: future boxed in while causal past remains unresolved"
    elif past_vol >= 2 and future_vol >= 2:
        glyph = "^_^"
        meaning = "corroborated chiasm: reversible future options preserved"
    else:
        glyph = "~"
        meaning = "still-looking: narrow repertoire"

    return {
        "contract": CONTRACT,
        "tau": float(tau),
        "horizon": int(horizon),
        "past_repertoire": past,
        "future_repertoire": future,
        "past_accessible_volume": past_vol,
        "past_accessible_states": past_states,
        "future_accessible_volume": future_vol,
        "future_accessible_states": future_states,
        "chiasm_shift": delta_vol,
        "effective_information_bits": round(ei_bits, 6) if ei_bits is not None else None,
        "future_boxed_in": future_boxed_in,
        "presence_glyph": glyph,
        "presence_meaning": meaning,
        "executed": False,
        "sentience_claimed": False,
    }


def persistent_filtration_tomography(
    episodes: Sequence[Dict[str, float]],
    thresholds: Iterable[float] = DEFAULT_THRESHOLDS,
    invariant_tau: float = 0.14,
) -> Dict[str, Any]:
    """Sweep tau across episode distributions to compute F(t, tau) = A_tau(p_t) & persistence P(x)."""
    if not episodes:
        raise ValueError("filtration tomography requires at least 1 episode distribution")
    tau_list = sorted({float(t) for t in thresholds})
    if not tau_list:
        raise ValueError("at least one threshold is required")

    norm_eps = [normalize_dist(ep) for ep in episodes]
    all_states = sorted({s for ep in norm_eps for s in ep})

    surface: List[List[int]] = []
    max_surviving: Dict[str, List[float]] = {s: [] for s in all_states}

    for ep in norm_eps:
        row = [len(accessible_set(ep, t)) for t in tau_list]
        surface.append(row)
        for s in all_states:
            pv = ep.get(s, 0.0)
            surv = [t for t in tau_list if pv > t]
            max_surviving[s].append(max(surv) if surv else 0.0)

    persistence_scores = {
        s: round(sum(vals) / len(norm_eps), 6) for s, vals in max_surviving.items()
    }
    invariants = sorted(s for s, sc in persistence_scores.items() if sc >= invariant_tau)
    transient = sorted(s for s, sc in persistence_scores.items() if sc < invariant_tau)

    return {
        "contract": CONTRACT,
        "episode_count": len(norm_eps),
        "thresholds": tau_list,
        "filtration_surface": surface,
        "persistence_scores": persistence_scores,
        "invariant_tau": float(invariant_tau),
        "structural_invariants": invariants,
        "transient_states": transient,
        "executed": False,
        "sentience_claimed": False,
    }
