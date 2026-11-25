"""Range-capable loopback showcase server + Android/Pixel USB ADB pusher."""

from __future__ import annotations

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def make_range_handler(root: Path):
    root_str = str(root.resolve())

    class RangeHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root_str, **kwargs)

        def send_head(self):
            path = self.translate_path(self.path)
            if os.path.isdir(path):
                return super().send_head()
            range_hdr = self.headers.get("Range")
            if not range_hdr or not os.path.isfile(path):
                return super().send_head()
            m = RANGE_RE.match(range_hdr.strip())
            if not m:
                return super().send_head()
            f = open(path, "rb")
            size = os.fstat(f.fileno()).st_size
            start_s, end_s = m.groups()
            start = int(start_s) if start_s else 0
            end = min(int(end_s) if end_s else size - 1, size - 1)
            if start > end or start >= size:
                f.close()
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return None
            length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            f.seek(start)
            self._range_remaining = length
            return f

        def copyfile(self, source, outputfile):
            remaining = getattr(self, "_range_remaining", None)
            if remaining is None:
                return super().copyfile(source, outputfile)
            self._range_remaining = None
            while remaining > 0:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)

    return RangeHandler


def serve_directory(root: str | Path, *, host: str = "127.0.0.1", port: int = 8776) -> None:
    """Serve a Fieldglass showcase directory over loopback HTTP with Range support."""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Fieldglass showcase binds loopback-only by default (127.0.0.1).")
    target = Path(root).expanduser().resolve()
    srv = ThreadingHTTPServer((host, int(port)), make_range_handler(target))
    print(f"Fieldglass showcase live at http://{host}:{port}/ (root={target})", flush=True)
    srv.serve_forever()


def push_to_pixel_adb(
    bundle_dir: str | Path,
    *,
    remote_name: str = "fieldglass",
    port: int = 8776,
    open_browser: bool = True,
) -> dict[str, Any]:
    """Push a Fieldglass showcase bundle to an authorized Android/Pixel device via USB ADB."""
    adb = shutil.which("adb")
    if not adb:
        raise FileNotFoundError("adb not found on PATH")
    proc = subprocess.run([adb, "devices"], capture_output=True, text=True, check=True)
    serial = ""
    for line in proc.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            serial = parts[0]
            break
    if not serial:
        raise RuntimeError("No authorized Android/Pixel device detected via `adb devices`.")

    src = Path(bundle_dir).expanduser().resolve()
    remote_dir = f"/sdcard/Download/{remote_name}"
    subprocess.run([adb, "-s", serial, "shell", f"mkdir -p {remote_dir}"], check=True)
    for item in sorted(src.iterdir()):
        if item.name.startswith("."):
            continue
        subprocess.run([adb, "-s", serial, "push", str(item), f"{remote_dir}/"], check=True)

    subprocess.run([adb, "-s", serial, "reverse", f"tcp:{port}", f"tcp:{port}"], check=True)
    if open_browser:
        subprocess.run(
            [adb, "-s", serial, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"http://127.0.0.1:{port}/"],
            check=True,
        )
    return {"ok": True, "serial": serial, "remote_dir": remote_dir, "url": f"http://127.0.0.1:{port}/"}
