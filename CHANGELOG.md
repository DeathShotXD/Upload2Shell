# Changelog

## 0.2.0 - 2026-11-24

- Added the standalone raw-IPP client (`cups_poc.py`): no `lp`, no local
  shell on the target, `--cmd`, `--exfil`, `--json`, loopback-first scope
  guard.
- Added zero-click remote chain: anonymous IPP `Print-Job` → `gstopdf` →
  `gstoraster` → `gs -dSAFER` → CVE-2026-125396 → `%pipe%` as `uid=7(lp)`.
- Verified 3/3 on Debian 13 (10.05.1), Ubuntu 24.04 (10.02.1), Ubuntu 22.04
  (9.55.0).
- Added 9.55/10.x auto-detect: `ref.value.pdevice` is a `gx_device*` in 9.55
  and a `psi_device_ref*` in 10.x.
- Documented the Ubuntu CUPS `file:` backend gap (use `discard://`).
- Added unit tests, CI matrix, and Docker lab job.

## 0.1.0 - 2026-11-21

- Reproduced the published bounded native-write PoC on Debian 13
  `+deb13u1` (5/5) with the fixed-build A/B control (`+deb13u3`).
- Added `fetch-debs.sh` to pin the vulnerable packages from
  snapshot.debian.org.
- Added the Docker lab for the vulnerable Ghostscript build.
