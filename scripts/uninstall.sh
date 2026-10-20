#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "Please run as root" >&2; exit 1; fi
systemctl disable --now lincstation-display.service lincstation-monitor.service || true
rm -f /etc/systemd/system/lincstation-display.service /etc/systemd/system/lincstation-monitor.service /etc/systemd/system/lincstation-display.service.d/quiet.conf
rmdir /etc/systemd/system/lincstation-display.service.d 2>/dev/null || true
systemctl daemon-reload
printf 'Services removed. Files under /root/lincstation-test were intentionally preserved.\n'
