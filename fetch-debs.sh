#!/usr/bin/env bash
# Fetch the last vulnerable Debian 13 Ghostscript build from snapshot.debian.org.
# Fixed in 10.05.1~dfsg-1+deb13u2 (trixie-security).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p debs
base=https://snapshot.debian.org
for p in \
  "/archive/debian-security/20251011T081951Z/pool/updates/main/g/ghostscript/ghostscript_10.05.1~dfsg-1%2Bdeb13u1_amd64.deb" \
  "/archive/debian-security/20251011T081951Z/pool/updates/main/g/ghostscript/libgs10_10.05.1~dfsg-1%2Bdeb13u1_amd64.deb" \
  "/archive/debian-security/20251011T081951Z/pool/updates/main/g/ghostscript/libgs10-common_10.05.1~dfsg-1%2Bdeb13u1_all.deb"; do
  f=$(basename "$p" | sed 's/%2B/+/g')
  [ -f "debs/$f" ] && { echo "have $f"; continue; }
  echo "fetch $f"
  curl -sSL -m 300 "$base$p" -o "debs/$f"
done
for f in debs/*.deb; do dpkg-deb -f "$f" Package Version; done
