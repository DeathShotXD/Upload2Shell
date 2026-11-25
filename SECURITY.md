# Security

## Read this first

This is a lab reproducer plus a client for authorized testing of
CVE-2026-125396. The exploit really does run code as the CUPS filter account:
it clears `-dSAFER`'s native path control and then runs your command. So point
it only at:

- the Docker labs in this repo;
- a box you own;
- a box you have written permission to test, with a scope on record;
- a bug-bounty target whose published scope actually covers the host and its
  print service.

Not at a live third-party CUPS server, not at a shared queue, not at anything
in government or defence. And not to read other people's data, leave anything
behind, or break printing.

## The CVE

Paulos Yibelo (pwn.ai) found CVE-2026-125396 and published it on 21 Nov 2026.
Ghostscript 10.08.0 fixes it. I did not find it. This repo is my own chain for
Debian 13 / Ubuntu 22.04 / Ubuntu 24.04, plus a small standalone IPP client.

## Reporting something in this repo

Use GitHub's private vulnerability reporting (Security -> Report a
vulnerability). Please do not open a public issue for a scope-guard bypass, a
payload that fires on a patched build, or anything that could take a target
down.

## Output and secrets

The labs use throwaway credentials in a disposable container. If you run
`--cmd` against anything real, the output can contain secrets. Treat it that
way and do not commit it.

## Versions

0.2.x, Python 3.9+. The client is standard library only. The labs want Docker
(Docker Compose if you wire up several distros).
