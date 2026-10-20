#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "Please run as root (sudo)." >&2; exit 1; fi
if systemctl is-active --quiet lincstation-monitor.service || systemctl is-active --quiet lincstation-display.service; then
  echo "Existing LincStation service is running. Refusing to modify a live installation." >&2
  echo "Stop services during a planned maintenance window, or use backup.sh only." >&2
  exit 1
fi
LINK=/var/unraid-systemMonitor/state.json
if [[ -L "$LINK" && "$(readlink "$LINK")" != /run/lincstation/state.json ]]; then
  echo "Unexpected existing symlink: $LINK" >&2; exit 1
elif [[ -e "$LINK" && ! -L "$LINK" ]]; then
  echo "Existing non-symlink: $LINK; refusing to replace" >&2; exit 1
fi
BASE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEST=/root/lincstation-test
if [[ ! -f "$DEST/serialtest" ]]; then
  echo "Missing vendor serialtest binary: $DEST/serialtest" >&2
  echo "Obtain it from a source you are authorized to use; see README." >&2
  exit 1
fi
if [[ ! -x "$DEST/serialtest" ]]; then echo "Vendor binary is not executable: $DEST/serialtest" >&2; exit 1; fi
command -v smartctl >/dev/null || { echo "Install smartmontools first: apt install smartmontools" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 is required" >&2; exit 1; }
[[ -e /dev/ttyS0 ]] || { echo "Warning: /dev/ttyS0 not found" >&2; }
mkdir -p "$DEST" /etc/systemd/system/lincstation-display.service.d
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="$DEST/github-install-backup-$STAMP"
mkdir -p "$BACKUP"
for p in "$DEST/debian-monitor.py" "$DEST/state-template.json" /etc/systemd/system/lincstation-monitor.service /etc/systemd/system/lincstation-display.service /etc/systemd/system/lincstation-display.service.d/quiet.conf; do
  if [[ -f "$p" ]]; then cp -a "$p" "$BACKUP/$(basename "$p")"; fi
done
install -m 0644 "$BASE/src/debian-monitor.py" "$DEST/debian-monitor.py"
if [[ ! -f "$DEST/state-template.json" ]]; then
  install -m 0644 "$BASE/config/state-template.json" "$DEST/state-template.json"
  echo "Review disk and network mappings in $DEST/state-template.json and $DEST/debian-monitor.py before starting."
fi
install -m 0644 "$BASE/systemd/lincstation-monitor.service" /etc/systemd/system/
install -m 0644 "$BASE/systemd/lincstation-display.service" /etc/systemd/system/
install -m 0644 "$BASE/systemd/quiet.conf" /etc/systemd/system/lincstation-display.service.d/quiet.conf
# The vendor program expects this compatibility path.
mkdir -p /var/unraid-systemMonitor
LINK=/var/unraid-systemMonitor/state.json
if [[ -L "$LINK" ]]; then
  [[ "$(readlink "$LINK")" == /run/lincstation/state.json ]] || { echo "Unexpected existing symlink: $LINK" >&2; exit 1; }
elif [[ -e "$LINK" ]]; then
  echo "Refusing to replace existing $LINK. Resolve manually." >&2
  exit 1
else
  ln -s /run/lincstation/state.json "$LINK"
fi
python3 -m py_compile "$DEST/debian-monitor.py"
systemctl daemon-reload
echo "Files installed; existing services were NOT restarted."
echo "Backup: $BACKUP"
echo "For fresh installations: python3 $BASE/scripts/configure.py (review slot mapping)."
echo "After confirming the slot mapping, run: systemctl enable --now lincstation-monitor.service lincstation-display.service"
echo "If already active and you want new code loaded, restart monitor then display during maintenance."
