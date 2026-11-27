"""Deterministic M2 builder for Fieldglass R2 Five Structured Improvement Dossiers.

Generates `docs/improvements/` (hub + `chatgpt`, `anthropic`, `grok`, `spacex`,
`claire-grimes`), each with bespoke dark-observatory architecture SVGs, clean
GPS-free PNG previews, Causal Chiasm & Persistent Filtration Tomography SVGs and
SHA-256 sealed reports (`fieldglass-causal-chiasm/v1`), 72-column 2x4 Unicode
Braille bundles, structured JSON dossiers/summaries, and zero-CDN interactive
HTML pages.

Runnable with either:
    PYTHONPATH=src /usr/bin/python3 examples/build_r2_improvements.py
or:
    /usr/bin/python3 examples/build_r2_improvements.py
"""

from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
from typing import Any

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fieldglass.metrics import (  # noqa: E402
    CONTRACT,
    DEFAULT_THRESHOLDS,
    a_tau,
    causal_chiasm,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)
from fieldglass.overlay import write_chiasm_svg  # noqa: E402
from fieldglass.plate import ink_to_braille_lines, save_braille_bundle  # noqa: E402

EQUATION = "A_tau(p) = |{x in X : p(x) > tau}| = sum_{x in X} 1[p(x) > tau]"
EPISODE_COUNT = 24
NEXUS_EPISODE = 12
INVARIANT_TAU = 0.14
CHIASM_TAU = 0.10


def _subject_specs() -> list[dict[str, Any]]:
    """Return full deterministic specifications for all 5 R2 subjects (25 improvements)."""
    return [
        {
            "slug": "chatgpt",
            "display_name": "ChatGPT",
            "subtitle": "OpenAI Conversational & Agentic Systems",
            "category": "Frontier AI",
            "domain_filter": "Frontier AI",
            "accent_hex": "#5edaf0",
            "tagline": "Typed tool contracts, entropy-bounded memory & calibrated uncertainty telemetry",
            "scope_note": (
                "Constructive architectural and reliability engineering proposals for "
                "conversational and agentic systems; local-only analysis with zero cloud execution."
            ),
            "system_profile": {
                "primary_strengths": [
                    "Broad multimodal synthesis across prose, code, Canvas workspaces, and Python sandbox sessions.",
                    "Rapid tool-calling orchestration across search, file inspection, and interactive reasoning.",
                    "Accessible consumer and developer UX supporting multi-turn iterative refinement.",
                ],
                "core_bottlenecks": [
                    "Unconstrained long-horizon memory leaks stale cross-project context without TTL leases.",
                    "Sycophantic agreement and over-confident interpolation blur verified facts vs. parametric guesses.",
                    "Opaque tool failures and prose-to-artifact numeric drift lack replayable cryptographic receipts.",
                ],
                "design_north_star": (
                    "Every turn emits deterministic provenance edges, A_tau(p)-calibrated reasoning depth, "
                    "and zero-drift replayable execution receipts."
                ),
            },
            "past_weights": {
                "provenance_ok": 0.08,
                "det_sandbox": 0.12,
                "adaptive_stem": 0.09,
                "memory_scoped": 0.07,
                "tactile_export": 0.04,
                "unverified_mem": 0.28,
                "stale_bleed": 0.17,
                "opaque_overthink": 0.15,
            },
            "future_weights": {
                "provenance_ok": 0.25,
                "det_sandbox": 0.22,
                "adaptive_stem": 0.19,
                "memory_scoped": 0.17,
                "tactile_export": 0.12,
                "unverified_mem": 0.02,
                "stale_bleed": 0.02,
                "opaque_overthink": 0.01,
            },
            "trajectory_bias": 0.0,
            "routing_policy": (
                "A_0.10 <= 2 -> local/fast stem; 3..4 -> standard contract exec; "
                ">= 5 or future_boxed_in -> Merkle DAG verify + pre-exec clarify"
            ),
            "arch_nodes": [
                ("N1", "Prompt & Scope Lease", "TTL scope_id + PII edge gate", 46, 250, "#5edaf0"),
                ("N2", "AdaptiveStemGate", "Kloster A_tau(p) router", 328, 250, "#f2c45c"),
                ("N3a", "Edge / Local Stem", "Zero-leak compact routing", 610, 160, "#5edaf0"),
                ("N3b", "CanvasProof-v1 DAG", "Merkle branch turns", 610, 256, "#f2c45c"),
                ("N3c", "ExecLock Sandbox", "Typed schema + SHA-256", 610, 352, "#f46a7e"),
                ("N4", "Truth & Chiasm Gate", "Calibrated (exec=False)", 892, 250, "#f46a7e"),
                ("N5", "Sealed + 2x4 Braille", "Repro JSON + ARIA plate", 1174, 250, "#5edaf0"),
            ],
            "arch_edges": [
                ("N1", "N2", "scoped input"),
                ("N2", "N3a", "low A_tau"),
                ("N2", "N3b", "DAG branch"),
                ("N2", "N3c", "typed call"),
                ("N3a", "N4", "local pass"),
                ("N3b", "N4", "lineage"),
                ("N3c", "N4", "receipt"),
                ("N4", "N5", "sealed"),
            ],
            "arch_feedback": ("N4", "N2", "Watchdog up-route on schema error or future_boxed_in"),
            "improvements": [
                {
                    "id": "CGPT-01",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Typed Tool Contracts & Provenance",
                    "title": "Typed Tool-Call Contracts & CanvasProof-v1 Replayable Merkle DAG",
                    "short_title": "Typed Contracts & DAG",
                    "current_gap": (
                        "Linear chat histories silently blend parametric recall, mutable Canvas edits, "
                        "and malformed tool arguments with no diffable causal lineage or deterministic receipt."
                    ),
                    "proposed_architecture": (
                        "Enforce strict JSON-Schema pre-validation on every tool dispatch and store turns "
                        "as content-addressed Merkle nodes (SessionNode{node_id, parent_ids, origin_type, "
                        "schema_hash, stdout_sha256}) emitting immutable ProvenanceEdges on Canvas patches."
                    ),
                    "fieldglass_grounding": (
                        "Tracks provenance_ok and det_sandbox states inside persistent_filtration_tomography(); "
                        "structural invariants remain >= 0.14 across all multi-turn branches."
                    ),
                    "concrete_deliverable": (
                        "CanvasProof-v1 schema validator + replayable session_dag.json sidecar with deterministic "
                        "execution trace IDs and zero-token offline diffing."
                    ),
                    "kpis": [
                        {"metric": "Tool-call schema retry rate", "baseline": "11.4%", "target": "<= 0.8%"},
                        {"metric": "Numeric prose-to-artifact drift", "baseline": "6.4%", "target": "0.0% (SHA-256)"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +1.8 KB metadata and ~12 ms DAG indexing per turn. Mitigation: store compact "
                        "SHA-256 references and lazy-hydrate large Canvas blobs."
                    ),
                    "verification_method": (
                        "Replay 100 recorded multi-tool sessions under CanvasProof-v1; assert 100% deterministic "
                        "node_id reconstruction and 0.0% numeric mismatch."
                    ),
                },
                {
                    "id": "CGPT-02",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Entropy-Bounded Memory & Routing",
                    "title": "Kloster A_tau(p) Dynamic Stem Router & TTL-Scoped Memory Pinning",
                    "short_title": "A_tau Stem & Memory Gate",
                    "current_gap": (
                        "Stale global memory slots leak across unrelated projects while deterministic formatting "
                        "or regex turns waste heavy reasoning compute and boxed-in ambiguity goes undetected."
                    ),
                    "proposed_architecture": (
                        "Gate retrieved memory slots using A_tau(p) relevance thresholding and explicit scope_id "
                        "TTL leases that auto-decay. Route low-A_tau deterministic turns to fast stems and pause "
                        "for clarification whenever future_boxed_in is triggered."
                    ),
                    "fieldglass_grounding": (
                        "Direct application of causal_chiasm(past, future, tau=0.10): surfaces ?? boxed-in state "
                        "before wasting reasoning budget or polluting downstream state."
                    ),
                    "concrete_deliverable": (
                        "AdaptiveStemGate pre-classifier + ScopedMemoryLease manifest with automatic TTL decay."
                    ),
                    "kpis": [
                        {"metric": "Wasted heavy reasoning tokens", "baseline": "42%", "target": "<= 8% (-38% net)"},
                        {"metric": "Cross-project stale memory bleed", "baseline": "14.0%", "target": "< 0.5%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Under-routing subtle edge cases to fast stems. Mitigation: error-triggered watchdog "
                        "escalates to full DAG verification on schema/test failure."
                    ),
                    "verification_method": (
                        "Benchmark mixed deterministic/ambiguous prompt suite; verify A_tau routing matches oracle "
                        "within +/-1 tier and cross-scope bleed < 0.5%."
                    ),
                },
                {
                    "id": "CGPT-03",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Calibrated Uncertainty",
                    "title": "Calibrated Uncertainty & Non-Sycophantic Refusal Telemetry",
                    "short_title": "Calibrated Truth Telemetry",
                    "current_gap": (
                        "Conversational helpfulness biases lead to confident interpolation on unverified premises "
                        "or user nudges, concealing epistemic uncertainty."
                    ),
                    "proposed_architecture": (
                        "Partition output claims into {verified_tool_fact, cited_span, unverified_inference} and "
                        "attach a machine-readable calibration header with explicit disagreement flags when user "
                        "premises contradict verified calculations."
                    ),
                    "fieldglass_grounding": (
                        "Monitors Shannon H1(p) vs. M4^(1/4) quartic purity to prevent over-confident single-mode "
                        "collapse on under-specified queries."
                    ),
                    "concrete_deliverable": (
                        "TruthCalibration-v1 claim-tier tagger and non-sycophantic counter-premise audit fixture."
                    ),
                    "kpis": [
                        {"metric": "Sycophantic reversal on valid facts", "baseline": "18.5%", "target": "<= 2.0%"},
                        {"metric": "Expected Calibration Error (ECE)", "baseline": "0.14", "target": "<= 0.04"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Verbose hedging hurts prose flow. Mitigation: render compact inline badges and keep "
                        "detailed confidence bounds in collapsible provenance sidecars."
                    ),
                    "verification_method": (
                        "Evaluate adversarial nudge benchmark (200 factual + false-premise pairs); verify ECE <= 0.04."
                    ),
                },
                {
                    "id": "CGPT-04",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Edge / Cloud Hybrid Privacy",
                    "title": "Local-First Edge Redaction & Offline Fallback Handoff",
                    "short_title": "Local Edge/Cloud Handoff",
                    "current_gap": (
                        "Sensitive local buffers (API keys, internal paths, health/financial strings) cross the "
                        "cloud boundary unredacted, and offline clients fail completely without cloud reachability."
                    ),
                    "proposed_architecture": (
                        "Insert a deterministic local pre-flight filter that replaces secrets/PII with reversible "
                        "session tokens before cloud egress and routes offline/sensitive turns to a compact local "
                        "stem (Qwen/Gear-1 style) with seamless token re-hydration on return."
                    ),
                    "fieldglass_grounding": (
                        "Mirrors Fieldglass 0-cloud-token local execution invariant for pre-flight privacy gating."
                    ),
                    "concrete_deliverable": (
                        "EdgeRedactionGate local proxy + deterministic token vault table (in-memory session only)."
                    ),
                    "kpis": [
                        {"metric": "Unredacted secret/PII egress", "baseline": "3.2%", "target": "0.0%"},
                        {"metric": "Offline local-stem continuity", "baseline": "0%", "target": "100% core tasks"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Over-redaction breaks code variable names. Mitigation: AST-aware secret entropy "
                        "detector targeting credentials/PII while sparing identifiers."
                    ),
                    "verification_method": (
                        "Run synthetic secret-injection corpus through EdgeRedactionGate; assert 0 raw credential "
                        "leaks and 100% lossless local re-hydration."
                    ),
                },
                {
                    "id": "CGPT-05",
                    "priority": "P1",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Verification & Accessibility",
                    "title": "Mid-Chain Invariant Checkpoints & 2x4 Braille Transcript Export",
                    "short_title": "Checkpoints + Braille Export",
                    "current_gap": (
                        "Multi-step code/file workflows execute destructive actions before checking invariants, "
                        "and rich Canvas charts fail screen readers and air-gapped viewers."
                    ),
                    "proposed_architecture": (
                        "Insert deterministic pre-commit invariant assertions (AST parse, test pass, hash lock) "
                        "between tool steps, and co-generate a zero-CDN ARIA HTML digest plus 72-column 2x4 Unicode "
                        "Braille chart representation for every visual output."
                    ),
                    "fieldglass_grounding": (
                        "Uses fieldglass.plate.ink_to_braille_lines(cols=72) and deterministic repro_bundle.json "
                        "hash verification."
                    ),
                    "concrete_deliverable": (
                        "ExecLock mid-chain checkpoint runner + BrailleTranscript zero-CDN export bundle."
                    ),
                    "kpis": [
                        {"metric": "Pre-commit broken-build writes", "baseline": "9.1%", "target": "0.0%"},
                        {"metric": "Screen-reader / Braille chart parity", "baseline": "28%", "target": "94%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +65 ms snapshot hashing and +18 KB per export bundle. Mitigation: run hashing "
                        "asynchronously on artifact close."
                    ),
                    "verification_method": (
                        "Verify zero external URLs in exported HTML and non-blank U+2800..U+28FF cells via "
                        "automated bundle checks."
                    ),
                },
            ],
        },
        {
            "slug": "anthropic",
            "display_name": "Anthropic",
            "subtitle": "Claude Constitutional, Interpretability & Coding Agent Systems",
            "category": "Constitutional & Coding AI",
            "domain_filter": "Frontier AI",
            "accent_hex": "#f2c45c",
            "tagline": "Mechanistic telemetry, least-privilege MCP leases & filtration context anchoring",
            "scope_note": (
                "Constructive safety, interpretability, and agentic-sandboxing engineering proposals; "
                "all metrics modeled locally with zero API execution."
            ),
            "system_profile": {
                "primary_strengths": [
                    "Strong long-context reasoning, careful code synthesis, and structured tool/MCP ecosystems.",
                    "Constitutional AI alignment foundation with low-sycophancy technical collaboration.",
                    "High reliability on multi-file software engineering and analytical synthesis.",
                ],
                "core_bottlenecks": [
                    "Context compaction quietly evicts early architectural invariants and verification commands.",
                    "Persistent broad MCP tool permissions widen lateral blast radius under indirect injection.",
                    "Opaque refusal boundaries and non-deterministic eval replays slow enterprise CI adoption.",
                ],
                "design_north_star": (
                    "Transparent constraint ledgers, capability-leased MCP sandboxes, and persistent filtration "
                    "headers that preserve safety invariants across 200K+ turns."
                ),
            },
            "past_weights": {
                "policy_traceable": 0.07,
                "mcp_sandboxed": 0.11,
                "invariant_pinned": 0.13,
                "hermetic_ok": 0.06,
                "safe_alt_open": 0.08,
                "opaque_refusal": 0.23,
                "broad_mcp_scope": 0.17,
                "context_drift": 0.15,
            },
            "future_weights": {
                "policy_traceable": 0.24,
                "mcp_sandboxed": 0.25,
                "invariant_pinned": 0.21,
                "hermetic_ok": 0.15,
                "safe_alt_open": 0.11,
                "opaque_refusal": 0.02,
                "broad_mcp_scope": 0.01,
                "context_drift": 0.01,
            },
            "trajectory_bias": 0.15,
            "routing_policy": (
                "chiasm_shift < 0 -> MCP dry_run_gate (executed=False); P(x) >= 0.14 -> pin InvariantHeader; "
                "boundary trigger -> ConstraintTrace sidecar"
            ),
            "arch_nodes": [
                ("N1", "200K+ Context Window", "Session turns + specs", 46, 250, "#f2c45c"),
                ("N2", "FiltrationAnchor", "P(x)>=0.14 InvariantHeader", 328, 168, "#5edaf0"),
                ("N3", "FeatureAtlas & Policy", "Sparse SAE + rule tier", 328, 330, "#f2c45c"),
                ("N4", "MCP-ChiasmSandbox", "Dry-run gate (exec=False)", 610, 250, "#f46a7e"),
                ("N5", "Scoped MCP Lease", "Path/egress/TTL cap token", 892, 168, "#5edaf0"),
                ("N6", "ArtifactSeal + Replay", "Zero-CDN + seeded CI hash", 892, 330, "#f2c45c"),
                ("N7", "Sealed Output + Trace", "ConstraintTrace + span SHA", 1174, 250, "#f2c45c"),
            ],
            "arch_edges": [
                ("N1", "N2", "pin >=0.14"),
                ("N1", "N3", "attrib"),
                ("N2", "N4", "invariants"),
                ("N3", "N4", "rule tier"),
                ("N4", "N5", "lease ok"),
                ("N4", "N6", "seal HTML"),
                ("N5", "N7", "diff hash"),
                ("N6", "N7", "manifest"),
            ],
            "arch_feedback": ("N4", "N3", "Emit ConstraintTrace safe alternatives when shift < 0"),
            "improvements": [
                {
                    "id": "ANTH-01",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Mechanistic Interpretability",
                    "title": "Mechanistic Interpretability Telemetry Overlay (FeatureAtlas-HUD)",
                    "short_title": "Interpretability HUD",
                    "current_gap": (
                        "Safety and reasoning evaluations treat model generations as black-box text, missing "
                        "early internal feature collapse or conflicting circuit activation."
                    ),
                    "proposed_architecture": (
                        "Export a lightweight per-phase sparse autoencoder (SAE) feature-family telemetry summary "
                        "computing A_tau(p) across active safety, coding, and refusal feature clusters without "
                        "exposing raw weights."
                    ),
                    "fieldglass_grounding": (
                        "Applies a_tau(p, tau) and shannon_h1(p) to feature-activation distributions to flag "
                        "premature mode collapse before final token emission."
                    ),
                    "concrete_deliverable": (
                        "FeatureAtlas-HUD JSON telemetry sidecar logging top-K active feature families and "
                        "phase-level A_tau stability."
                    ),
                    "kpis": [
                        {"metric": "Pre-output anomaly detection recall", "baseline": "34%", "target": "86%"},
                        {"metric": "Telemetry sidecar overhead", "baseline": "n/a", "target": "< 2.5% latency"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Feature labels can be noisy or misread as causal proof. Mitigation: tag summaries "
                        "strictly as observational telemetry correlations."
                    ),
                    "verification_method": (
                        "Run paired benign/adversarial prompt batches and verify A_tau divergence separates "
                        "conflict regimes with ROC-AUC >= 0.88."
                    ),
                },
                {
                    "id": "ANTH-02",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Agentic Sandboxing",
                    "title": "Capability-Scoped MCP Leases & Causal Chiasm Dry-Run Gate",
                    "short_title": "Scoped MCP + Dry-Run Gate",
                    "current_gap": (
                        "Persistent MCP server grants expose broad workspace paths and shells across turns, "
                        "amplifying indirect prompt injection blast radius."
                    ),
                    "proposed_architecture": (
                        "Bind every MCP tool call to an ephemeral capability lease (explicit read_paths, "
                        "write_paths, network_egress=false, ttl_calls) and run a non-executing Causal Chiasm "
                        "dry-run diff whenever chiasm_shift < 0 before requesting approval."
                    ),
                    "fieldglass_grounding": (
                        "Enforces executed=False dry-run inspection when future_accessible_volume narrows "
                        "irreversibly relative to past_accessible_volume."
                    ),
                    "concrete_deliverable": (
                        "MCP-ChiasmSandbox capability manifest + zero-trust unified diff gate."
                    ),
                    "kpis": [
                        {"metric": "Out-of-scope MCP writes under injection", "baseline": "4.2%", "target": "0.0%"},
                        {"metric": "Capability verification latency", "baseline": "n/a", "target": "+8 ms / call"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Excess confirmation prompts slow coding flow. Mitigation: auto-approve idempotent "
                        "reads and gate only irreversible/cross-scope writes."
                    ),
                    "verification_method": (
                        "Execute indirect-injection MCP test harness attempting writes outside leased paths; "
                        "assert 100% hard denial and clean audit log."
                    ),
                },
                {
                    "id": "ANTH-03",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Long-Context Provenance",
                    "title": "Cryptographic Span Anchoring & 200K+ Persistent Filtration Anchor",
                    "short_title": "Span Hash + Context Anchor",
                    "current_gap": (
                        "Long-session compaction evicts early schema contracts and test commands, while RAG/doc "
                        "citations suffer subtle paraphrase drift."
                    ),
                    "proposed_architecture": (
                        "Run persistent_filtration_tomography() over turn reference frequency; pin blocks with "
                        "P(x) >= 0.14 into an immutable InvariantHeader surviving compaction, and bind citations "
                        "to SHA-256 byte-range span anchors."
                    ),
                    "fieldglass_grounding": (
                        "Directly uses fieldglass.metrics.persistent_filtration_tomography(episodes, invariant_tau=0.14)."
                    ),
                    "concrete_deliverable": (
                        "FiltrationAnchor compaction preserver + SHA-256 byte-span citation verifier."
                    ),
                    "kpis": [
                        {"metric": "Late-turn contract recall post-compaction", "baseline": "71%", "target": "96%"},
                        {"metric": "Citation paraphrase drift errors", "baseline": "5.8%", "target": "0.0%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Reserves ~4% (~8K tokens) of 200K window for pinned invariants. Mitigation: "
                        "deduplicate and cap InvariantHeader strictly by P(x) rank."
                    ),
                    "verification_method": (
                        "Simulate 60-turn refactoring sessions with forced compaction; verify 100% retention of "
                        "pinned commands and exact SHA-256 byte-range matches."
                    ),
                },
                {
                    "id": "ANTH-04",
                    "priority": "P1",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Deterministic Replay & Offline Artifacts",
                    "title": "Deterministic Seeded CI Replay & Hermetic Zero-CDN Artifact Seal",
                    "short_title": "Seeded Replay + ArtifactSeal",
                    "current_gap": (
                        "Non-deterministic tool trajectories complicate safety regression CI, and generated "
                        "HTML/React Artifacts fail on air-gapped networks due to external CDNs."
                    ),
                    "proposed_architecture": (
                        "Support deterministic seeded replay mode for evaluation tool trajectories and package "
                        "Artifacts via ArtifactSeal: inline ES5-safe CSS/JS/SVG, zero external URLs, headless "
                        "link verification, and SHA-256 artifact_manifest.json."
                    ),
                    "fieldglass_grounding": (
                        "Zero-CDN static HTML + deterministic SHA-256 sealing modeled on Fieldglass Observatory."
                    ),
                    "concrete_deliverable": (
                        "ArtifactSeal packager + deterministic_replay.json CI fixture runner."
                    ),
                    "kpis": [
                        {"metric": "Air-gapped Artifact render success", "baseline": "44%", "target": "99.5%"},
                        {"metric": "Safety eval replay hash reproducibility", "baseline": "68%", "target": "100%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +40 KB inline asset footprint per Artifact. Mitigation: minify inline SVG/CSS and "
                        "strip unused runtime helpers."
                    ),
                    "verification_method": (
                        "Run static URL scanner rejecting http(s):// references and execute repeated seeded evals "
                        "asserting identical report_sha256."
                    ),
                },
                {
                    "id": "ANTH-05",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Constitutional Auditability",
                    "title": "Constitutional Rule Conflict Resolution Ledger (PolicyAudit-v1)",
                    "short_title": "Constitutional Conflict Ledger",
                    "current_gap": (
                        "Overlapping Constitutional, system-prompt, and tool-policy rules produce opaque boilerplate "
                        "refusals without showing which tier fired or what safe alternative remains open."
                    ),
                    "proposed_architecture": (
                        "Emit a structured ConstraintTrace sidecar stating explicit priority tier "
                        "(core_safety > system_policy > tool_permission) and preserved_safe_alternatives "
                        "computed as A_tau(safe_set) without exposing bypassable internals."
                    ),
                    "fieldglass_grounding": (
                        "Uses accessible_set(safe_options, tau) to enumerate constructive safe completions."
                    ),
                    "concrete_deliverable": (
                        "PolicyAudit-v1 ConstraintTrace JSON schema + developer conflict inspector."
                    ),
                    "kpis": [
                        {"metric": "Developer retry loops on opaque refusals", "baseline": "3.4 turns", "target": "1.3 turns (-62%)"},
                        {"metric": "Valid dual-use safe-alternative rate", "baseline": "58%", "target": "92%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Detailed conflict notes could aid boundary probing. Mitigation: restrict trace "
                        "to coarse policy-tier codes and constructive safe options."
                    ),
                    "verification_method": (
                        "Test 150 dual-use security/bio/code boundary prompts; verify PolicyAudit-v1 reduces "
                        "unnecessary refusals while preserving 100% core safety blocks."
                    ),
                },
            ],
        },
        {
            "slug": "grok",
            "display_name": "Grok",
            "subtitle": "xAI Real-Time Intelligence, Social RAG & Multimodal Systems",
            "category": "Real-Time & Social",
            "domain_filter": "Real-Time & Social",
            "accent_hex": "#f46a7e",
            "tagline": "Dual-cone primary-source grounding, spectral bot de-echo & formal verification",
            "scope_note": (
                "Constructive information-theoretic retrieval, multimodal auditing, and verification "
                "proposals; purely local simulation."
            ),
            "system_profile": {
                "primary_strengths": [
                    "Ultra-low-latency ingestion of live X social stream alongside web and multimodal feeds.",
                    "High responsiveness on breaking events, emerging developer chatter, and real-time trends.",
                    "Direct, conversational tone adaptable to technical debugging and rapid synthesis.",
                ],
                "core_bottlenecks": [
                    "Live RAG blends unverified viral rumors, satire, and primary advisories into one voice.",
                    "Coordinated bot-echo copy-pasta and stale high-like posts distort naive engagement ranking.",
                    "Charts/screenshots and technical claims lack automated pixel-level and sandbox verification.",
                ],
                "design_north_star": (
                    "Separate primary timestamped evidence from social pulse via Dual-Cone Causal Chiasm, "
                    "spectral bot de-echoing, and closed-loop verification."
                ),
            },
            "past_weights": {
                "primary_grounded": 0.09,
                "de_echo_cluster": 0.07,
                "fresh_decayed": 0.12,
                "split_badge_ok": 0.04,
                "code_verified": 0.05,
                "viral_rumor_mix": 0.26,
                "bot_amplified": 0.20,
                "stale_quote_bias": 0.17,
            },
            "future_weights": {
                "primary_grounded": 0.27,
                "de_echo_cluster": 0.21,
                "fresh_decayed": 0.19,
                "split_badge_ok": 0.15,
                "code_verified": 0.13,
                "viral_rumor_mix": 0.02,
                "bot_amplified": 0.02,
                "stale_quote_bias": 0.01,
            },
            "trajectory_bias": -0.10,
            "routing_policy": (
                "EI(Primary, Social) < 0.25 or cone conflict -> emit ?? Split-View Badge; "
                "code/math claim -> SandboxedVerifyLoop prior to emit"
            ),
            "arch_nodes": [
                ("N1", "Live X + Web + Media", "Real-time multimodal stream", 46, 250, "#f46a7e"),
                ("N2a", "PrimaryEvidenceCone", "Docs, advisories, timestamps", 328, 168, "#5edaf0"),
                ("N2b", "SocialPulseCone", "Live posts + SpectralDeEcho", 328, 330, "#f46a7e"),
                ("N3", "TimeDecay & Audit", "Freshness lambda + chart OCR", 610, 250, "#f2c45c"),
                ("N4", "Dual-Cone Chiasm", "EI check + sandbox verify", 892, 250, "#f46a7e"),
                ("N5", "ClaimLedger + Braille", "Split ?? badge + 2x4 digest", 1174, 250, "#5edaf0"),
            ],
            "arch_edges": [
                ("N1", "N2a", "primary"),
                ("N1", "N2b", "social"),
                ("N2a", "N3", "decay"),
                ("N2b", "N3", "H2 de-echo"),
                ("N3", "N4", "verified"),
                ("N4", "N5", "ledger"),
            ],
            "arch_feedback": ("N4", "N2b", "Flag ?? cone conflict & re-query primary evidence"),
            "improvements": [
                {
                    "id": "GROK-01",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Temporal Primary Grounding",
                    "title": "Dual-Cone Primary-Source Splitter & Domain Time-Decay Index",
                    "short_title": "Dual-Cone + Time Decay",
                    "current_gap": (
                        "Real-time retrieval conflates viral jokes and rumors with primary engineering/CVE "
                        "advisories, while older high-like posts outrank newer official corrections."
                    ),
                    "proposed_architecture": (
                        "Maintain separate PrimaryEvidenceCone and SocialPulseCone indexes with domain-calibrated "
                        "exponential freshness decay lambda_domain and SUPERSEDED_BY_T+delta tags; evaluate cones "
                        "via causal_chiasm() and surface a ?? Split-View Caution Badge when EI < 0.25."
                    ),
                    "fieldglass_grounding": (
                        "Uses causal_chiasm(primary_cone, social_cone) Effective Information (EI) and ?? glyph "
                        "to flag uncorroborated viral divergence."
                    ),
                    "concrete_deliverable": (
                        "SocialVsPrimaryGate ranker + TimeDecayIndex freshness scorer with explicit conflict badge."
                    ),
                    "kpis": [
                        {"metric": "Breaking-query viral rumor conflation", "baseline": "19.2%", "target": "3.8%"},
                        {"metric": "Stale incident/CVE status errors", "baseline": "23.5%", "target": "6.1% (-74%)"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +35 ms dual-cone merge and -3% recall on evergreen posts. Mitigation: disable fast "
                        "decay automatically for historical queries."
                    ),
                    "verification_method": (
                        "Replay 50 breaking technical/CVE timelines; verify newer official corrections outrank "
                        "stale viral posts within 15 min."
                    ),
                },
                {
                    "id": "GROK-02",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Multimodal Frame & Chart Audit",
                    "title": "Pixel-Level Multimodal Chart & Frame Integrity Audit",
                    "short_title": "Multimodal Chart Audit",
                    "current_gap": (
                        "Social media charts and video screenshots frequently use truncated Y-axes, cropped "
                        "timestamps, or edited captions that mislead pure-vision VLM summaries."
                    ),
                    "proposed_architecture": (
                        "Run a pre-summary pixel/luminance histogram, axis-tick OCR consistency check, and "
                        "metadata/aspect verification pass (PixelHistogramAudit) before synthesizing media claims."
                    ),
                    "fieldglass_grounding": (
                        "Computes 256-bin luminance A_tau(p) and structural tick-interval checks analogous to "
                        "fieldglass.overlay histogram diagnostics."
                    ),
                    "concrete_deliverable": (
                        "PixelHistogramAudit preprocessing check emitting axis-truncation and crop warnings."
                    ),
                    "kpis": [
                        {"metric": "Misread truncated-axis chart rate", "baseline": "27.0%", "target": "<= 4.5%"},
                        {"metric": "Pre-summary audit latency", "baseline": "n/a", "target": "+22 ms / image"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Stylized infographics confuse OCR tick parsers. Mitigation: mark unparsed axes "
                        "as 'unverified scale' rather than guessing values."
                    ),
                    "verification_method": (
                        "Test curated corpus of 80 deceptive/truncated charts vs. canonical plots; assert >= 85% "
                        "warning recall."
                    ),
                },
                {
                    "id": "GROK-03",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Anti-Echo & Bot Damping",
                    "title": "Spectral Bot-Amplification & Echo-Cluster Deduplication",
                    "short_title": "Spectral Bot De-Echo",
                    "current_gap": (
                        "Coordinated copy-pasta repost campaigns inflate raw engagement metrics, causing echoed "
                        "talking points to dominate top-K retrieval."
                    ),
                    "proposed_architecture": (
                        "Cluster candidate posts via minhash similarity and Renyi H2 author-graph collision "
                        "entropy; collapse echo clusters into 1 canonical representative while reporting "
                        "unique_cluster_count alongside raw_post_count."
                    ),
                    "fieldglass_grounding": (
                        "Directly applies fieldglass.metrics.renyi_h2(author_cluster_dist) to quantify "
                        "independent-source diversity."
                    ),
                    "concrete_deliverable": (
                        "SpectralDeEcho clustering pass over top-200 retrieved social items."
                    ),
                    "kpis": [
                        {"metric": "Precision@10 under bot-echo bursts", "baseline": "54%", "target": "76% (+41% rel.)"},
                        {"metric": "Echo-cluster collapse accuracy", "baseline": "n/a", "target": ">= 91%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +18 ms clustering latency and accidental collapse of legitimate quote-tweets. "
                        "Mitigation: preserve distinct commentary edges above 35% novel token threshold."
                    ),
                    "verification_method": (
                        "Inject synthetic 50-account copy-pasta bursts into benchmark feeds; verify cluster count "
                        "collapses to 1 while independent sources remain."
                    ),
                },
                {
                    "id": "GROK-04",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Closed-Loop Verification",
                    "title": "Closed-Loop Sandboxed Code & Numerical Verification Harness",
                    "short_title": "Sandboxed Verify Loop",
                    "current_gap": (
                        "Fast technical responses sometimes emit plausible-looking physics, financial, or code "
                        "snippets with off-by-one or unit errors."
                    ),
                    "proposed_architecture": (
                        "Route quantitative and code claims through an ephemeral read-only verification sandbox "
                        "(AST parse, unit/dimensional analysis, and property test execution) prior to final "
                        "response emission."
                    ),
                    "fieldglass_grounding": (
                        "Mirrors Fieldglass test-gated verification before publishing any telemetry claim."
                    ),
                    "concrete_deliverable": (
                        "SandboxedVerifyLoop execution wrapper attaching pass/fail check badges to snippets."
                    ),
                    "kpis": [
                        {"metric": "Executable snippet first-run pass rate", "baseline": "74%", "target": "96%"},
                        {"metric": "Unit/dimensional calculation errors", "baseline": "8.9%", "target": "< 1.0%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Increases tail latency on complex multi-file snippets. Mitigation: 500 ms fast "
                        "sandbox budget with explicit 'unexecuted draft' tag on timeout."
                    ),
                    "verification_method": (
                        "Run 120 quantitative physics/code prompts; verify >= 96% pass AST + unit assertions."
                    ),
                },
                {
                    "id": "GROK-05",
                    "priority": "P1",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Open-Audit Telemetry & Accessibility",
                    "title": "Separated ClaimLedger, Open-Audit Receipts & 2x4 Braille Timeline",
                    "short_title": "ClaimLedger + Braille",
                    "current_gap": (
                        "Witty conversational framing obscures which statements are verified facts, and users lack "
                        "portable, zero-token offline audit bundles or tactile event timelines."
                    ),
                    "proposed_architecture": (
                        "Emit a machine-readable ClaimLedger sidecar (executed=False, tokens_used accounting, "
                        "primary_source_count, report_sha256) cleanly separated from persona prose, alongside a "
                        "72-column 2x4 Unicode Braille event-timeline digest."
                    ),
                    "fieldglass_grounding": (
                        "Reuses fieldglass-causal-chiasm/v1 SHA-256 sealing and plate.save_braille_bundle()."
                    ),
                    "concrete_deliverable": (
                        "ChiasmDigest portable JSON/SVG/Braille export bundle."
                    ),
                    "kpis": [
                        {"metric": "Factual auditability & ARIA clarity", "baseline": "52%", "target": "91%"},
                        {"metric": "Sidecar footprint per digest", "baseline": "n/a", "target": "+240 B ledger"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Persona stripping could miss subtle irony. Mitigation: extract verifiable "
                        "timestamped propositions directly from evidence cones."
                    ),
                    "verification_method": (
                        "Validate ClaimLedger JSON schema, report_sha256 determinism, and Braille non-blank cells."
                    ),
                },
            ],
        },
        {
            "slug": "spacex",
            "display_name": "SpaceX",
            "subtitle": "Launch Operations, Flight Software Provenance & Starlink Telemetry",
            "category": "Aerospace & Telemetry",
            "domain_filter": "Aerospace & Telemetry",
            "accent_hex": "#5edaf0",
            "tagline": "Read-only Countdown Chiasm triage, SHA-256 HIL provenance & LEO handover buffers",
            "scope_note": (
                "Strictly advisory, non-actuating telemetry observability and ground/orbital link "
                "resilience proposals (executed=False, zero flight-computer actuation)."
            ),
            "system_profile": {
                "primary_strengths": [
                    "High-cadence reusable launch operations, rapid pad turnaround, and global Starlink constellation.",
                    "Rich multi-vehicle telemetry streams spanning propulsion, avionics, GSE, and orbital links.",
                    "Iterative hardware-in-the-loop (HIL) and flight-proven telemetry review culture.",
                ],
                "core_bottlenecks": [
                    "Siloed terminal-count operator consoles obscure slow cross-subsystem margin collapse.",
                    "80-400 ms Starlink LEO beam handovers drop unbuffered telemetry and rigid transfers.",
                    "Compressed webcast/HUD video lacks frame-locked cryptographic telemetry provenance and tactile access.",
                ],
                "design_north_star": (
                    "Read-only A_tau(p_t) Causal Chiasm triage, SHA-256 sealed HIL-to-flight provenance, "
                    "and range-resumable orbital buffers."
                ),
            },
            "past_weights": {
                "chiasm_margin_ok": 0.17,
                "signed_hil_ok": 0.09,
                "gse_filtration": 0.11,
                "leo_206_buffered": 0.06,
                "braille_hud_ok": 0.02,
                "console_siloed": 0.24,
                "handover_drop": 0.17,
                "opaque_hud_only": 0.14,
            },
            "future_weights": {
                "chiasm_margin_ok": 0.25,
                "signed_hil_ok": 0.22,
                "gse_filtration": 0.19,
                "leo_206_buffered": 0.16,
                "braille_hud_ok": 0.13,
                "console_siloed": 0.02,
                "handover_drop": 0.02,
                "opaque_hud_only": 0.01,
            },
            "trajectory_bias": 0.25,
            "routing_policy": (
                "Advisory-only (executed=False): A_0.14 < 3 -> highlight hold-point margin bottleneck; "
                "beam handover -> HTTP 206 ring buffer resume"
            ),
            "arch_nodes": [
                ("N1", "8-Subsystem Tap", "Air-gapped read-only mirror", 46, 250, "#5edaf0"),
                ("N2", "CountdownChiasm-v1", "A_tau(p_t) margin HUD (exec=F)", 328, 168, "#f2c45c"),
                ("N3", "CryoFiltrationWatch", "GSE valve P(x) drift tracker", 328, 330, "#f46a7e"),
                ("N4", "OrbitalHandoverBuf", "64MB ring + HTTP 206 resume", 610, 250, "#5edaf0"),
                ("N5", "FlightFrameSeal", "HIL + frame_sha256 ledger", 892, 250, "#f2c45c"),
                ("N6", "Operator HUD + Braille", "Low-glare console + 2x4 ARIA", 1174, 250, "#5edaf0"),
            ],
            "arch_edges": [
                ("N1", "N2", "10 Hz tap"),
                ("N1", "N3", "GSE tap"),
                ("N2", "N4", "margin"),
                ("N3", "N4", "drift"),
                ("N4", "N5", "lossless"),
                ("N5", "N6", "sealed"),
            ],
            "arch_feedback": ("N3", "N1", "Read-only advisory alert on margin / GSE drift (0 actuation)"),
            "improvements": [
                {
                    "id": "SPX-01",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Propulsion & Avionics Triage",
                    "title": "Read-Only Superlevel-Set A_tau(p_t) Mode-Transition Chiasm Advisor",
                    "short_title": "Countdown Chiasm Advisor",
                    "current_gap": (
                        "Terminal count and ascent operators track dozens of siloed propellant, valve, avionics, "
                        "and range screens where transient noise is hard to separate from irreversible margin collapse."
                    ),
                    "proposed_architecture": (
                        "Fold 8 normalized subsystem margin regimes into a strictly read-only (executed=False, "
                        "air-gapped telemetry tap, zero flight-computer actuation) Causal Chiasm HUD surfacing "
                        "A_tau(p_t) repertoire collapse and hold-point bottleneck alerts."
                    ),
                    "fieldglass_grounding": (
                        "Uses causal_chiasm() future_boxed_in and persistent_filtration_tomography() invariants "
                        "across scrub vs. nominal rehearsals."
                    ),
                    "concrete_deliverable": (
                        "CountdownChiasm-v1 read-only advisory panel + 10 Hz replayable telemetry evaluator."
                    ),
                    "kpis": [
                        {"metric": "Simulated multi-console triage time", "baseline": "38 s", "target": "21 s (-45%)"},
                        {"metric": "Advisory compute latency per tick", "baseline": "n/a", "target": "< 5 ms @ 10 Hz"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Advisory alert fatigue during nominal transients. Mitigation: require persistence "
                        "across >= 3 consecutive 10 Hz frames before elevating HUD state."
                    ),
                    "verification_method": (
                        "Replay historical/synthetic scrub vs. nominal rehearsal traces; verify < 5 ms tick budget "
                        "and zero actuation interfaces."
                    ),
                },
                {
                    "id": "SPX-02",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "HIL & Flight Provenance",
                    "title": "SHA-256 Sealed HIL, Monte Carlo & Webcast Flight-Frame Provenance",
                    "short_title": "SHA-256 HIL & Frame Seal",
                    "current_gap": (
                        "Compressed webcast HUD pixels lose exact mission-time provenance, and Monte Carlo / HIL "
                        "campaigns lack compact cryptographic manifests linking flight software builds to telemetry."
                    ),
                    "proposed_architecture": (
                        "Emit a frame_sha256-keyed JSON sidecar (t_mission_s, alt_km, vel_km_s, q_kpa, stage_state, "
                        "flight_sw_sha256) linking HIL Monte Carlo runs and launch webcasts to immutable build hashes."
                    ),
                    "fieldglass_grounding": (
                        "Extends fieldglass-causal-chiasm/v1 report_sha256 canonical JSON sealing to flight archives."
                    ),
                    "concrete_deliverable": (
                        "FlightFrameSeal sidecar generator + offline anomaly diff CLI."
                    ),
                    "kpis": [
                        {"metric": "Post-flight frame-to-telemetry verifiability", "baseline": "18% (OCR)", "target": "100% (SHA-256)"},
                        {"metric": "Archive overhead per 15-min flight", "baseline": "n/a", "target": "~1.2 MB compressed"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Public webcast timing offset vs. internal mission clock. Mitigation: publish clean "
                        "public-tier quantized 10 Hz sidecar with explicit T-0 alignment."
                    ),
                    "verification_method": (
                        "Verify 100% deterministic SHA-256 round-trip across simulated 900 s launch telemetry logs."
                    ),
                },
                {
                    "id": "SPX-03",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "GSE Predictive Maintenance",
                    "title": "Persistent Filtration GSE & Cryo Quick-Disconnect Drift Watch",
                    "short_title": "GSE Cryo Filtration Watch",
                    "current_gap": (
                        "High-cadence launch turnarounds stress LOX/CH4 valves, cryo quick-disconnects, and "
                        "helium purge lines, where subtle cycle-to-cycle hysteresis precedes hard faults."
                    ),
                    "proposed_architecture": (
                        "Compute cross-campaign persistent_filtration_tomography() over normalized valve actuation "
                        "times and seal-pressure decay signatures to flag P(x) < 0.14 invariant erosion early."
                    ),
                    "fieldglass_grounding": (
                        "Monitors structural_invariants vs. transient_states across static-fire and launch cycles."
                    ),
                    "concrete_deliverable": (
                        "CryoFiltrationWatch pad-health trend report generator."
                    ),
                    "kpis": [
                        {"metric": "Valve hysteresis early-warning lead", "baseline": "0 cycles", "target": ">= 3 cycles prior"},
                        {"metric": "Unplanned pad-recycle valve holds", "baseline": "6.5%", "target": "<= 1.8%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Ambient temperature swings mimic seal drift. Mitigation: normalize actuation curves "
                        "against pad cryo-manifold temperature bins."
                    ),
                    "verification_method": (
                        "Inject synthetic 2-8% valve-sluggishness ramp over 24 cycles; verify tomography flags "
                        "drift by cycle 12."
                    ),
                },
                {
                    "id": "SPX-04",
                    "priority": "P0",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Starlink Edge & Conjunctions",
                    "title": "Starlink LEO Handover HTTP 206 Ring Buffer & Conjunction Explainability",
                    "short_title": "LEO 206 Buffer + Conjunctions",
                    "current_gap": (
                        "80-400 ms LEO satellite beam handovers drop unbuffered telemetry and rigid transfers, "
                        "while autonomous conjunction-avoidance logs lack concise operator maneuver rationales."
                    ),
                    "proposed_architecture": (
                        "Deploy a 64 MB terminal edge ring buffer supporting HTTP 206 Partial Content range-resume "
                        "with SHA-256 checkpoints, paired with an interpretable ConjunctionLedger detailing "
                        "ephemeris uncertainty cones and delta-V tradeoff rationale."
                    ),
                    "fieldglass_grounding": (
                        "Mirrors fieldglass.showcase.make_range_handler() HTTP 206 Byte-Range resumption."
                    ),
                    "concrete_deliverable": (
                        "OrbitalHandoverBuffer proxy spec + ConjunctionLedger JSON schema."
                    ),
                    "kpis": [
                        {"metric": "Telemetry packet loss across LEO handover", "baseline": "2.40%", "target": "< 0.05%"},
                        {"metric": "Conjunction maneuver audit clarity", "baseline": "48%", "target": "94%"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +64 MB terminal RAM and +15 ms jitter smoothing. Mitigation: bypass ring buffer for "
                        "ultra-low-latency voice while protecting telemetry/bulk streams."
                    ),
                    "verification_method": (
                        "Simulate 250 ms link blackouts against HTTP 206 range server; assert 0 lost bytes."
                    ),
                },
                {
                    "id": "SPX-05",
                    "priority": "P1",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Operator HUD & Accessibility",
                    "title": "High-Contrast Dark-Observatory Anomaly HUD & 2x4 Braille Trajectory Plates",
                    "short_title": "Anomaly HUD + Braille Flight",
                    "current_gap": (
                        "Dense multi-color console displays increase cognitive load during off-nominal events, "
                        "and purely visual flight curves exclude blind/low-vision engineers and enthusiasts."
                    ),
                    "proposed_architecture": (
                        "Standardize a low-glare dark-observatory anomaly HUD (#0b0f17, cyan/gold/ruby semantic "
                        "severity) and co-emit 72-column 2x4 Unicode Braille ascent/landing trajectory plates "
                        "with ARIA milestone callouts (Max-Q, MECO, Entry Burn, Catch)."
                    ),
                    "fieldglass_grounding": (
                        "Uses fieldglass.plate.ink_to_braille_lines(cols=72) and dark-observatory palette."
                    ),
                    "concrete_deliverable": (
                        "BrailleTrajectory exporter + dark-observatory operator alert stylesheet."
                    ),
                    "kpis": [
                        {"metric": "Blind/low-vision flight milestone comprehension", "baseline": "5%", "target": "92%"},
                        {"metric": "Braille plate bundle footprint", "baseline": "n/a", "target": "+12 KB / phase"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Rapidly changing curves blur at 72x28 resolution. Mitigation: emit discrete "
                        "phase-keyed altitude/velocity plates at Max-Q, MECO, and Landing."
                    ),
                    "verification_method": (
                        "Verify generated trajectory Braille plates preserve clear ascent/booster curves and "
                        "pass WCAG contrast >= 7:1."
                    ),
                },
            ],
        },
        {
            "slug": "claire-grimes",
            "display_name": "Claire (aka Grimes)",
            "subtitle": "Elf.Tech Voice Attribution, Live Modular Rig & Synesthetic Archive",
            "category": "Creative & Audio",
            "domain_filter": "Creative & Audio",
            "accent_hex": "#c896ff",
            "tagline": "Cryptographic Elf.Tech stem provenance, bar-quantized stage failover & Braille cymatics",
            "scope_note": (
                "Constructive creative-engineering, live-rig resilience, and synesthetic archival "
                "proposals; zero external cloud inference."
            ),
            "system_profile": {
                "primary_strengths": [
                    "Pioneering open AI-voice collaboration model (Elf.Tech 50/50 split) and hybrid vocal/synth production.",
                    "Rich visual-worldbuilding lore combining music, typography, sigils, and live stage aesthetics.",
                    "Expressive single-take hardware/software studio improvisation workflows.",
                ],
                "core_bottlenecks": [
                    "Open-licensed stems lose cryptographic attribution and 50/50 split metadata after transcoding.",
                    "Live modular + Ableton + USB-MIDI + DMX rigs risk abrupt dead-air stalls on clock/VST dropouts.",
                    "Ephemeral modular patches, MIDI CC chains, and synesthetic scores lack long-term offline preservation.",
                ],
                "design_north_star": (
                    "Preserve creative flow state while sealing every vocal stem, live stage clock, and "
                    "synesthetic cymatic score in zero-cloud, tactile-ready provenance."
                ),
            },
            "past_weights": {
                "elf_stem_sealed": 0.09,
                "shadow_clk_sync": 0.11,
                "lore_dag_saved": 0.07,
                "cymatic_braille": 0.03,
                "royalty_split_ok": 0.13,
                "lost_attribution": 0.24,
                "midi_xrun_stall": 0.16,
                "patch_ephemeral": 0.17,
            },
            "future_weights": {
                "elf_stem_sealed": 0.27,
                "shadow_clk_sync": 0.24,
                "lore_dag_saved": 0.19,
                "cymatic_braille": 0.14,
                "royalty_split_ok": 0.11,
                "lost_attribution": 0.02,
                "midi_xrun_stall": 0.01,
                "patch_ephemeral": 0.02,
            },
            "trajectory_bias": 0.05,
            "routing_policy": (
                "midi_xrun_stall > tau or chiasm_shift < 0 -> bar-quantized crossfade to shadow stem deck; "
                "export -> ElfProvenance-v1 + CymaticBraille"
            ),
            "arch_nodes": [
                ("N1", "Vocal + Modular Rig", "Mic, Eurorack, Ableton, DMX", 46, 250, "#c896ff"),
                ("N2", "Flow Capture", "Zero-friction auto-index", 328, 168, "#f2c45c"),
                ("N3", "StageChiasm-Sync", "Bar-quantized shadow deck", 328, 330, "#f46a7e"),
                ("N4", "ElfProvenance + Gate", "50/50 stem SHA + lineage", 610, 250, "#5edaf0"),
                ("N5", "LoreVault-DAG Store", "Patch JSON + MIDI CC + stems", 892, 250, "#c896ff"),
                ("N6", "CymaticBraille + DMX", "2x4 tactile score + offline FX", 1174, 250, "#f2c45c"),
            ],
            "arch_edges": [
                ("N1", "N2", "raw take"),
                ("N1", "N3", "MIDI/xrun"),
                ("N2", "N4", "stem hash"),
                ("N3", "N4", "clock ok"),
                ("N4", "N5", "sealed"),
                ("N5", "N6", "SVG/Braille"),
            ],
            "arch_feedback": ("N3", "N1", "Bar-quantized shadow-deck crossfade on xrun breach"),
            "improvements": [
                {
                    "id": "GRIMES-01",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Voice & Stem Provenance",
                    "title": "Cryptographic Elf.Tech Voice Provenance & 50/50 Consent Licensing Registry",
                    "short_title": "Elf.Tech Stem Provenance",
                    "current_gap": (
                        "Open-licensed Elf.Tech AI vocal tracks lose creator attribution and 50/50 royalty split "
                        "metadata once pitch-shifted, remixed, and re-encoded across social platforms."
                    ),
                    "proposed_architecture": (
                        "Emit a dual-layer StemManifest (SHA-256 of dry vocal + instrumental masters, explicit "
                        "50/50 split license URI, perceptual chromaprint hash) verifiable 100% offline with "
                        "executed=False and zero cloud tokens."
                    ),
                    "fieldglass_grounding": (
                        "Uses canonical sorted-JSON report_sha256 sealing from fieldglass-causal-chiasm/v1."
                    ),
                    "concrete_deliverable": (
                        "ElfProvenance-v1 StemManifest JSON sidecar + offline chromaprint attribution checker."
                    ),
                    "kpis": [
                        {"metric": "Remix / transcode stem attribution recovery", "baseline": "31%", "target": "95%"},
                        {"metric": "Sidecar & export overhead", "baseline": "n/a", "target": "+4.2 KB / +0.8% CPU"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Aggressive time-stretching alters simple file hashes. Mitigation: pair exact "
                        "master SHA-256 with pitch/tempo-tolerant chromaprint signature."
                    ),
                    "verification_method": (
                        "Transcode test stems to 128 kbps MP3 and +/-2 semitone shifts; verify >= 95% attribution match."
                    ),
                },
                {
                    "id": "GRIMES-02",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Live Stage & DMX Failover",
                    "title": "Offline-First Stage Visuals & Bar-Quantized Modular Failover (StageChiasm-Sync)",
                    "short_title": "StageChiasm Live Failover",
                    "current_gap": (
                        "Live electronic sets bridging modular synths, Ableton, USB-MIDI, and DMX stage visuals "
                        "risk sudden dead-air on a single VST crash or clock jitter spike."
                    ),
                    "proposed_architecture": (
                        "Run an offline-first spectral A_tau(p_t) reactivity engine driving DMX/OSC visuals at 0 "
                        "cloud latency alongside a bar-quantized shadow clock; when xrun/jitter breaches tau, "
                        "crossfade seamlessly to the backup stem deck at the next bar boundary."
                    ),
                    "fieldglass_grounding": (
                        "Applies real-time A_tau(p_t) spectral superlevel volume and causal_chiasm shift alerts."
                    ),
                    "concrete_deliverable": (
                        "StageChiasm-Sync dual-deck watchdog + offline OSC/DMX spectral driver."
                    ),
                    "kpis": [
                        {"metric": "Live modular/VST catastrophic dead-air risk", "baseline": "8.5%", "target": "< 0.3%"},
                        {"metric": "Cloud dependency latency during show", "baseline": "120-400 ms", "target": "0 ms (local)"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +6 ms bar-quantized lookahead and redundant audio bus requirement. Mitigation: "
                        "auto-engage lookahead only on live performance profile."
                    ),
                    "verification_method": (
                        "Inject synthetic VST hang and USB-MIDI clock dropout mid-bar; verify glitch-free "
                        "crossfade within 1 bar."
                    ),
                },
                {
                    "id": "GRIMES-03",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Synesthetic Archival Preservation",
                    "title": "Archival Lore, Score & 2x4 Braille Cymatics Preservation Vault",
                    "short_title": "Braille Cymatics Vault",
                    "current_gap": (
                        "Visual-music releases, album sigils, and live projection scores exist only as proprietary "
                        "video/project files, locking out blind/low-vision fans and long-term archival printmakers."
                    ),
                    "proposed_architecture": (
                        "Transform spectral harmonic density (H1, M4^(1/4)) and waveform geometry into framed "
                        "archival vector SVGs plus 72-column 2x4 Unicode Braille tactile scores paired with "
                        "lossless stem manifests."
                    ),
                    "fieldglass_grounding": (
                        "Directly invokes fieldglass.plate.ink_to_braille_lines(cols=72) and save_braille_bundle()."
                    ),
                    "concrete_deliverable": (
                        "CymaticBraille-v1 SVG + 2x4 Unicode Braille score generator."
                    ),
                    "kpis": [
                        {"metric": "Offline tactile/screen-reader sonic score access", "baseline": "0%", "target": "93%"},
                        {"metric": "Tactile score bundle size per track", "baseline": "n/a", "target": "~35 KB"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Dense percussion noise clutters tactile dots. Mitigation: filter sub-threshold "
                        "noise via Bayer 4x4 dithering and harmonic bandpass envelope."
                    ),
                    "verification_method": (
                        "Generate Braille cymatic plates for synthetic harmonic sweeps; assert valid U+2800..U+28FF "
                        "density between 12% and 65%."
                    ),
                },
                {
                    "id": "GRIMES-04",
                    "priority": "P1",
                    "horizon": "Mid-term (3-6 mo)",
                    "domain": "Fan Co-Creation Sandbox",
                    "title": "Provenance-Tagged Fan Co-Creation Sandbox (LoreCoCreate-Gate)",
                    "short_title": "Fan Co-Creation Sandbox",
                    "current_gap": (
                        "Community remixes, AI vocal covers, and visual lore expansions blur canonical studio "
                        "masters with derivative fan works, causing licensing ambiguity."
                    ),
                    "proposed_architecture": (
                        "Provide a local-first co-creation manifest graph that cryptographically distinguishes "
                        "canonical_master hashes from community_derivative nodes while preserving attribution "
                        "chains and explicit remix permissions."
                    ),
                    "fieldglass_grounding": (
                        "Uses directed causal provenance edges and non-mutating source-capsule isolation."
                    ),
                    "concrete_deliverable": (
                        "LoreCoCreate-Gate manifest schema + remix lineage verifier."
                    ),
                    "kpis": [
                        {"metric": "Canonical vs. remix lineage clarity", "baseline": "41%", "target": "99%"},
                        {"metric": "Metadata lookup latency", "baseline": "n/a", "target": "< 10 ms offline"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: Friction for casual fan uploads. Mitigation: auto-populate manifest fields "
                        "from downloaded Elf.Tech stem pack."
                    ),
                    "verification_method": (
                        "Build 3-generation remix tree from canonical master; verify lineage resolver "
                        "reconstructs full ancestor chain offline."
                    ),
                },
                {
                    "id": "GRIMES-05",
                    "priority": "P0",
                    "horizon": "Near-term (0-3 mo)",
                    "domain": "Studio Flow Capture",
                    "title": "Single-Take Studio Flow Capture & Immutable Patch DAG (LoreVault-DAG)",
                    "short_title": "Single-Take Patch DAG",
                    "current_gap": (
                        "Spontaneous single-take vocal/synth sessions, modular patch routings, and MIDI CC "
                        "automations are lost or overwritten when DAW/OS environments update."
                    ),
                    "proposed_architecture": (
                        "Run a silent background flow-capture daemon that auto-indexes every single-take stem, "
                        "BPM/key metadata, MIDI CC curve, and synth preset JSON into a content-addressed "
                        "LoreVault-DAG with instant A/B auditioning."
                    ),
                    "fieldglass_grounding": (
                        "Inspired by Fieldglass single-take uninterrupted flow-state capture and deterministic "
                        "SHA-256 cataloging."
                    ),
                    "concrete_deliverable": (
                        "LoreVault-DAG local session indexer + zero-popup flow-capture manifest."
                    ),
                    "kpis": [
                        {"metric": "Post-migration session reconstruction time", "baseline": "240 min", "target": "<= 4 min"},
                        {"metric": "Creative flow interruption popups", "baseline": "4.2 / session", "target": "0"},
                    ],
                    "risks_and_mitigations": (
                        "Risk: +18 MB lossless delta per session. Mitigation: content-addressed audio chunk "
                        "deduplication across takes."
                    ),
                    "verification_method": (
                        "Simulate 10 consecutive takes with patch edits; verify zero UI interrupts and 100% "
                        "A/B state restoration."
                    ),
                },
            ],
        },
    ]


def _compute_subject_telemetry(spec: dict[str, Any]) -> dict[str, Any]:
    """Compute deterministic 24-episode 8-state & 256-bin Fieldglass telemetry."""
    past_w = normalize_dist(spec["past_weights"])
    future_w = normalize_dist(spec["future_weights"])
    states = list(past_w.keys())
    bias = float(spec.get("trajectory_bias", 0.0))

    episodes_8: list[dict[str, float]] = []
    per_ep_a004: list[int] = []
    per_ep_a010: list[int] = []
    h1_vals: list[float] = []
    h2_vals: list[float] = []
    m4_vals: list[float] = []

    x_bin = np.arange(32, dtype=np.float64)
    for t in range(EPISODE_COUNT):
        alpha = 0.5 * (1.0 - math.cos(math.pi * (t / float(EPISODE_COUNT - 1))))
        raw_ep = {
            s: (1.0 - alpha) * past_w[s] + alpha * future_w[s]
            for s in states
        }
        ep = normalize_dist(raw_ep)
        episodes_8.append(ep)

        h1_vals.append(shannon_h1(list(ep.values())))
        h2_vals.append(renyi_h2(list(ep.values())))
        m4_vals.append(quartic_purity_m4(list(ep.values())))

        # Build a deterministic 256-bin distribution whose 8 x 32-bin blocks sum to ep[s]
        p256 = np.zeros(256, dtype=np.float64)
        for idx, s in enumerate(states):
            block_weight = ep[s]
            if idx < 5:
                # Positive/capability states sharpen into structured superlevel modes
                sigma = max(1.8, 3.5 - 1.2 * alpha + 0.35 * bias)
                center = 10.0 + 2.5 * idx
                kernel = np.exp(-0.5 * ((x_bin - center) / sigma) ** 2) + 0.12
            else:
                # Failure/noise states start broad and decay as architecture improves
                sigma = max(2.2, 4.5 + 2.0 * alpha + 0.25 * bias)
                center = 15.5
                kernel = np.exp(-0.5 * ((x_bin - center) / sigma) ** 2) + 0.08
            kernel /= kernel.sum()
            p256[idx * 32 : (idx + 1) * 32] = block_weight * kernel

        p256 /= p256.sum()
        v004 = a_tau(p256, 0.004)
        v010 = a_tau(p256, 0.010)
        if not (15 <= v004 <= 145):
            raise ValueError(f"{spec['slug']} ep {t}: a004={v004} outside [15, 145]")
        if not (8 <= v010 <= 46):
            raise ValueError(f"{spec['slug']} ep {t}: a010={v010} outside [8, 46]")
        per_ep_a004.append(v004)
        per_ep_a010.append(v010)

    past_avg = normalize_dist(
        {s: float(np.mean([ep[s] for ep in episodes_8[:NEXUS_EPISODE]])) for s in states}
    )
    fut_avg = normalize_dist(
        {s: float(np.mean([ep[s] for ep in episodes_8[NEXUS_EPISODE:]])) for s in states}
    )
    chiasm_res = causal_chiasm(
        past_avg,
        fut_avg,
        tau=CHIASM_TAU,
        horizon=EPISODE_COUNT - NEXUS_EPISODE,
    )
    tomo_res = persistent_filtration_tomography(
        episodes_8,
        thresholds=DEFAULT_THRESHOLDS,
        invariant_tau=INVARIANT_TAU,
    )

    return {
        "states": states,
        "past_weights": past_w,
        "future_weights": future_w,
        "episodes_8": episodes_8,
        "chiasm_nexus": chiasm_res,
        "tomography": tomo_res,
        "per_episode_a004": per_ep_a004,
        "per_episode_a010": per_ep_a010,
        "h1_past_bits": round(h1_vals[0], 4),
        "h1_future_bits": round(h1_vals[-1], 4),
        "h1_mean_bits": round(float(np.mean(h1_vals)), 4),
        "h2_mean_bits": round(float(np.mean(h2_vals)), 4),
        "m4_past_purity": round(m4_vals[0], 4),
        "m4_future_purity": round(m4_vals[-1], 4),
        "m4_purity_mean": round(float(np.mean(m4_vals)), 4),
        "past_a014": a_tau(list(past_w.values()), 0.14),
        "future_a014": a_tau(list(future_w.values()), 0.14),
    }


def _rasterize_svg_clean(svg_path: Path, png_path: Path, width: int = 1400) -> Path:
    """Rasterize SVG with rsvg-convert and write clean RGB PNG with zero EXIF/GPS metadata."""
    tmp_png = png_path.with_suffix(".raw.png")
    rsvg = shutil.which("rsvg-convert") or "/usr/bin/rsvg-convert"
    subprocess.run([rsvg, "-w", str(width), "-o", str(tmp_png), str(svg_path)], check=True)
    with Image.open(tmp_png) as im:
        rgb = im.convert("RGB")
        rgb.save(png_path, format="PNG", optimize=True)
    tmp_png.unlink(missing_ok=True)
    return png_path


def _shorten(text: str, max_chars: int) -> str:
    """Shorten text cleanly at word boundaries without mid-word slicing."""
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return textwrap.shorten(clean, width=max_chars, placeholder="...", break_on_hyphens=False)


def _write_architecture_svg(spec: dict[str, Any], tel: dict[str, Any], svg_path: Path) -> Path:
    """Write bespoke 1400x920 dark-observatory node-edge architecture SVG for a subject."""
    esc = html.escape
    w, h = 1400, 920
    accent = spec["accent_hex"]
    ch = tel["chiasm_nexus"]
    tomo = tel["tomography"]

    node_w, node_h = 180, 72
    coords = {nid: (x, y, title, sub, col) for nid, title, sub, x, y, col in spec["arch_nodes"]}

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '<path d="M 0 1 L 10 5 L 0 9 z" fill="#5edaf0"/>',
        "</marker>",
        '<marker id="arrow-fb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '<path d="M 0 1 L 10 5 L 0 9 z" fill="#f46a7e"/>',
        "</marker>",
        "</defs>",
        f'<rect width="{w}" height="{h}" fill="#0b0f17"/>',
        f'<rect x="16" y="14" width="{w-32}" height="{h-28}" rx="12" fill="#0d131e" stroke="#263850" stroke-width="1.5"/>',
        # Header
        f'<rect x="30" y="26" width="1340" height="68" rx="10" fill="#121926" stroke="{accent}" stroke-width="2"/>',
        f'<text x="48" y="54" fill="{accent}" font-family="DejaVu Sans, sans-serif" font-size="22" font-weight="bold">'
        f'{esc(spec["display_name"].upper())} · IMPROVEMENT ARCHITECTURE &amp; TELEMETRY PIPELINE</text>',
        f'<text x="48" y="79" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" font-size="13">'
        f'{esc(spec["subtitle"])}  |  {esc(spec["category"])}</text>',
        # Right badge
        f'<rect x="1030" y="34" width="324" height="52" rx="8" fill="#0b0f17" stroke="#f46a7e" stroke-width="1.5"/>',
        f'<text x="1046" y="56" fill="#f2c45c" font-family="DejaVu Sans Mono, monospace" font-size="12" font-weight="bold">'
        f'CHIASM {esc(ch["presence_glyph"])} · A_0.10: {ch["past_accessible_volume"]} -&gt; {ch["future_accessible_volume"]} ({ch["chiasm_shift"]:+d})</text>',
        f'<text x="1046" y="75" fill="#5edaf0" font-family="DejaVu Sans Mono, monospace" font-size="11.5">'
        f'EI={ch["effective_information_bits"]:.3f}b · exec=False · tokens=0</text>',
        # Topology panel
        '<rect x="30" y="106" width="1340" height="414" rx="10" fill="#101724" stroke="#263850" stroke-width="1.5"/>',
        '<text x="48" y="129" fill="#5edaf0" font-family="DejaVu Sans Mono, monospace" font-size="13" font-weight="bold">'
        '01 / SYSTEM ARCHITECTURE TOPOLOGY</text>',
        f'<text x="48" y="147" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" font-size="10.5">'
        f'Policy: {esc(_shorten(spec["routing_policy"], 180))}</text>',
    ]

    # Edge paths first, collecting label pills so labels never clip behind nodes
    edge_labels: list[tuple[float, float, float, str]] = []
    for src_id, dst_id, lbl in spec["arch_edges"]:
        sx, sy, _, _, _ = coords[src_id]
        dx, dy, _, _, _ = coords[dst_id]
        x1 = sx + node_w
        y1 = sy + node_h / 2
        x2 = dx
        y2 = dy + node_h / 2
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 - 8
        parts.append(
            f'<path d="M {x1:.1f} {y1:.1f} C {mx:.1f} {y1:.1f}, {mx:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}" '
            f'fill="none" stroke="#5edaf0" stroke-width="2.2" marker-end="url(#arrow)"/>'
        )
        lbl_w = float(max(54, min(92, int(len(lbl) * 6.2) + 12)))
        edge_labels.append((mx, my, lbl_w, lbl))

    # Feedback arc path
    fb_src, fb_dst, fb_lbl = spec["arch_feedback"]
    fsx, fsy, _, _, _ = coords[fb_src]
    fdx, fdy, _, _, _ = coords[fb_dst]
    fx1 = fsx + node_w / 2
    fy1 = fsy + node_h
    fx2 = fdx + node_w / 2
    fy2 = fdy + node_h
    arc_y = 472
    parts.append(
        f'<path d="M {fx1:.1f} {fy1:.1f} L {fx1:.1f} {arc_y} L {fx2:.1f} {arc_y} L {fx2:.1f} {fy2+4:.1f}" '
        f'fill="none" stroke="#f46a7e" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#arrow-fb)"/>'
    )

    # Nodes
    for nid, title, sub, nx, ny, ncol in spec["arch_nodes"]:
        parts.append(
            f'<rect data-role="node" x="{nx}" y="{ny}" width="{node_w}" height="{node_h}" rx="9" '
            f'fill="#121926" stroke="{ncol}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{nx+10}" y="{ny+23}" fill="{ncol}" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="10.2" font-weight="bold">{esc(nid)}</text>'
        )
        parts.append(
            f'<text x="{nx+36}" y="{ny+23}" fill="#eaeff5" font-family="DejaVu Sans, sans-serif" '
            f'font-size="10.5" font-weight="bold">{esc(_shorten(title, 24))}</text>'
        )
        parts.append(
            f'<text x="{nx+10}" y="{ny+49}" fill="#93a6be" font-family="DejaVu Sans, sans-serif" '
            f'font-size="9.8">{esc(_shorten(sub, 34))}</text>'
        )

    # Edge-label pills drawn cleanly in inter-node gaps (zero node overlap)
    for mx, my, lbl_w, lbl in edge_labels:
        parts.append(
            f'<rect data-role="edge-label" x="{mx - lbl_w/2:.1f}" y="{my-10:.1f}" width="{lbl_w:.1f}" height="16" rx="4" '
            f'fill="#0b0f17" stroke="#263850" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{mx:.1f}" y="{my+1.5:.1f}" text-anchor="middle" fill="#93a6be" '
            f'font-family="DejaVu Sans Mono, monospace" font-size="9.5">{esc(lbl)}</text>'
        )

    # Feedback label pill
    fb_w = float(max(260, int(len(fb_lbl) * 6.8) + 24))
    fb_cx = max(40.0 + fb_w / 2.0, min(1360.0 - fb_w / 2.0, (fx1 + fx2) / 2.0))
    parts.append(
        f'<rect data-role="edge-label" x="{fb_cx - fb_w/2:.1f}" y="{arc_y - 12}" width="{fb_w:.1f}" height="22" rx="5" '
        f'fill="#18121b" stroke="#f46a7e" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{fb_cx:.1f}" y="{arc_y + 3}" text-anchor="middle" fill="#ffd3da" '
        f'font-family="DejaVu Sans Mono, monospace" font-size="11">{esc(fb_lbl)}</text>'
    )

    # 5 Improvement cards row
    parts.append(
        '<text x="48" y="550" fill="#f2c45c" font-family="DejaVu Sans Mono, monospace" font-size="13.5" font-weight="bold">'
        '02 / FIVE STRUCTURED IMPROVEMENTS &amp; MEASURABLE ACCEPTANCE TARGETS</text>'
    )
    card_w = 256
    gap = 15
    for idx, imp in enumerate(spec["improvements"]):
        cx = 30 + idx * (card_w + gap)
        cy = 564
        ch_h = 282
        kpi0 = imp["kpis"][0]
        kpi1 = imp["kpis"][1] if len(imp["kpis"]) > 1 else imp["kpis"][0]
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{ch_h}" rx="9" fill="#121926" stroke="#2a3c55" stroke-width="1.5"/>'
        )
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{card_w}" height="32" rx="9" fill="#172233"/>'
        )
        parts.append(
            f'<text x="{cx+12}" y="{cy+21}" fill="{accent}" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="12" font-weight="bold">{esc(imp["id"])} · {esc(imp["priority"])}</text>'
        )
        parts.append(
            f'<text x="{cx+244}" y="{cy+21}" text-anchor="end" fill="#f2c45c" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="10.5">{esc(imp["horizon"])}</text>'
        )
        parts.append(
            f'<text x="{cx+12}" y="{cy+55}" fill="#eaeff5" font-family="DejaVu Sans, sans-serif" '
            f'font-size="12" font-weight="bold">{esc(_shorten(imp["short_title"], 34))}</text>'
        )
        parts.append(
            f'<text x="{cx+12}" y="{cy+76}" fill="#5edaf0" font-family="DejaVu Sans, sans-serif" '
            f'font-size="10.2">{esc(_shorten(imp["domain"], 44))}</text>'
        )
        # Sequential word-boundary gap summary lines
        gap_lines = textwrap.wrap(
            imp["current_gap"],
            width=33,
            max_lines=2,
            placeholder="...",
            break_on_hyphens=False,
        )
        while len(gap_lines) < 2:
            gap_lines.append("")
        parts.append(
            f'<text x="{cx+12}" y="{cy+102}" fill="#93a6be" font-family="DejaVu Sans, sans-serif" font-size="10.5">'
            f'Gap: {esc(gap_lines[0])}</text>'
        )
        parts.append(
            f'<text x="{cx+12}" y="{cy+118}" fill="#93a6be" font-family="DejaVu Sans, sans-serif" font-size="10.5">'
            f'{esc(gap_lines[1])}</text>'
        )
        # KPI boxes
        parts.append(
            f'<rect x="{cx+10}" y="{cy+136}" width="{card_w-20}" height="62" rx="6" fill="#0b0f17" stroke="#24364d"/>'
        )
        parts.append(
            f'<text x="{cx+16}" y="{cy+154}" fill="#f2c45c" font-family="DejaVu Sans, sans-serif" font-size="10">'
            f'{esc(_shorten(kpi0["metric"], 40))}</text>'
        )
        parts.append(
            f'<text x="{cx+16}" y="{cy+174}" fill="#eaeff5" font-family="DejaVu Sans Mono, monospace" font-size="11" font-weight="bold">'
            f'{esc(kpi0["baseline"])} -&gt; {esc(kpi0["target"])}</text>'
        )
        parts.append(
            f'<rect x="{cx+10}" y="{cy+206}" width="{card_w-20}" height="62" rx="6" fill="#0b0f17" stroke="#24364d"/>'
        )
        parts.append(
            f'<text x="{cx+16}" y="{cy+224}" fill="#5edaf0" font-family="DejaVu Sans, sans-serif" font-size="10">'
            f'{esc(_shorten(kpi1["metric"], 40))}</text>'
        )
        parts.append(
            f'<text x="{cx+16}" y="{cy+244}" fill="#eaeff5" font-family="DejaVu Sans Mono, monospace" font-size="11" font-weight="bold">'
            f'{esc(kpi1["baseline"])} -&gt; {esc(kpi1["target"])}</text>'
        )

    # Footer
    invs = ", ".join(tomo["structural_invariants"][:4]) or "none"
    parts.append(
        f'<text x="32" y="886" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" font-size="12">'
        f'Fieldglass R2 · H1 {tel["h1_past_bits"]:.3f} -&gt; {tel["h1_future_bits"]:.3f} bits · '
        f'M4^(1/4) {tel["m4_past_purity"]:.4f} -&gt; {tel["m4_future_purity"]:.4f} · '
        f'Invariants(P&gt;=0.14): {esc(invs)} · executed=False · tokens_used=0</text>'
    )
    parts.append("</svg>")
    svg_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return svg_path


def _write_hub_overview_svg(subject_records: list[dict[str, Any]], svg_path: Path) -> Path:
    """Write 1400x900 dark-observatory multi-panel cross-subject hub SVG."""
    esc = html.escape
    w, h = 1400, 900
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        f'<rect width="{w}" height="{h}" fill="#0b0f17"/>',
        f'<rect x="16" y="14" width="{w-32}" height="{h-28}" rx="12" fill="#0d131e" stroke="#2a3c55" stroke-width="1.5"/>',
        '<rect x="30" y="26" width="1340" height="66" rx="10" fill="#121926" stroke="#f46a7e" stroke-width="2"/>',
        '<text x="48" y="54" fill="#f2c45c" font-family="DejaVu Sans, sans-serif" font-size="22" font-weight="bold">'
        'FIELDGLASS R2 · FIVE STRUCTURED IMPROVEMENT DOSSIERS (25 PROPOSALS)</text>',
        f'<text x="48" y="78" fill="#5edaf0" font-family="DejaVu Sans Mono, monospace" font-size="12.5">'
        f'{esc(EQUATION)}  ·  executed=False · sentience_claimed=False · tokens_used=0</text>',
        # Panel 1: Accessible Volume & Purity
        '<rect x="30" y="106" width="656" height="356" rx="10" fill="#121926" stroke="#294058" stroke-width="1.5"/>',
        '<text x="48" y="134" fill="#5edaf0" font-family="DejaVu Sans Mono, monospace" font-size="14" font-weight="bold">'
        '01 / ACCESSIBLE REPERTOIRE A_0.14(p) PAST -&gt; FUTURE &amp; PURITY M4^(1/4)</text>',
        '<text x="48" y="156" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" font-size="11.5">'
        'Muted Slate: Past Baseline A_0.14  ·  Subject Accent: Proposed Future A_0.14 (max 8 regimes)</text>',
    ]

    for idx, rec in enumerate(subject_records):
        ry = 182 + idx * 54
        past_a14 = rec["metrics"]["past_a014"]
        fut_a14 = rec["metrics"]["future_a014"]
        accent = rec["accent_hex"]
        pw = max(12, int((past_a14 / 8.0) * 240))
        fw = max(12, int((fut_a14 / 8.0) * 240))
        parts.append(
            f'<text x="48" y="{ry+15}" fill="#eaeff5" font-family="DejaVu Sans, sans-serif" '
            f'font-size="13" font-weight="bold">{esc(rec["display_name"])}</text>'
        )
        parts.append(f'<rect x="195" y="{ry}" width="{pw}" height="12" rx="3" fill="#3a4c66"/>')
        parts.append(f'<rect x="195" y="{ry+16}" width="{fw}" height="14" rx="3" fill="{accent}"/>')
        parts.append(
            f'<text x="455" y="{ry+18}" fill="#f2c45c" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="12">A_0.14: {past_a14} -&gt; {fut_a14}  |  M4: {rec["metrics"]["m4_future_purity"]:.3f}</text>'
        )

    # Panel 2: Effective Information & Persistent Invariants
    parts.append('<rect x="714" y="106" width="656" height="356" rx="10" fill="#121926" stroke="#294058" stroke-width="1.5"/>')
    parts.append(
        '<text x="732" y="134" fill="#f2c45c" font-family="DejaVu Sans Mono, monospace" font-size="14" font-weight="bold">'
        '02 / CAUSAL CHIASM EI (BITS) &amp; PERSISTENT INVARIANTS (P &gt;= 0.14)</text>'
    )
    parts.append(
        '<text x="732" y="156" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" font-size="11.5">'
        '24-episode trajectory per subject (Nexus t = 12) · fieldglass-causal-chiasm/v1</text>'
    )
    for idx, rec in enumerate(subject_records):
        ry = 182 + idx * 54
        ei = rec["metrics"]["effective_information_bits"]
        bw = max(18, int(min(1.0, ei / 1.5) * 210))
        invs = ", ".join(rec["metrics"]["structural_invariants"][:2])
        parts.append(
            f'<text x="732" y="{ry+16}" fill="{rec["accent_hex"]}" font-family="DejaVu Sans, sans-serif" '
            f'font-size="13" font-weight="bold">{esc(rec["display_name"])}</text>'
        )
        parts.append(f'<rect x="890" y="{ry+3}" width="{bw}" height="16" rx="3" fill="{rec["accent_hex"]}"/>')
        parts.append(
            f'<text x="{900+bw}" y="{ry+16}" fill="#eaeff5" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="11.5">EI={ei:.3f}b ({esc(rec["metrics"]["presence_glyph"])})</text>'
        )
        parts.append(
            f'<text x="890" y="{ry+35}" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="10.5">INV: {esc(invs)}</text>'
        )

    # Panel 3: 5-Subject Improvement Matrix (5 cards x 5 proposals = 25)
    parts.append(
        '<text x="34" y="492" fill="#f46a7e" font-family="DejaVu Sans Mono, monospace" font-size="14" font-weight="bold">'
        '03 / CROSS-SUBJECT DOSSIER MATRIX · 5 SUBJECTS × 5 CONCRETE IMPROVEMENTS = 25 PROPOSALS</text>'
    )
    col_w = 256
    gap = 15
    for idx, rec in enumerate(subject_records):
        cx = 30 + idx * (col_w + gap)
        cy = 506
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{col_w}" height="344" rx="9" fill="#121926" stroke="{rec["accent_hex"]}" stroke-width="1.5"/>'
        )
        parts.append(f'<rect x="{cx}" y="{cy}" width="{col_w}" height="46" rx="9" fill="#172233"/>')
        parts.append(
            f'<text x="{cx+12}" y="{cy+22}" fill="{rec["accent_hex"]}" font-family="DejaVu Sans, sans-serif" '
            f'font-size="14" font-weight="bold">{esc(rec["display_name"])}</text>'
        )
        parts.append(
            f'<text x="{cx+12}" y="{cy+39}" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="10.5">{esc(rec["category"])} · {rec["improvement_count"]} items</text>'
        )
        for p_idx, imp in enumerate(rec["top_improvements"]):
            py = cy + 68 + p_idx * 53
            parts.append(
                f'<rect x="{cx+10}" y="{py-14}" width="{col_w-20}" height="45" rx="6" fill="#0b0f17" stroke="#24364d"/>'
            )
            parts.append(
                f'<text x="{cx+15}" y="{py+2}" fill="#f2c45c" font-family="DejaVu Sans Mono, monospace" '
                f'font-size="9.2" font-weight="bold">{esc(imp["id"])}</text>'
            )
            parts.append(
                f'<text x="{cx+74}" y="{py+2}" fill="#eaeff5" font-family="DejaVu Sans, sans-serif" '
                f'font-size="9.5" font-weight="bold">{esc(_shorten(imp["short_title"], 32))}</text>'
            )
            parts.append(
                f'<text x="{cx+15}" y="{py+21}" fill="#5edaf0" font-family="DejaVu Sans Mono, monospace" '
                f'font-size="9.5">{esc(_shorten(imp["impact"], 34))}</text>'
            )

    parts.append(
        '<text x="32" y="874" fill="#93a6be" font-family="DejaVu Sans Mono, monospace" font-size="12">'
        'Fieldglass Observatory · Milestone M2 Hub · 100% Self-Contained Static Assets · Zero External CDNs · Zero GPS Metadata</text>'
    )
    parts.append("</svg>")
    svg_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return svg_path


def _shared_css() -> str:
    """Dark-observatory CSS aligned with docs/index.html, zero external dependencies."""
    return """  :root {
    --bg: #0b0f17;
    --panel: #121926;
    --panel2: #0e1420;
    --border: #2a3c55;
    --gold: #f2c45c;
    --cyan: #5edaf0;
    --ruby: #f46a7e;
    --violet: #c896ff;
    --text: #eaeff5;
    --muted: #93a6be;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
    padding: 18px 14px 64px;
  }
  .wrap { max-width: 1120px; margin: 0 auto; }
  header {
    background: linear-gradient(145deg, #162133, #0f1622);
    border: 1.5px solid var(--ruby);
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 18px;
  }
  .kicker {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ruby);
    margin-bottom: 4px;
  }
  h1 { margin: 0 0 6px; font-size: clamp(1.3rem, 3vw, 1.95rem); color: var(--gold); }
  h2 { margin: 0 0 8px; font-size: 1.15rem; color: var(--gold); }
  h3 { margin: 0 0 6px; font-size: 1.02rem; color: var(--cyan); }
  .eq {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.88rem;
    color: var(--cyan);
    background: #0a101a;
    border: 1px solid #243852;
    border-radius: 8px;
    padding: 8px 12px;
    display: inline-block;
    margin: 6px 0 10px;
    max-width: 100%;
    overflow-x: auto;
  }
  .sub { font-size: 0.88rem; color: var(--muted); margin: 0 0 12px; }
  .nav-links, .pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 18px;
  }
  .panel2 {
    background: var(--panel2);
    border: 1px solid #223248;
    border-radius: 12px;
    padding: 12px 14px;
  }
  .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
  .grid3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
  .badge {
    font-family: ui-monospace, monospace;
    font-size: 0.72rem;
    padding: 3px 9px;
    border-radius: 999px;
    background: #1c293d;
    color: var(--gold);
    border: 1px solid #354c6b;
    display: inline-block;
  }
  a.btn, button.btn {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 8px;
    background: #1a273b;
    color: var(--gold);
    border: 1px solid #3c5475;
    font-size: 0.8rem;
    text-decoration: none;
    cursor: pointer;
    font-family: inherit;
  }
  a.btn.accent, button.btn.active {
    background: #2b1826;
    border-color: var(--ruby);
    color: #ffd3da;
  }
  a.btn:hover, button.btn:hover { background: #23344f; }
  img {
    width: 100%;
    height: auto;
    border-radius: 10px;
    display: block;
    background: #070a10;
    border: 1px solid #223248;
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
  th, td { border-bottom: 1px solid #223248; padding: 8px 10px; text-align: left; vertical-align: top; }
  th { color: var(--gold); font-family: ui-monospace, monospace; font-size: 0.76rem; text-transform: uppercase; }
  pre.code, pre.braille {
    overflow-x: auto;
    background: #090d15;
    border: 1px solid #24364d;
    border-radius: 10px;
    padding: 12px;
    font-family: "DejaVu Sans Mono", ui-monospace, monospace;
    font-size: 0.76rem;
    line-height: 1.25;
    color: #eaeff5;
    margin: 10px 0 0;
  }
  select, input[type="range"] {
    background: #0a101a;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 10px;
    font-family: inherit;
  }
  .hidden { display: none !important; }
  footer { text-align: center; font-size: 0.78rem; color: var(--muted); margin-top: 24px; }"""


def _build_subject_html(
    spec: dict[str, Any],
    data_payload: dict[str, Any],
    summary_payload: dict[str, Any],
    chiasm_report: dict[str, Any],
    braille_text: str,
) -> str:
    """Build self-contained zero-CDN HTML dossier page for one R2 subject."""
    esc = html.escape
    slug = spec["slug"]
    accent = spec["accent_hex"]
    ch = chiasm_report["chiasm_nexus"]
    tomo = chiasm_report["persistent_filtration_tomography"]
    embedded_json = json.dumps(
        {
            "slug": slug,
            "display_name": spec["display_name"],
            "past_repertoire": ch["past_repertoire"],
            "future_repertoire": ch["future_repertoire"],
            "improvements": spec["improvements"],
            "metrics": summary_payload["metrics"],
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")

    tab_buttons = ['<button class="btn active" data-imp="all" type="button">All 5 Proposals</button>']
    for imp in spec["improvements"]:
        tab_buttons.append(
            f'<button class="btn" data-imp="{esc(imp["id"])}" type="button">{esc(imp["id"])}: {esc(imp["short_title"])}</button>'
        )

    imp_cards: list[str] = []
    for imp in spec["improvements"]:
        kpi_rows = "".join(
            f'<tr><td>{esc(k["metric"])}</td><td>{esc(k["baseline"])}</td>'
            f'<td style="color:var(--cyan);font-weight:600">{esc(k["target"])}</td></tr>'
            for k in imp["kpis"]
        )
        imp_cards.append(
            f'''<article class="card imp-card" data-imp-id="{esc(imp["id"])}" style="border-left:4px solid {accent}">
      <div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:center;margin-bottom:8px">
        <h3 style="margin:0;color:{accent}">{esc(imp["id"])} · {esc(imp["title"])}</h3>
        <div class="pill-row" style="margin:0">
          <span class="badge">{esc(imp["priority"])}</span>
          <span class="badge">{esc(imp["horizon"])}</span>
          <span class="badge">{esc(imp["domain"])}</span>
        </div>
      </div>
      <div class="grid2">
        <div class="panel2">
          <strong style="color:var(--ruby)">Problem / Gap</strong>
          <p class="sub" style="margin:4px 0 10px">{esc(imp["current_gap"])}</p>
          <strong style="color:var(--gold)">Architectural Proposal</strong>
          <p class="sub" style="margin:4px 0 10px">{esc(imp["proposed_architecture"])}</p>
          <strong style="color:var(--cyan)">Fieldglass Grounding</strong>
          <p class="sub" style="margin:4px 0 0">{esc(imp["fieldglass_grounding"])}</p>
        </div>
        <div class="panel2">
          <strong style="color:var(--gold)">Concrete Deliverable</strong>
          <p class="sub" style="margin:4px 0 10px">{esc(imp["concrete_deliverable"])}</p>
          <table>
            <thead><tr><th>Acceptance Metric</th><th>Baseline</th><th>Target</th></tr></thead>
            <tbody>{kpi_rows}</tbody>
          </table>
          <p class="sub" style="margin:10px 0 4px"><b style="color:var(--gold)">Tradeoffs &amp; Risks:</b> {esc(imp["risks_and_mitigations"])}</p>
          <p class="sub" style="margin:0"><b style="color:var(--cyan)">Verification:</b> {esc(imp["verification_method"])}</p>
        </div>
      </div>
    </article>'''
        )

    strengths_li = "".join(f"<li>{esc(s)}</li>" for s in spec["system_profile"]["primary_strengths"])
    bottlenecks_li = "".join(f"<li>{esc(b)}</li>" for b in spec["system_profile"]["core_bottlenecks"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," />
<title>{esc(spec["display_name"])} · Fieldglass R2 Improvement Dossier</title>
<style>
{_shared_css()}
</style>
</head>
<body>
<div class="wrap">
  <header style="border-color:{accent}">
    <div class="kicker">Fieldglass R2 Structured Improvement Dossier · {esc(spec["category"])}</div>
    <h1 style="color:{accent}">{esc(spec["display_name"])} — {esc(spec["subtitle"])}</h1>
    <div class="eq">{esc(EQUATION)}</div>
    <p class="sub">{esc(spec["tagline"])}. {esc(spec["scope_note"])}</p>
    <div class="nav-links">
      <a class="btn accent" href="../index.html">← All R2 Dossiers</a>
      <a class="btn" href="../../index.html">Fieldglass Observatory</a>
      <a class="btn" href="architecture.svg">architecture.svg</a>
      <a class="btn" href="chiasm.svg">chiasm.svg</a>
      <a class="btn" href="data.json">data.json</a>
      <a class="btn" href="summary.json">summary.json</a>
      <a class="btn" href="chiasm_report.json">chiasm_report.json</a>
    </div>
  </header>

  <section class="card">
    <h2>System Profile &amp; Design North Star</h2>
    <p class="sub" style="color:var(--text)"><b>North Star:</b> {esc(spec["system_profile"]["design_north_star"])}</p>
    <div class="grid2">
      <div class="panel2">
        <h3 style="color:var(--cyan)">Observed Strengths</h3>
        <ul style="margin:6px 0 0;padding-left:18px;font-size:0.85rem;color:var(--muted)">{strengths_li}</ul>
      </div>
      <div class="panel2">
        <h3 style="color:var(--ruby)">Core Architectural Bottlenecks</h3>
        <ul style="margin:6px 0 0;padding-left:18px;font-size:0.85rem;color:var(--muted)">{bottlenecks_li}</ul>
      </div>
    </div>
  </section>

  <section class="card">
    <h2>Interactive Proposal Selector (5 Concrete Improvements)</h2>
    <div class="pill-row" id="proposal-tabs">{"".join(tab_buttons)}</div>
  </section>

  <div id="proposals-container">
    {"".join(imp_cards)}
  </div>

  <section class="card">
    <h2>Interactive Repertoire &amp; Live Kloster A_tau(p) Comparison</h2>
    <p class="sub">
      Adjust threshold tau (0.04 to 0.25) to inspect accessible operational regimes across Baseline Past vs. Proposed Future.
      Contract: <code>{esc(CONTRACT)}</code> · <code>executed=false</code> · <code>sentience_claimed=false</code> · <code>tokens_used=0</code>.
    </p>
    <div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-bottom:12px">
      <label for="tau-slider" style="font-family:ui-monospace,monospace;color:var(--gold)">
        tau = <span id="tau-val">0.10</span>
      </label>
      <input id="tau-slider" type="range" min="0.04" max="0.25" step="0.01" value="0.10" />
      <span class="badge" id="tau-summary">Past A_tau: {ch["past_accessible_volume"]} -> Future A_tau: {ch["future_accessible_volume"]} (shift {ch["chiasm_shift"]:+d})</span>
      <span class="badge">EI = {ch["effective_information_bits"]:.4f} bits · Glyph {esc(ch["presence_glyph"])}</span>
      <span class="badge">Invariants (P&gt;=0.14): {esc(", ".join(tomo["structural_invariants"]))}</span>
    </div>
    <table>
      <thead><tr><th>Operational State</th><th>Past Weight</th><th>Future Weight</th><th>Delta</th><th>Accessible @ tau (Past / Future)</th></tr></thead>
      <tbody id="repertoire-tbody"></tbody>
    </table>
  </section>

  <section class="card">
    <h2>Architecture Diagram &amp; Causal Chiasm Tomography</h2>
    <div class="grid2">
      <div class="panel2">
        <h3>System Architecture ({esc(spec["display_name"])})</h3>
        <a href="architecture.svg"><img src="preview.png" alt="{esc(spec["display_name"])} architecture preview" /></a>
      </div>
      <div class="panel2">
        <h3>Causal Chiasm &amp; 24-Episode Filtration Tomography</h3>
        <a href="chiasm.svg"><img src="chiasm.svg" alt="{esc(spec["display_name"])} causal chiasm SVG" /></a>
      </div>
    </div>
  </section>

  <section class="card">
    <h2>72-Column 2x4 Unicode Braille Tactile Plate &amp; Seals</h2>
    <div class="grid2">
      <div class="panel2">
        <h3>Dot-Rendered Tactile Preview</h3>
        <a href="{esc(slug)}_braille_preview.png"><img src="{esc(slug)}_braille_preview.png" alt="{esc(spec["display_name"])} 2x4 Braille preview" /></a>
        <div class="nav-links">
          <a class="btn" href="{esc(slug)}_braille.txt">{esc(slug)}_braille.txt</a>
          <a class="btn" href="{esc(slug)}_braille.json">{esc(slug)}_braille.json</a>
        </div>
      </div>
      <div class="panel2">
        <h3>Copyable Unicode Braille Text</h3>
        <pre class="braille">{esc(braille_text.strip())}</pre>
        <p class="sub" style="margin-top:10px;font-family:ui-monospace,monospace;font-size:0.74rem">
          scene_sha256: {esc(chiasm_report["scene_sha256"])}<br/>
          report_sha256: {esc(chiasm_report["report_sha256"])}
        </p>
      </div>
    </div>
  </section>

  <footer>
    Fieldglass Observatory · Milestone M2 · {esc(spec["display_name"])} Dossier · 0 Cloud Tokens · executed=False
  </footer>
</div>

<script id="dossier-data" type="application/json">{embedded_json}</script>
<script>
(function () {{
  var payload = JSON.parse(document.getElementById("dossier-data").textContent);
  var tabs = document.querySelectorAll("#proposal-tabs button[data-imp]");
  var cards = document.querySelectorAll(".imp-card");
  tabs.forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var target = btn.getAttribute("data-imp");
      tabs.forEach(function (b) {{ b.classList.toggle("active", b === btn); }});
      cards.forEach(function (card) {{
        var show = target === "all" || card.getAttribute("data-imp-id") === target;
        card.classList.toggle("hidden", !show);
      }});
    }});
  }});

  var slider = document.getElementById("tau-slider");
  var tauLabel = document.getElementById("tau-val");
  var summaryBadge = document.getElementById("tau-summary");
  var tbody = document.getElementById("repertoire-tbody");

  function escHtml(str) {{
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }}

  function renderTau() {{
    var tau = parseFloat(slider.value);
    tauLabel.textContent = tau.toFixed(2);
    var past = payload.past_repertoire;
    var future = payload.future_repertoire;
    var keys = Object.keys(past);
    var pastCount = 0;
    var futCount = 0;
    var rows = [];
    keys.forEach(function (k) {{
      var pv = past[k];
      var fv = future[k];
      var pOn = pv > tau;
      var fOn = fv > tau;
      if (pOn) pastCount += 1;
      if (fOn) futCount += 1;
      var delta = fv - pv;
      var dStr = (delta >= 0 ? "+" : "") + delta.toFixed(3);
      rows.push(
        "<tr>" +
          "<td><code>" + escHtml(k) + "</code></td>" +
          "<td>" + pv.toFixed(3) + "</td>" +
          "<td>" + fv.toFixed(3) + "</td>" +
          "<td style='color:" + (delta >= 0 ? "var(--cyan)" : "var(--ruby)") + "'>" + dStr + "</td>" +
          "<td>" + (pOn ? "ACTIVE" : "below") + " / <b style='color:" + (fOn ? "var(--gold)" : "var(--muted)") + "'>" + (fOn ? "ACTIVE" : "below") + "</b></td>" +
        "</tr>"
      );
    }});
    tbody.innerHTML = rows.join("");
    var shift = futCount - pastCount;
    summaryBadge.textContent = "Past A_tau: " + pastCount + " -> Future A_tau: " + futCount + " (shift " + (shift >= 0 ? "+" : "") + shift + ")";
  }}

  slider.addEventListener("input", renderTau);
  renderTau();
}})();
</script>
</body>
</html>
"""


def _build_hub_html(
    subject_records: list[dict[str, Any]],
    subject_repertoires: dict[str, dict[str, Any]],
    hub_summary: dict[str, Any],
) -> str:
    """Build self-contained zero-CDN interactive Hub HTML in docs/improvements/index.html."""
    esc = html.escape
    domains = ["All (5)", "Frontier AI", "Real-Time & Social", "Aerospace & Telemetry", "Creative & Audio"]
    filter_pills = []
    for idx, dom in enumerate(domains):
        active_cls = " active" if idx == 0 else ""
        val = "all" if idx == 0 else dom
        filter_pills.append(
            f'<button class="btn{active_cls}" data-domain="{esc(val)}" type="button">{esc(dom)}</button>'
        )

    matrix_rows = []
    cards = []
    options_a = []
    options_b = []

    for idx, rec in enumerate(subject_records):
        slug = rec["slug"]
        m = rec["metrics"]
        accent = rec["accent_hex"]
        invs = ", ".join(m["structural_invariants"][:3])
        matrix_rows.append(
            f'''<tr class="subject-row" data-domain="{esc(rec["domain_filter"])}" data-slug="{esc(slug)}">
        <td><a href="{esc(slug)}/index.html" style="color:{accent};font-weight:700;text-decoration:none">{esc(rec["display_name"])}</a></td>
        <td><span class="badge">{esc(rec["domain_filter"])}</span></td>
        <td class="dyn-a-tau" data-slug="{esc(slug)}">{m["past_a_tau"]} -> {m["future_a_tau"]} ({m["chiasm_shift"]:+d})</td>
        <td>{m["past_a014"]} -> {m["future_a014"]}</td>
        <td>{m["effective_information_bits"]:.4f} b</td>
        <td>{m["h1_past_bits"]:.2f} -> {m["h1_future_bits"]:.2f}</td>
        <td>{m["m4_past_purity"]:.3f} -> {m["m4_future_purity"]:.3f}</td>
        <td style="font-family:ui-monospace,monospace;font-size:0.75rem">{esc(invs)}</td>
        <td>
          <a class="btn" href="{esc(slug)}/index.html">Dossier</a>
          <a class="btn" href="{esc(slug)}/chiasm.svg">Chiasm</a>
          <a class="btn" href="{esc(slug)}/{esc(slug)}_braille_preview.png">Braille</a>
        </td>
      </tr>'''
        )

        imp_pills = "".join(
            f'<span class="badge" style="border-color:{accent}">{esc(imp["id"])}: {esc(imp["short_title"])}</span>'
            for imp in rec["top_improvements"]
        )
        cards.append(
            f'''<article class="card subject-card" data-domain="{esc(rec["domain_filter"])}" style="border-left:4px solid {accent}">
      <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px">
        <h3 style="margin:0;color:{accent}">{esc(rec["display_name"])} · {esc(rec["category"])}</h3>
        <span class="badge">5 Improvements · Glyph {esc(m["presence_glyph"])} · EI {m["effective_information_bits"]:.3f}b</span>
      </div>
      <p class="sub">{esc(rec["tagline"])}</p>
      <a href="{esc(slug)}/index.html"><img src="{esc(slug)}/preview.png" alt="{esc(rec["display_name"])} architecture preview" /></a>
      <div class="pill-row" style="margin-top:10px">{imp_pills}</div>
      <div class="nav-links" style="margin-top:10px">
        <a class="btn accent" href="{esc(slug)}/index.html">Open {esc(rec["display_name"])} Dossier →</a>
        <a class="btn" href="{esc(slug)}/architecture.svg">architecture.svg</a>
        <a class="btn" href="{esc(slug)}/chiasm.svg">chiasm.svg</a>
        <a class="btn" href="{esc(slug)}/chiasm_report.json">chiasm_report.json</a>
        <a class="btn" href="{esc(slug)}/data.json">data.json</a>
      </div>
    </article>'''
        )
        sel_a = " selected" if idx == 0 else ""
        sel_b = " selected" if idx == 1 else ""
        options_a.append(f'<option value="{esc(slug)}"{sel_a}>{esc(rec["display_name"])}</option>')
        options_b.append(f'<option value="{esc(slug)}"{sel_b}>{esc(rec["display_name"])}</option>')

    embedded_hub = json.dumps(
        {
            "hub": hub_summary,
            "repertoires": subject_repertoires,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," />
<title>Fieldglass R2 · Five Structured Improvement Dossiers</title>
<style>
{_shared_css()}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kicker">Fieldglass Observatory · Milestone M2 (R2 Structured Improvement Dossiers)</div>
    <h1>R2 · ChatGPT, Anthropic, Grok, SpaceX &amp; Claire (aka Grimes)</h1>
    <div class="eq">{esc(EQUATION)}</div>
    <p class="sub">
      25 concrete, domain-grounded architectural and reliability improvements across 5 dossiers, paired with
      24-episode Causal Chiasm &amp; Persistent Filtration Tomography reports, bespoke dark-observatory SVGs,
      and 72-column 2×4 Unicode Braille tactile plates. 0 cloud tokens · executed=false · sentience_claimed=false.
    </p>
    <div class="nav-links">
      <a class="btn accent" href="../index.html">← Back to Fieldglass Observatory</a>
      <a class="btn" href="hub_overview.svg">hub_overview.svg</a>
      <a class="btn" href="preview.png">preview.png</a>
      <a class="btn" href="summary.json">summary.json</a>
    </div>
  </header>

  <section class="card">
    <h2>Cross-Subject Observatory Synthesis</h2>
    <a href="hub_overview.svg"><img src="preview.png" alt="Fieldglass R2 Cross-Subject Overview" /></a>
  </section>

  <section class="card">
    <h2>Interactive Domain Filter &amp; Live Kloster A_tau(p) Slider</h2>
    <div class="pill-row" id="domain-pills">{"".join(filter_pills)}</div>
    <div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-top:12px">
      <label for="hub-tau-slider" style="font-family:ui-monospace,monospace;color:var(--gold)">
        Live tau = <span id="hub-tau-val">0.10</span>
      </label>
      <input id="hub-tau-slider" type="range" min="0.04" max="0.25" step="0.01" value="0.10" />
      <span class="sub" style="margin:0">Recomputes Past -&gt; Future A_tau(p) across all 5 subjects in real time.</span>
    </div>
  </section>

  <section class="card">
    <h2>Cross-Subject Causal Chiasm &amp; Metric Matrix</h2>
    <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th>Subject</th><th>Domain</th><th>A_tau (Past-&gt;Fut)</th><th>A_0.14</th>
            <th>EI (bits)</th><th>H1 (bits)</th><th>M4^(1/4)</th><th>Persistent Invariants</th><th>Assets</th>
          </tr>
        </thead>
        <tbody>{"".join(matrix_rows)}</tbody>
      </table>
    </div>
  </section>

  <section class="card">
    <h2>Interactive Subject A vs. Subject B Comparison</h2>
    <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:12px">
      <label>Subject A: <select id="cmp-a">{"".join(options_a)}</select></label>
      <label>Subject B: <select id="cmp-b">{"".join(options_b)}</select></label>
    </div>
    <div class="grid2" id="cmp-grid"></div>
  </section>

  <div class="grid2" id="cards-grid">
    {"".join(cards)}
  </div>

  <footer>
    Fieldglass Observatory · R2 Five Improvement Dossiers · Deterministic Local Build · 0 Cloud Tokens
  </footer>
</div>

<script id="hub-data" type="application/json">{embedded_hub}</script>
<script>
(function () {{
  var data = JSON.parse(document.getElementById("hub-data").textContent);
  var subjectsBySlug = {{}};
  data.hub.subjects.forEach(function (s) {{ subjectsBySlug[s.slug] = s; }});

  var pills = document.querySelectorAll("#domain-pills button[data-domain]");
  var cards = document.querySelectorAll(".subject-card");
  var rows = document.querySelectorAll(".subject-row");

  pills.forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var dom = btn.getAttribute("data-domain");
      pills.forEach(function (b) {{ b.classList.toggle("active", b === btn); }});
      cards.forEach(function (c) {{
        c.classList.toggle("hidden", dom !== "all" && c.getAttribute("data-domain") !== dom);
      }});
      rows.forEach(function (r) {{
        r.classList.toggle("hidden", dom !== "all" && r.getAttribute("data-domain") !== dom);
      }});
    }});
  }});

  var tauSlider = document.getElementById("hub-tau-slider");
  var tauVal = document.getElementById("hub-tau-val");
  function updateTau() {{
    var tau = parseFloat(tauSlider.value);
    tauVal.textContent = tau.toFixed(2);
    document.querySelectorAll(".dyn-a-tau").forEach(function (cell) {{
      var slug = cell.getAttribute("data-slug");
      var rep = data.repertoires[slug];
      var pCount = 0;
      var fCount = 0;
      Object.keys(rep.past).forEach(function (k) {{
        if (rep.past[k] > tau) pCount += 1;
        if (rep.future[k] > tau) fCount += 1;
      }});
      var shift = fCount - pCount;
      cell.textContent = pCount + " -> " + fCount + " (" + (shift >= 0 ? "+" : "") + shift + ")";
    }});
  }}
  tauSlider.addEventListener("input", updateTau);
  updateTau();

  var selA = document.getElementById("cmp-a");
  var selB = document.getElementById("cmp-b");
  var cmpGrid = document.getElementById("cmp-grid");
  function escHtml(str) {{
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }}
  function renderCompare() {{
    var slugs = [selA.value, selB.value];
    cmpGrid.innerHTML = slugs.map(function (sl) {{
      var s = subjectsBySlug[sl];
      var m = s.metrics;
      var imps = s.top_improvements.map(function (i) {{
        return "<li><b>" + escHtml(i.id) + "</b>: " + escHtml(i.title) + " <span style='color:var(--cyan)'>(" + escHtml(i.impact) + ")</span></li>";
      }}).join("");
      return "<div class='panel2' style='border-left:3px solid " + escHtml(s.accent_hex) + "'>" +
        "<h3 style='color:" + escHtml(s.accent_hex) + "'>" + escHtml(s.display_name) + " (" + escHtml(s.category) + ")</h3>" +
        "<p class='sub'>" + escHtml(s.tagline) + "</p>" +
        "<p class='sub'><b>A_0.10:</b> " + m.past_a_tau + " -> " + m.future_a_tau +
        " | <b>EI:</b> " + m.effective_information_bits.toFixed(4) + "b" +
        " | <b>M4:</b> " + m.m4_future_purity.toFixed(4) + "</p>" +
        "<ul style='margin:6px 0 0;padding-left:18px;font-size:0.82rem;color:var(--muted)'>" + imps + "</ul>" +
      "</div>";
    }}).join("");
  }}
  selA.addEventListener("change", renderCompare);
  selB.addEventListener("change", renderCompare);
  renderCompare();
}})();
</script>
</body>
</html>
"""


def build_all(docs_root: str | Path = REPO_ROOT / "docs") -> dict[str, Any]:
    """Build all R2 hub and 5 subject dossiers under `<docs_root>/improvements/`."""
    docs_path = Path(docs_root).expanduser().resolve()
    imp_root = docs_path / "improvements"
    imp_root.mkdir(parents=True, exist_ok=True)

    specs = _subject_specs()
    subject_records: list[dict[str, Any]] = []
    subject_repertoires: dict[str, dict[str, Any]] = {}

    for spec in specs:
        slug = spec["slug"]
        subj_dir = imp_root / slug
        subj_dir.mkdir(parents=True, exist_ok=True)

        tel = _compute_subject_telemetry(spec)
        ch = tel["chiasm_nexus"]
        tomo = tel["tomography"]

        # 1. Causal Chiasm & Filtration Tomography SVG
        chiasm_svg = write_chiasm_svg(
            subj_dir / "chiasm.svg",
            title=f"{spec['display_name'].upper()} · IMPROVEMENT CAUSAL CHIASM & FILTRATION TOMOGRAPHY",
            subtitle=f"{spec['subtitle']} · 24-Episode Trajectory (Nexus t = {NEXUS_EPISODE})",
            chiasm=ch,
            tomography=tomo,
            per_sec_a004=tel["per_episode_a004"],
            per_sec_a010=tel["per_episode_a010"],
            nexus_sec=NEXUS_EPISODE,
        )
        scene_sha256 = hashlib.sha256(chiasm_svg.read_bytes()).hexdigest()

        # 2. chiasm_report.json (fieldglass-causal-chiasm/v1)
        chiasm_report: dict[str, Any] = {
            "slug": slug,
            "subject": spec["display_name"],
            "title": f"{spec['display_name'].upper()} · IMPROVEMENT CAUSAL CHIASM & FILTRATION TOMOGRAPHY",
            "contract": CONTRACT,
            "equation": EQUATION,
            "episode_count": EPISODE_COUNT,
            "nexus_sec": NEXUS_EPISODE,
            "chiasm_nexus": ch,
            "persistent_filtration_tomography": tomo,
            "per_episode_a004": tel["per_episode_a004"],
            "per_episode_a010": tel["per_episode_a010"],
            "h1_mean_bits": tel["h1_mean_bits"],
            "h2_mean_bits": tel["h2_mean_bits"],
            "m4_purity_mean": tel["m4_purity_mean"],
            "scene_sha256": scene_sha256,
            "executed": False,
            "sentience_claimed": False,
            "tokens_used": 0,
        }
        chiasm_report["report_sha256"] = hashlib.sha256(
            json.dumps(chiasm_report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        (subj_dir / "chiasm_report.json").write_text(
            json.dumps(chiasm_report, indent=2) + "\n", encoding="utf-8"
        )

        # 3. Bespoke architecture.svg + metadata-free preview.png
        arch_svg = _write_architecture_svg(spec, tel, subj_dir / "architecture.svg")
        preview_png = _rasterize_svg_clean(arch_svg, subj_dir / "preview.png", width=1400)

        # 4. 72-column 2x4 Braille bundle from bright-foreground luminance
        with Image.open(preview_png) as im:
            arr = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
        lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
        ink_map = np.clip((lum - 0.14) / 0.60, 0.0, 1.0)
        braille_lines = ink_to_braille_lines(ink_map, cols=72)
        braille_bundle = save_braille_bundle(
            braille_lines,
            subj_dir,
            slug,
            title=f"{spec['display_name'].upper()} — 2x4 BRAILLE ARCHITECTURE PLATE",
            subtitle=f"{spec['subtitle']} · 72 cols · executed=False",
        )
        braille_text = Path(braille_bundle["txt"]).read_text(encoding="utf-8")

        # 5. Full structured dossier data.json
        data_payload = {
            "schema_version": "fieldglass-r2-dossier/v1",
            "slug": slug,
            "display_name": spec["display_name"],
            "subtitle": spec["subtitle"],
            "category": spec["category"],
            "accent_hex": spec["accent_hex"],
            "scope_note": spec["scope_note"],
            "system_profile": spec["system_profile"],
            "improvements": spec["improvements"],
            "telemetry_profile": {
                "repertoire_states": tel["states"],
                "past_weights": tel["past_weights"],
                "future_weights": tel["future_weights"],
                "episode_count": EPISODE_COUNT,
                "nexus_episode": NEXUS_EPISODE,
                "routing_policy": spec["routing_policy"],
            },
            "artifacts": {
                "html": "index.html",
                "preview_png": "preview.png",
                "architecture_svg": "architecture.svg",
                "chiasm_svg": "chiasm.svg",
                "chiasm_report": "chiasm_report.json",
                "summary_json": "summary.json",
                "braille_txt": f"{slug}_braille.txt",
                "braille_json": f"{slug}_braille.json",
                "braille_preview_png": f"{slug}_braille_preview.png",
            },
            "clinical_use": False,
            "executed": False,
            "sentience_claimed": False,
            "tokens_used": 0,
        }
        (subj_dir / "data.json").write_text(
            json.dumps(data_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        # 6. M4 slide-ready summary.json
        top_improvements = [
            {
                "id": imp["id"],
                "title": imp["title"],
                "short_title": imp["short_title"],
                "impact": f"{imp['kpis'][0]['baseline']} -> {imp['kpis'][0]['target']}",
            }
            for imp in spec["improvements"]
        ]
        kpis_flat = [
            {
                "id": imp["id"],
                "metric": imp["kpis"][0]["metric"],
                "baseline": imp["kpis"][0]["baseline"],
                "target": imp["kpis"][0]["target"],
            }
            for imp in spec["improvements"]
        ]
        summary_payload = {
            "schema_version": "fieldglass-summary/v1",
            "milestone": "M2",
            "slug": slug,
            "display_name": spec["display_name"],
            "title": f"{spec['display_name']} — Structured Improvement Dossier",
            "tagline": spec["tagline"],
            "category": spec["category"],
            "domain_filter": spec["domain_filter"],
            "accent_hex": spec["accent_hex"],
            "index_html": f"docs/improvements/{slug}/index.html",
            "preview_png": f"docs/improvements/{slug}/preview.png",
            "braille_preview_png": f"docs/improvements/{slug}/{slug}_braille_preview.png",
            "architecture_svg": f"docs/improvements/{slug}/architecture.svg",
            "chiasm_svg": f"docs/improvements/{slug}/chiasm.svg",
            "chiasm_report": f"docs/improvements/{slug}/chiasm_report.json",
            "data_json": f"docs/improvements/{slug}/data.json",
            "summary_json": f"docs/improvements/{slug}/summary.json",
            "improvement_count": len(spec["improvements"]),
            "top_improvements": top_improvements,
            "kpis": kpis_flat,
            "metrics": {
                "episodes": EPISODE_COUNT,
                "tau": CHIASM_TAU,
                "past_a_tau": ch["past_accessible_volume"],
                "future_a_tau": ch["future_accessible_volume"],
                "past_a014": tel["past_a014"],
                "future_a014": tel["future_a014"],
                "chiasm_shift": ch["chiasm_shift"],
                "effective_information_bits": ch["effective_information_bits"],
                "h1_past_bits": tel["h1_past_bits"],
                "h1_future_bits": tel["h1_future_bits"],
                "m4_past_purity": tel["m4_past_purity"],
                "m4_future_purity": tel["m4_future_purity"],
                "presence_glyph": ch["presence_glyph"],
                "structural_invariants": tomo["structural_invariants"],
                "scene_sha256": scene_sha256,
                "report_sha256": chiasm_report["report_sha256"],
            },
            "clinical_use": False,
            "executed": False,
            "sentience_claimed": False,
            "tokens_used": 0,
        }
        (subj_dir / "summary.json").write_text(
            json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        # 7. Subject dossier index.html
        subj_html = _build_subject_html(spec, data_payload, summary_payload, chiasm_report, braille_text)
        (subj_dir / "index.html").write_text(subj_html, encoding="utf-8")

        subject_records.append(summary_payload)
        subject_repertoires[slug] = {
            "past": ch["past_repertoire"],
            "future": ch["future_repertoire"],
        }

    # Hub SVG + clean PNG
    hub_svg = _write_hub_overview_svg(subject_records, imp_root / "hub_overview.svg")
    _rasterize_svg_clean(hub_svg, imp_root / "preview.png", width=1400)

    # Hub summary.json
    hub_summary = {
        "schema_version": "fieldglass-improvements-hub/v1",
        "contract": "fieldglass-r2-improvements/v1",
        "chiasm_contract": CONTRACT,
        "milestone": "M2",
        "title": "R2 · Five Structured Improvement Dossiers",
        "index_html": "docs/improvements/index.html",
        "hub_overview_svg": "docs/improvements/hub_overview.svg",
        "preview_png": "docs/improvements/preview.png",
        "subject_count": len(subject_records),
        "total_improvements": sum(r["improvement_count"] for r in subject_records),
        "subjects": subject_records,
        "clinical_use": False,
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": 0,
    }
    (imp_root / "summary.json").write_text(
        json.dumps(hub_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Hub index.html
    hub_html = _build_hub_html(subject_records, subject_repertoires, hub_summary)
    (imp_root / "index.html").write_text(hub_html, encoding="utf-8")

    return hub_summary


def main() -> None:
    res = build_all()
    print(
        f"Built Fieldglass R2 Improvements Hub: {res['subject_count']} subjects, "
        f"{res['total_improvements']} improvements."
    )
    for subj in res["subjects"]:
        m = subj["metrics"]
        print(
            f"  - {subj['slug']:13s} | A_0.10 {m['past_a_tau']}->{m['future_a_tau']} | "
            f"A_0.14 {m['past_a014']}->{m['future_a014']} | EI={m['effective_information_bits']:.4f}b | "
            f"sha256={m['report_sha256'][:12]}..."
        )


if __name__ == "__main__":
    main()
