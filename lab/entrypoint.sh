#!/bin/sh
# Upload2Shell lab: Debian 13 + vulnerable Ghostscript + anonymous shared CUPS queue.
set -e

mkdir -p /run/cups /var/log/cups /var/spool/cups

# CUPS blocks the file: backend by default; the lab prints to a file.
if grep -q '^#FileDevice No' /etc/cups/cups-files.conf; then
    sed -i 's/^#FileDevice No/FileDevice Yes/' /etc/cups/cups-files.conf
fi
grep -q '^FileDevice' /etc/cups/cups-files.conf || echo 'FileDevice Yes' >> /etc/cups/cups-files.conf

/usr/sbin/cupsd
sleep 1

if ! lpstat -p u2s >/dev/null 2>&1; then
    lpadmin -p u2s -E -v file:/tmp/u2s_cups.pdf -P /etc/cups/u2s.ppd
fi

echo "[*] cupsd up; shared queue 'u2s' ready on :631"
exec tail -f /dev/null
