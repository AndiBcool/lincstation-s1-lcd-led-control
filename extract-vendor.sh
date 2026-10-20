#!/usr/bin/env bash
# Extract the LincStation S1 vendor executable from the official recovery ZIP/ISO.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "Run with sudo/root." >&2; exit 1; fi
if [[ $# -ne 1 || ! -f "$1" ]]; then echo "Usage: sudo bash scripts/extract-vendor.sh /path/to/LincStation-S1-recovery.zip" >&2; exit 2; fi
if systemctl is-active --quiet lincstation-display.service || systemctl is-active --quiet lincstation-monitor.service; then
  echo "LincStation services are active; refusing to change the vendor executable." >&2; exit 1
fi
command -v 7z >/dev/null || { echo "Missing 7z. Install: apt install p7zip-full" >&2; exit 1; }
command -v unzip >/dev/null || { echo "Missing unzip. Install: apt install unzip" >&2; exit 1; }
ZIP=$(realpath -- "$1")
case "$(basename "$ZIP" | tr '[:upper:]' '[:lower:]')" in *lincstation*s1*unraidserver*.zip) ;; *)
  echo "Expected an official LincStation S1 recovery ZIP; refusing an unrecognized archive name." >&2; exit 1;; esac
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT
# Search ZIP members without unpacking the full firmware bundle.
mapfile -t ISO_MEMBERS < <(unzip -Z -1 "$ZIP" | tr -d '\r' | grep -iE '(^|/)UNRAID\.iso$' || true)
if [[ ${#ISO_MEMBERS[@]} -ne 1 ]]; then echo "Expected exactly one UNRAID.iso in the S1 ZIP; found ${#ISO_MEMBERS[@]}." >&2; exit 1; fi
ISO_MEMBER=${ISO_MEMBERS[0]}
if [[ "$ISO_MEMBER" == /* || "$ISO_MEMBER" == *../* || "$ISO_MEMBER" == *\\* ]]; then echo "Unsafe ISO member path." >&2; exit 1; fi
unzip -p "$ZIP" "$ISO_MEMBER" > "$TMP/UNRAID.iso"
[[ -s "$TMP/UNRAID.iso" ]] || { echo "ISO extraction failed." >&2; exit 1; }
# Inspect the ISO and accept only the documented config/serial/serialtest file.
mapfile -t BIN_MEMBERS < <(7z l -slt "$TMP/UNRAID.iso" | sed -n 's/^Path = //p' | tr -d '\r' | grep -iE '^(/)?config/serial/serialtest$' || true)
if [[ ${#BIN_MEMBERS[@]} -ne 1 ]]; then echo "Expected config/serial/serialtest inside ISO; found ${#BIN_MEMBERS[@]}." >&2; exit 1; fi
7z e -y -so "$TMP/UNRAID.iso" "${BIN_MEMBERS[0]}" > "$TMP/serialtest"
[[ -s "$TMP/serialtest" ]] || { echo "serialtest extraction failed." >&2; exit 1; }
if [[ "$(head -c 4 "$TMP/serialtest" | od -An -tx1 | tr -d ' \n')" != 7f454c46 ]]; then
  echo "Extracted file is not an ELF executable; refusing to install." >&2; exit 1
fi
DEST=/root/lincstation-test/serialtest
if [[ -e "$DEST" ]]; then
  echo "Existing $DEST found. Refusing to overwrite it. Back it up/remove it manually only if intended." >&2; exit 1
fi
install -d -m 0755 /root/lincstation-test
install -m 0755 "$TMP/serialtest" "$DEST"
echo "Vendor serialtest extracted to $DEST. Original monitor and test.sh were not installed."
echo "Next: sudo bash scripts/install.sh (on a fresh, stopped installation)."
