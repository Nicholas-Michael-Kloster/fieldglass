"""Tier 5 white-box adversarial coverage tests for Fieldglass Observatory Expansion."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import http.client
from http.server import ThreadingHTTPServer
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import threading
import urllib.parse

import numpy as np
from PIL import Image
import pytest

from fieldglass import cli, plate
from fieldglass.metrics import (
    a_tau,
    accessible_set,
    causal_chiasm,
    luminance_to_8state,
    normalize_dist,
    persistent_filtration_tomography,
    quartic_purity_m4,
    renyi_h2,
    shannon_h1,
)
from fieldglass.observatory_r1 import (
    CHIASM_CONTRACT,
    EQUATION,
    FlightSim6DOF,
    MedicalSandboxModel,
    SoftwareObservatoryModel,
    canonical_sha256,
    compute_distribution_telemetry,
    isa_density,
)
from fieldglass.showcase import make_range_handler

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


def _find_node_bin() -> str:
    found = shutil.which("node")
    if found:
        return found
    nvm_node = Path("/home/cowboy/.nvm/versions/node/v24.16.0/bin/node")
    if nvm_node.is_file():
        return str(nvm_node)
    pytest.skip("node binary not found for JS VM execution test")
    return ""


def test_t5_metrics_rejects_nonfinite_and_bool_weights() -> None:
    for bad_w in (float("nan"), float("inf"), float("-inf"), True, False):
        with pytest.raises(ValueError):
            normalize_dist({"a": bad_w, "b": 1.0})
    with pytest.raises(ValueError):
        normalize_dist({"a": 1.0, "b": False})

    for bad_tau in (float("nan"), float("inf"), float("-inf"), True, False):
        with pytest.raises(ValueError):
            a_tau([0.5, 0.5], bad_tau)
        with pytest.raises(ValueError):
            accessible_set({"a": 0.5, "b": 0.5}, bad_tau)
        with pytest.raises(ValueError):
            causal_chiasm({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.5}, tau=bad_tau)

    with pytest.raises(ValueError):
        persistent_filtration_tomography([{"a": 0.5, "b": 0.5}], thresholds=[float("nan")])
    with pytest.raises(ValueError):
        persistent_filtration_tomography([{"a": 0.5, "b": 0.5}], invariant_tau=float("inf"))
    with pytest.raises(ValueError):
        renyi_h2([])
    with pytest.raises(ValueError):
        renyi_h2([float("nan"), 0.5])


def test_t5_medical_sandbox_rejects_nonfinite_and_bool_scalars() -> None:
    for bad in (float("nan"), float("inf"), float("-inf"), True, False):
        with pytest.raises(ValueError):
            MedicalSandboxModel.ecg_pqrst(bad, 72.0)
        with pytest.raises(ValueError):
            MedicalSandboxModel.ecg_pqrst(0.3, bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.ecg_trace(hr_bpm=bad)

        with pytest.raises(ValueError):
            MedicalSandboxModel.spo2_beer_lambert(bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.spo2_beer_lambert(0.6, perfusion_index=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.spo2_beer_lambert(0.6, t_sec=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.spo2_beer_lambert(0.6, hr_bpm=bad)

        with pytest.raises(ValueError):
            MedicalSandboxModel.capnography_waveform(bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.capnography_waveform(0.5, rr_bpm=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.capnography_waveform(0.5, etco2_mmhg=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.capnography_trace(rr_bpm=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.capnography_trace(etco2_mmhg=bad)

        with pytest.raises(ValueError):
            MedicalSandboxModel.ventilator_pv_loop(compliance_ml_cmh2o=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.ventilator_pv_loop(resistance_cmh2o_l_s=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.ventilator_pv_loop(vt_ml=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.ventilator_pv_loop(peep_cmh2o=bad)
        with pytest.raises(ValueError):
            MedicalSandboxModel.ventilator_pv_loop(n_pts=bad)  # type: ignore[arg-type]


def test_t5_flight_sim_rejects_nonfinite_controls_and_altitude() -> None:
    sim = FlightSim6DOF()
    with pytest.raises(ValueError):
        sim.step(0.05, throttle=float("nan"))
    with pytest.raises(ValueError):
        sim.step(0.05, pitch_cmd=float("inf"))
    with pytest.raises(ValueError):
        sim.step(0.05, roll_cmd=float("-inf"))
    with pytest.raises(ValueError):
        sim.step(0.05, rudder_cmd=float("nan"))
    with pytest.raises(ValueError):
        sim.step(0.05, throttle=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        isa_density(float("nan"))
    with pytest.raises(ValueError):
        isa_density(float("inf"))
    with pytest.raises(ValueError):
        isa_density(True)  # type: ignore[arg-type]


def test_t5_chiasm_bundle_rejects_bool_tokens_and_nan_sealing() -> None:
    forged = {
        "contract": CHIASM_CONTRACT,
        "equation": EQUATION,
        "executed": False,
        "sentience_claimed": False,
        "tokens_used": False,
    }
    forged["report_sha256"] = canonical_sha256(forged)
    res = SoftwareObservatoryModel.verify_chiasm_bundle(forged)
    assert res["valid"] is False
    assert res["safety_invariants_ok"] is False

    non_dict = SoftwareObservatoryModel.verify_chiasm_bundle(["invalid"])  # type: ignore[arg-type]
    assert non_dict["valid"] is False

    with pytest.raises(ValueError):
        canonical_sha256({"x": float("nan")})
    with pytest.raises(ValueError):
        SoftwareObservatoryModel.evaluate_repertoire({"a": 0.5, "b": 0.5}, tau=float("nan"))
    with pytest.raises(ValueError):
        compute_distribution_telemetry(
            [{"a": 0.5, "b": 0.5}, {"a": 0.6, "b": 0.4}],
            tau=float("nan"),
        )


def test_t5_showcase_range_handler_suffix_and_invalid_ranges(tmp_path: Path) -> None:
    sample = tmp_path / "sample.bin"
    payload = bytes(range(100))
    sample.write_bytes(payload)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_range_handler(tmp_path))
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        # 1. Suffix range bytes=-10 -> last 10 bytes (90..99)
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", "/sample.bin", headers={"Range": "bytes=-10"})
        resp = conn.getresponse()
        body = resp.read()
        cr = resp.getheader("Content-Range")
        conn.close()
        assert resp.status == 206
        assert cr == "bytes 90-99/100"
        assert body == payload[90:]

        # 2. Suffix > file size bytes=-200 -> full file 0..99
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", "/sample.bin", headers={"Range": "bytes=-200"})
        resp = conn.getresponse()
        body = resp.read()
        cr = resp.getheader("Content-Range")
        conn.close()
        assert resp.status == 206
        assert cr == "bytes 0-99/100"
        assert body == payload

        # 3. Zero suffix bytes=-0 -> 416
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", "/sample.bin", headers={"Range": "bytes=-0"})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        assert resp.status == 416

        # 4. Empty bounds bytes=- -> NOT 206
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", "/sample.bin", headers={"Range": "bytes=-"})
        resp = conn.getresponse()
        resp.read()
        conn.close()
        assert resp.status in (200, 416)

        # 5. HEAD with Range: bytes=0-9 -> 206, Content-Length 10, empty body
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("HEAD", "/sample.bin", headers={"Range": "bytes=0-9"})
        resp = conn.getresponse()
        body = resp.read()
        cl = resp.getheader("Content-Length")
        conn.close()
        assert resp.status == 206
        assert cl == "10"
        assert body == b""
    finally:
        srv.shutdown()
        srv.server_close()


def test_t5_zoe_hospital_win7_python_and_http_adversarial() -> None:
    server_path = DOCS_DIR / "zoe-hospital" / "zoe_hospital_win7.py"
    spec = importlib.util.spec_from_file_location("zoe_hospital_win7_t5", server_path)
    assert spec is not None and spec.loader is not None
    zh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(zh)

    for bad in (float("nan"), float("inf"), float("-inf"), True):
        with pytest.raises(ValueError):
            zh.normalize_dist({"a": bad, "b": 1.0})
    with pytest.raises(ValueError):
        zh.compute_chiasm(zh.DEFAULT_PAST, zh.DEFAULT_FUTURE, tau=float("nan"))

    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONIOENCODING": "cp1252"}
    srv_proc = subprocess.Popen(
        ["/usr/bin/python3", str(server_path), "--port", "0", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert srv_proc.stdout is not None
        url = ""
        for _ in range(10):
            line = srv_proc.stdout.readline()
            if line.startswith("ZOE_HOSPITAL_URL="):
                url = line.split("=", 1)[1].strip()
                break
        assert url.startswith("http://127.0.0.1:")
        parsed = urllib.parse.urlparse(url)
        host, port = parsed.hostname, parsed.port
        assert host == "127.0.0.1" and port is not None

        # GET /api/chiasm?tau=-0.0 -> tau must be positive 0.0
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", "/api/chiasm?tau=-0.0")
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert data["tau"] == 0.0
        assert not (math.copysign(1.0, data["tau"]) < 0)
        assert str(data["tau"]) == "0.0"

        # GET /index.html%00 -> 404 JSON
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("GET", "/index.html%00")
        resp = conn.getresponse()
        body_404 = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 404 and body_404.get("ok") is False

        # HEAD /api/health -> 200 empty body with exact Content-Length
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request("HEAD", "/api/health")
        resp = conn.getresponse()
        head_body = resp.read()
        cl = int(resp.getheader("Content-Length") or "0")
        conn.close()
        assert resp.status == 200 and head_body == b"" and cl > 0

        # Invalid UTF-8 POST /api/metrics -> 400
        conn = http.client.HTTPConnection(host, port, timeout=3)
        conn.request(
            "POST",
            "/api/metrics",
            body=b"\xff\xfe\xfd",
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        resp.read()
        conn.close()
        assert resp.status == 400

        # Disjoint future keys -> effective_information_bits is None
        conn = http.client.HTTPConnection(host, port, timeout=3)
        disjoint_body = json.dumps(
            {
                "tau": 0.10,
                "distribution": {"a": 0.5, "b": 0.5},
                "future": {"x": 0.5, "y": 0.5},
            }
        ).encode("utf-8")
        conn.request(
            "POST",
            "/api/metrics",
            body=disjoint_body,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        disjoint_res = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert resp.status == 200
        assert disjoint_res["chiasm"]["effective_information_bits"] is None

        # 12 concurrent POST /api/metrics -> all 200
        def _post_once(idx: int) -> int:
            c = http.client.HTTPConnection(host, port, timeout=5)
            b = json.dumps({"tau": 0.10, "distribution": {"a": 0.4 + 0.01 * idx, "b": 0.6}}).encode("utf-8")
            c.request("POST", "/api/metrics", body=b, headers={"Content-Type": "application/json"})
            r = c.getresponse()
            r.read()
            c.close()
            return r.status

        with ThreadPoolExecutor(max_workers=12) as pool:
            statuses = list(pool.map(_post_once, range(12)))
        assert statuses == [200] * 12
    finally:
        srv_proc.terminate()
        srv_proc.wait(timeout=5)


def test_t5_zoe_hospital_es5_kiosk_adversarial_vm(tmp_path: Path) -> None:
    node_bin = _find_node_bin()
    zoe_dir = DOCS_DIR / "zoe-hospital"
    for idx, fname in enumerate(("zoe_hospital_kiosk.html", "zoe_hospital_kiosk.hta")):
        html_txt = (zoe_dir / fname).read_text(encoding="utf-8")
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html_txt, flags=re.IGNORECASE | re.DOTALL)
        combined_js = "\n".join(scripts)

        harness = r"""
const vm = require("vm");
const fs = require("fs");
const code = fs.readFileSync(process.argv[2], "utf8");

function makeEl(id) {
  return {
    id: id,
    value: id === "tauSelect" ? "0.10" : "ZOE T5",
    checked: id === "chk0" || id === "chk1",
    className: "",
    style: {},
    textContent: "",
    innerText: "",
    innerHTML: "",
    addEventListener: function () {}
  };
}
const els = {};
const sandbox = {
  Math: Math,
  JSON: JSON,
  Object: Object,
  Array: Array,
  String: String,
  Number: Number,
  Error: Error,
  parseFloat: parseFloat,
  isNaN: isNaN,
  isFinite: isFinite,
  document: {
    getElementById: function (id) {
      if (!els[id]) { els[id] = makeEl(id); }
      return els[id];
    }
  },
  window: null,
  navigator: { userAgent: "MSIE 9.0; Windows NT 6.1" }
};
sandbox.window = sandbox;
vm.runInNewContext(code, sandbox, { filename: process.argv[2] });
const K = sandbox.ZoeHospitalKiosk;

let infThrew = false;
try { K.normalizeDist({ a: Infinity, b: 1 }); } catch (e) { infThrew = true; }
if (!infThrew) { throw new Error("normalizeDist accepted Infinity"); }

const disjoint = K.causalChiasm({ a: 0.5, b: 0.5 }, { x: 0.5, y: 0.5 }, 0.10, 4);
if (disjoint.effective_information_bits !== null) {
  throw new Error("Expected null EI for disjoint keys, got " + disjoint.effective_information_bits);
}

let nanTauThrew = false;
try { K.causalChiasm({ a: 0.5, b: 0.5 }, { a: 0.5, b: 0.5 }, NaN, 4); } catch (e) { nanTauThrew = true; }
if (!nanTauThrew) { throw new Error("causalChiasm accepted NaN tau"); }

K.clearCommLog();
K.selectCommTile(99);
const logText = els.commLogBox.textContent || els.commLogBox.innerText;
if (logText.indexOf("[TILE 1]") !== 0 || logText.indexOf("[TILE 100]") !== -1) {
  throw new Error("Unexpected OOB tile log: " + logText);
}
console.log(JSON.stringify({ ok: true }));
"""
        script_tmp = tmp_path / f"_t5_kiosk_{idx}.js"
        harness_tmp = tmp_path / f"_t5_kiosk_harness_{idx}.cjs"
        script_tmp.write_text(combined_js, encoding="utf-8")
        harness_tmp.write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            [node_bin, str(harness_tmp), str(script_tmp)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert json.loads(proc.stdout.strip())["ok"] is True


def test_t5_r1_software_and_medical_ui_adversarial_vm(tmp_path: Path) -> None:
    node_bin = _find_node_bin()

    # 1. Software UI: INVALID JSON badge color + tampered contract check
    sw_html = (DOCS_DIR / "software" / "index.html").read_text(encoding="utf-8")
    sw_scripts = re.findall(r"<script[^>]*>(.*?)</script>", sw_html, flags=re.IGNORECASE | re.DOTALL)
    assert len(sw_scripts) == 1
    sw_harness = r"""
const vm = require("vm");
const fs = require("fs");
const crypto = require("crypto");
const code = fs.readFileSync(process.argv[2], "utf8");

const els = {};
function makeEl(id) {
  return {
    id: id || "",
    value: "10",
    style: {},
    textContent: "",
    innerHTML: "",
    width: 520,
    height: 190,
    _listeners: {},
    addEventListener: function (ev, fn) { this._listeners[ev] = fn; },
    appendChild: function () {},
    querySelectorAll: function () { return []; },
    getAttribute: function () { return ""; },
    getContext: function () {
      return {
        fillStyle: "", strokeStyle: "", lineWidth: 1, font: "",
        fillRect: function () {}, beginPath: function () {}, moveTo: function () {},
        lineTo: function () {}, stroke: function () {}, setLineDash: function () {},
        fillText: function () {}
      };
    }
  };
}
const sandbox = {
  Math: Math, JSON: JSON, Object: Object, Array: Array, String: String,
  Number: Number, Error: Error, encodeURIComponent: encodeURIComponent,
  unescape: unescape,
  document: {
    getElementById: function (id) {
      if (!els[id]) { els[id] = makeEl(id); }
      return els[id];
    },
    createElement: function (tag) { return makeEl(tag); }
  }
};
vm.runInNewContext(code, sandbox, { filename: process.argv[2] });

// Bad JSON
els.reportJsonBox.value = "{bad json";
els.verifyShaBtn._listeners.click();
if (els.shaBadge.textContent !== "INVALID JSON") {
  throw new Error("Expected INVALID JSON badge, got " + els.shaBadge.textContent);
}
if (els.shaBadge.style.color !== "#f46a7e") {
  throw new Error("Expected ruby #f46a7e on INVALID JSON, got " + els.shaBadge.style.color);
}

// Tampered contract with matching recomputed SHA-256
els.resetJsonBtn._listeners.click();
const parsed = JSON.parse(els.reportJsonBox.value);
parsed.contract = "tampered-contract/v0";
delete parsed.report_sha256;
function sortDeep(v) {
  if (Array.isArray(v)) return v.map(sortDeep);
  if (v && typeof v === "object") {
    const o = {};
    Object.keys(v).sort().forEach(k => { o[k] = sortDeep(v[k]); });
    return o;
  }
  return v;
}
const canon = JSON.stringify(sortDeep(parsed)).replace(/[\u007f-\uffff]/g, ch =>
  "\\u" + ("0000" + ch.charCodeAt(0).toString(16)).slice(-4)
);
parsed.report_sha256 = crypto.createHash("sha256").update(canon, "utf8").digest("hex");
els.reportJsonBox.value = JSON.stringify(parsed);
els.verifyShaBtn._listeners.click();
if (els.shaBadge.textContent !== "SEAL MISMATCH" || els.shaBadge.style.color !== "#f46a7e") {
  throw new Error("Expected SEAL MISMATCH on tampered contract, got " + els.shaBadge.textContent);
}
console.log(JSON.stringify({ ok: true }));
"""
    sw_js = tmp_path / "_t5_sw.js"
    sw_h = tmp_path / "_t5_sw_harness.cjs"
    sw_js.write_text(sw_scripts[0], encoding="utf-8")
    sw_h.write_text(sw_harness, encoding="utf-8")
    proc_sw = subprocess.run([node_bin, str(sw_h), str(sw_js)], capture_output=True, text=True, check=True)
    assert json.loads(proc_sw.stdout.strip())["ok"] is True

    # 2. Medical UI: 1e308 * 1e308 overflow -> Validation error (not Infinity)
    med_html = (DOCS_DIR / "medical-sim" / "index.html").read_text(encoding="utf-8")
    med_scripts = re.findall(r"<script[^>]*>(.*?)</script>", med_html, flags=re.IGNORECASE | re.DOTALL)
    assert len(med_scripts) == 1
    med_harness = r"""
const vm = require("vm");
const fs = require("fs");
const code = fs.readFileSync(process.argv[2], "utf8");

const defaults = {
  hrSlider: "72", rSlider: "60", rrSlider: "14", cSlider: "50",
  vtSlider: "480", peepSlider: "5", infDose: "5", infWeight: "70", infConc: "1000"
};
const els = {};
function makeEl(id) {
  return {
    id: id,
    value: defaults[id] || "0",
    style: {},
    textContent: "",
    innerHTML: "",
    width: 640,
    height: 360,
    _listeners: {},
    addEventListener: function (ev, fn) { this._listeners[ev] = fn; },
    getContext: function () {
      return {
        fillStyle: "", strokeStyle: "", lineWidth: 1, font: "",
        fillRect: function () {}, beginPath: function () {}, moveTo: function () {},
        lineTo: function () {}, stroke: function () {}, fillText: function () {}
      };
    }
  };
}
const sandbox = {
  Math: Math, JSON: JSON, Object: Object, Array: Array, String: String,
  Number: Number, Error: Error,
  document: {
    getElementById: function (id) {
      if (!els[id]) { els[id] = makeEl(id); }
      return els[id];
    }
  }
};
vm.runInNewContext(code, sandbox, { filename: process.argv[2] });

els.infDose.value = "1e308";
els.infWeight.value = "1e308";
els.infConc.value = "1";
els.infDose._listeners.input();
const txt = els.infOut.textContent;
if (txt.indexOf("Validation error") === -1 || txt.indexOf("Infinity") !== -1) {
  throw new Error("Expected overflow Validation error without Infinity, got: " + txt);
}
console.log(JSON.stringify({ ok: true }));
"""
    med_js = tmp_path / "_t5_med.js"
    med_h = tmp_path / "_t5_med_harness.cjs"
    med_js.write_text(med_scripts[0], encoding="utf-8")
    med_h.write_text(med_harness, encoding="utf-8")
    proc_med = subprocess.run([node_bin, str(med_h), str(med_js)], capture_output=True, text=True, check=True)
    assert json.loads(proc_med.stdout.strip())["ok"] is True


def test_t5_metrics_and_r1_reject_numpy_bool_and_bool_ndarrays() -> None:
    bool_arr = np.array([True, False])
    with pytest.raises(ValueError):
        a_tau(bool_arr, 0.1)
    with pytest.raises(ValueError):
        shannon_h1(bool_arr)
    with pytest.raises(ValueError):
        renyi_h2(bool_arr)
    with pytest.raises(ValueError):
        quartic_purity_m4(bool_arr)
    with pytest.raises(ValueError):
        luminance_to_8state(np.ones(256, dtype=bool))
    with pytest.raises(ValueError):
        a_tau([np.bool_(True), 0.5], 0.1)
    with pytest.raises(ValueError):
        a_tau([[np.bool_(True), 0.5]], 0.1)
    with pytest.raises(ValueError):
        a_tau(np.array([np.bool_(True), 0.5], dtype=object), 0.1)
    with pytest.raises(ValueError):
        a_tau([0.5, 0.5], np.bool_(True))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        normalize_dist({"a": np.bool_(True), "b": 1.0})  # type: ignore[dict-item]
    with pytest.raises(ValueError):
        normalize_dist({"a": 1.0, "b": np.bool_(False)})  # type: ignore[dict-item]
    with pytest.raises(ValueError):
        MedicalSandboxModel.ecg_pqrst(np.bool_(True), 72.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        FlightSim6DOF().step(0.05, throttle=np.bool_(True))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        isa_density(np.bool_(True))  # type: ignore[arg-type]


def test_t5_plate_and_cli_reject_nan_collinear_and_empty_inputs(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        plate.perspective_deskew(
            Image.new("RGB", (100, 100)),
            [(float("nan"), 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        )
    with pytest.raises(ValueError):
        plate.perspective_deskew(
            Image.new("RGB", (100, 100)),
            [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4)],
        )
    with pytest.raises(ValueError):
        plate.perspective_deskew(
            Image.new("RGB", (0, 0)),
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        )
    with pytest.raises(ValueError):
        plate.perspective_deskew(
            Image.new("RGB", (100, 100)),
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
            out_size=(0, 100),
        )
    with pytest.raises(ValueError):
        plate.trace_ink_to_svg(
            np.full((32, 32), np.nan, dtype=np.float32),
            tmp_path / "nan.svg",
        )
    with pytest.raises(ValueError):
        plate.trace_ink_to_svg(
            np.zeros((0, 0), dtype=np.float32),
            tmp_path / "empty.svg",
        )
    with pytest.raises(ValueError):
        plate.trace_ink_to_svg(
            np.ones((8, 8), dtype=bool),
            tmp_path / "bool.svg",
        )
    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_corners("nan,0,1,0,1,1,0,1")
    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_corners("inf,0,1,0,1,1,0,1")


def test_t5_plate_out_size_and_braille_validation() -> None:
    img = Image.new("RGB", (100, 100))
    unit_quad = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for bad_out_size in (
        (0.5, 20),
        (10.5, 20),
        ("10", "20"),
        None,
        10,
        (np.array(True, dtype=object), 20),
        (True, 20),
        (np.bool_(True), 20),
        (-4, 20),
    ):
        with pytest.raises(ValueError):
            plate.perspective_deskew(img, unit_quad, out_size=bad_out_size)  # type: ignore[arg-type]

    for bad_ink in (
        np.full((8, 8), np.nan, dtype=np.float32),
        np.ones((8, 8), dtype=bool),
        np.zeros((0, 0), dtype=np.float32),
        np.ones(8, dtype=np.float32),
        [[True, 0.0], [0.0, 1.0]],
    ):
        with pytest.raises(ValueError):
            plate.ink_to_braille_lines(bad_ink)  # type: ignore[arg-type]


def test_t5_scalar_object_bool_and_luminance_2d_rejected() -> None:
    obj_bool = np.array(True, dtype=object)
    nested_obj_bool = np.empty((), dtype=object)
    nested_obj_bool[()] = np.array(np.bool_(False), dtype=object)

    for bad_scalar in (obj_bool, nested_obj_bool):
        with pytest.raises(ValueError):
            a_tau([0.5, 0.5], bad_scalar)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            normalize_dist({"a": bad_scalar, "b": 1.0})  # type: ignore[dict-item]
        with pytest.raises(ValueError):
            accessible_set({"a": 0.5, "b": 0.5}, bad_scalar)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            causal_chiasm({"a": 0.5, "b": 0.5}, {"a": 0.5, "b": 0.5}, tau=bad_scalar)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            persistent_filtration_tomography([{"a": 0.5, "b": 0.5}], invariant_tau=bad_scalar)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            MedicalSandboxModel.ecg_pqrst(bad_scalar, 72.0)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            FlightSim6DOF().step(0.05, throttle=bad_scalar)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            isa_density(bad_scalar)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            plate.perspective_deskew(
                Image.new("RGB", (100, 100)),
                [(bad_scalar, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],  # type: ignore[list-item]
            )

    with pytest.raises(ValueError):
        plate.perspective_deskew(
            Image.new("RGB", (100, 100)),
            [(np.array([0.0]), 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],  # type: ignore[list-item]
        )
    with pytest.raises(ValueError):
        luminance_to_8state(np.ones((256, 2)))
    with pytest.raises(ValueError):
        luminance_to_8state(np.ones((256, 1)))
    with pytest.raises(ValueError):
        luminance_to_8state(np.ones((256, 2, 2)))
