# Changelog

## 0.2.0 - 2026-11-24

- new standalone raw-IPP client (`cups_poc.py`). No `lp`, no shell on the
  target: `--cmd`, `--exfil`, `--json`, and a loopback-first scope guard.
- full zero-click chain wired up: anonymous IPP `Print-Job` through `gstopdf`
  and `gstoraster` into `gs -dSAFER`, then CVE-2026-125396, then `%pipe%` as
  `uid=7(lp)`.
- 3/3 on Debian 13 (10.05.1), Ubuntu 24.04 (10.02.1) and Ubuntu 22.04 (9.55.0).
- 9.55/10.x auto-detect: `ref.value.pdevice` is a `gx_device*` on 9.55 and a
  `psi_device_ref*` on 10.x.
- wrote up the Ubuntu CUPS `file:` backend gap; use `discard://` instead.
- unit tests, a CI matrix, and a Docker lab job.

## 0.1.0 - 2026-11-21

- reproduced the published bounded native-write PoC on Debian 13 `+deb13u1`
  (5/5), with the fixed `+deb13u3` build as an A/B control.
- `fetch-debs.sh` pins the vulnerable packages from snapshot.debian.org.
- Docker lab for the vulnerable Ghostscript build.
