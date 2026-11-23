"""Unit tests for tools/fetch_series_status.py, against a local http.server. No internet needed.

Run: python -m unittest discover -s tests
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_series_status as css  # noqa: E402
import fetch_series_status as fss  # noqa: E402
import render_views as rv  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "series-status"
P2, P6 = "uas-sec-p2-verified-boot", "uas-sec-oscal"


class Handler(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, bytes]] = {}

    def do_GET(self):  # noqa: N802 (http.server API)
        status, body = self.routes.get(self.path, (404, b"404: Not Found"))
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class FetchSeriesStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}/samyoon727ca"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.routes = {}
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name) / "series-status"

    def serve(self, repo: str, body: bytes, status: int = 200) -> None:
        Handler.routes[f"/samyoon727ca/{repo}/HEAD/series-status.json"] = (status, body)

    def fetch(self, base: str | None = None) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fss.main(["--base-url", base or self.base, "--out-dir", str(self.out)])
        return code, buf.getvalue()

    def check(self) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return css.main([str(p) for p in sorted(self.out.glob("*.json"))])

    def test_success_writes_snapshot_that_checks_and_renders(self):
        body = (FIXTURES / "valid.json").read_bytes()
        self.serve(P2, body)
        code, out = self.fetch()
        self.assertEqual(code, 0, out)
        self.assertEqual((self.out / f"{P2}.json").read_bytes(), body)
        self.assertEqual([p.name for p in self.out.iterdir()], [f"{P2}.json"])
        self.assertEqual(self.check(), 0)
        table = rv.series_table(snapshot_dir=self.out)
        self.assertIn("partly evidenced: [VE-07](https://github.com/samyoon727ca/uas-sec-p2-verified-boot/blob/", table)

    def test_404_warns_and_keeps_existing_snapshot(self):
        self.out.mkdir()
        old = self.out / f"{P2}.json"
        old.write_bytes(b"previous")
        code, out = self.fetch()
        self.assertEqual(code, 0, out)
        self.assertIn(f"WARNING {P2}:", out)
        self.assertIn("kept the existing snapshot", out)
        self.assertEqual(old.read_bytes(), b"previous")
        self.assertEqual(len([line for line in out.splitlines() if line.startswith("WARNING")]), 5)

    def test_snapshot_of_repo_not_in_series_csv_is_removed(self):
        self.out.mkdir()
        stale = self.out / "uas-sec-retired.json"
        stale.write_bytes(b"{}")
        p1 = self.out / "uas-sec-p1-architecture.json"
        p1.write_bytes(b"{}")
        kept = self.out / f"{P2}.json"
        kept.write_bytes(b"previous")
        other = self.out / "README.md"
        other.write_text("notes")
        code, out = self.fetch()
        self.assertEqual(code, 0, out)
        self.assertIn("REMOVED", out)
        self.assertFalse(stale.exists())
        self.assertFalse(p1.exists())
        self.assertEqual(kept.read_bytes(), b"previous")
        self.assertTrue(other.exists())

    def test_other_http_error_fails(self):
        self.serve(P2, b"oops", status=500)
        code, out = self.fetch()
        self.assertEqual(code, 1)
        self.assertIn(f"ERROR   {P2}:", out)
        self.assertFalse((self.out / f"{P2}.json").exists())

    def test_malformed_json_is_written_then_rejected_by_checker(self):
        self.serve(P2, b'{"p_id": "P2",')
        code, out = self.fetch()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.check(), 1)

    def test_ve_claimed_outside_allocation_is_rejected_by_checker(self):
        self.serve(P6, (FIXTURES / "p6-claims-ve07.json").read_bytes())
        self.assertEqual(self.fetch()[0], 0)
        self.assertEqual(self.check(), 1)

    def test_file_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / P2 / "HEAD" / "series-status.json"
            src.parent.mkdir(parents=True)
            src.write_bytes((FIXTURES / "valid.json").read_bytes())
            code, out = self.fetch(Path(tmp).as_uri())
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("WARNING"), 4)
        self.assertTrue((self.out / f"{P2}.json").is_file())


if __name__ == "__main__":
    unittest.main()
