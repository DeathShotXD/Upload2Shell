# Security

## The boundary

Upload2Shell is a lab reproducer and an authorized-testing toolkit for
CVE-2026-125396, a use-after-free in Ghostscript's Type 1 font loader.

The exploit disables `-dSAFER`'s native path control and runs a command as the
CUPS filter account. That is real code execution. Use it only on:

- the included local Docker labs;
- a system you own;
- a system you have written permission to test, with a scope record;
- a bug-bounty target whose published scope covers the host and the print
  service.

Do not run it against a live third-party CUPS server, a shared print queue, or
a defence/government system. Do not use it to read other users' data, establish
persistence, or disrupt printing.

## The CVE

CVE-2026-125396 was discovered by Paulos Yibelo / pwn.ai and published on
21 Nov 2026; Ghostscript 10.08.0 fixes it (2026-09-08). This repository does
not claim discovery. It provides an independent, re-derived Debian 13 /
Ubuntu 22.04 / Ubuntu 24.04 chain and a standalone IPP client.

## Reporting a bug here

Use GitHub private vulnerability reporting (Security -> Report a vulnerability).
Do not open a public issue for a scope-guard bypass, a payload that executes on
a patched build, or anything that could crash a target.

## Data handling

The labs use dummy credentials and a disposable container. Do not point
`--cmd` at a production system with real data unless the engagement scope
allows it. Command output can contain secrets; treat it as sensitive and never
commit it.

## Supported versions

0.2.x on Python 3.9+. The client uses only the standard library. The labs need
Docker and Docker Compose.
