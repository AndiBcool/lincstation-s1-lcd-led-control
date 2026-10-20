#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { echo "Run as root" >&2; exit 1; }
OUT=${1:-/root/lincstation-s1-backup-$(date +%Y%m%d-%H%M%S).tar.gz}
FILES=(root/lincstation-test/debian-monitor.py root/lincstation-test/state-template.json etc/systemd/system/lincstation-monitor.service etc/systemd/system/lincstation-display.service)
[[ -f /etc/systemd/system/lincstation-display.service.d/quiet.conf ]] && FILES+=(etc/systemd/system/lincstation-display.service.d/quiet.conf)
[[ -f /root/lincstation-test/serialtest ]] && FILES+=(root/lincstation-test/serialtest)
tar -czf "$OUT" -C / "${FILES[@]}"
echo "Created $OUT (may include proprietary vendor binary and private configuration; do not publish)."
