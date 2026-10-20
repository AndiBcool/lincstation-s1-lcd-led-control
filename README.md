# LincStation S1 LCD & LED Support for Debian / OpenMediaVault

**🌐 Language / Sprache:** English | [Deutsch](docs/README.de.md)
**Community project — not affiliated with LincStation.**

On some non-vendor operating system installations, including our Debian 12 / OpenMediaVault setup, the LincStation S1's integrated LCD powers on but repeatedly restarts without showing useful values, and disk status LEDs remain off. This project restores the original LCD pages and status LEDs by feeding live Linux metrics to a vendor-provided display controller program.

## Confirmed working setup

- LincStation S1; Debian 12 with OpenMediaVault (one tested machine)
- Original touchscreen LCD pages; disk LEDs and network LED observed working
- CPU usage/temperature/frequency, memory, network/IP/throughput, four disk temperatures and SMART status
- BIOS serial number automatically detected locally at runtime (example uses `UNKNOWN`); ACPI thermal-zone reading (physical sensor location **not confirmed**)
- Two systemd services; reboot-tested

**Not guaranteed on other hardware revisions, OS releases or disk/network mappings.** LCD-reported firmware `30.17` is *not independently verified* as controller firmware; vendor program `serialtest -v` reports `V22.22`.

## How it works

`src/debian-monitor.py` periodically writes JSON to `/run/lincstation/state.json`. The original vendor `serialtest` binary reads `/var/unraid-systemMonitor/state.json`, which must point to that runtime JSON. The vendor binary communicates with the controller on `/dev/ttyS0` (9600 baud observed in the tested setup). The JSON schema and service behavior are based on the working installation.

## Important: vendor component

The **original vendor executable `serialtest` is not distributed** in this repository. You must obtain it from a source you are authorized to use and place it at `/root/lincstation-test/serialtest`. We do not claim rights to redistribute it or its firmware. The Python monitor and repository scripts are separate community-written components. No LCD firmware flashing is required.

## Official S1 recovery package (ZIP containing UNRAID.iso)

LincStation's official recovery instructions provide the S1 package:

- [S1 official Google Drive recovery download](https://drive.google.com/file/d/1cnAWnFPu-5ryIhjftFlg71YqRRDEZJa-/view?usp=sharing)
- Package filename: `LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip`
- Documented path: `ZIP → 7321-unRAIDServer-... → UNRAID.iso → config/serial/serialtest` (and `test.sh`)

Download the archive yourself from the manufacturer's link. On Debian, `sudo apt install unzip p7zip-full` then run `sudo bash scripts/extract-vendor.sh "/path/to/LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip"`. This script extracts **only** `serialtest` without unpacking the full ZIP to disk. It checks the archive filename, expected ISO path and ELF signature, and **refuses to overwrite an existing executable or modify a running installation**. It does not install the original `monitor` or run the Unraid `test.sh`. It has not yet been tested against the actual manufacturer ZIP; paths are based on the documented package layout. Downloading from the vendor does not confer redistribution rights.

## Installation (conservative, manual confirmation required)

1. Install Debian 12 / OpenMediaVault and prerequisites: `sudo apt install python3 smartmontools util-linux kmod unzip p7zip-full`. Confirm `/dev/ttyS0` exists and is not already in use. The installer additionally installs Debian `i2c-tools` through APT if missing, loads `i2c-dev`, and configures it to load on boot. Do **not** install the Unraid `.txz` package on Debian. The vendor includes I²C tooling for its S-series setup; the exact direct dependency of `serialtest` remains unverified.
2. Obtain the vendor **`serialtest`** using the official S1 recovery download and `scripts/extract-vendor.sh` described above (or place a lawfully obtained copy at `/root/lincstation-test/serialtest` and run `chmod 755 /root/lincstation-test/serialtest`). The original `monitor` executable is **not required**: this project replaces its metric collection with Python.
3. Clone/download this repository. Run `bash scripts/install.sh` as root. It installs files but **does not enable or start services**. It refuses to modify an installation while either LincStation service is active.
4. On a fresh machine, run `python3 scripts/configure.py` **after** installation, from the repository directory. It lists candidate disks/interfaces and requires explicit confirmation of physical slot mapping. Never assume `/dev/sda` is always bay 1; review `/root/lincstation-test/hardware-map.json` and `/root/lincstation-test/state-template.json`.
5. Only after confirming mappings, run `systemctl enable --now lincstation-monitor.service lincstation-display.service`.
6. Check `systemctl status lincstation-monitor.service lincstation-display.service`, `/run/lincstation/state.json`, the LCD pages and LEDs.

**Existing working installations:** Do not run the installer. Use `bash scripts/backup.sh` to make a private backup. A fresh-machine end-to-end installation is **not yet tested**.

## Known limitations

- Disk mapping is hard-coded in `DISKS` (slot 5/6 NVMe; 1/2 SATA in the tested setup); `/dev/sdX` can change across boots.
- Interface names are taken from the JSON template; change them for your system.
- The JSON template contains neutral placeholder temperatures/health flags until readings arrive. SMART handling depends on `smartctl` output; not every drive type is covered.
- ACPI `acpitz` was 27.8 °C on the tested machine, but it is **not proven to be chassis temperature**.
- The display executable is proprietary and is a required external dependency; its source is not included.
- The original LCD's firmware version display is not populated by our JSON template.

## Repository structure

- `src/debian-monitor.py` — actual tested Python collector, unchanged from the exported running setup
- `config/state-template.json` — privacy-cleaned example based on tested schema
- `systemd/` — tested unit files and quiet journal override
- `scripts/extract-vendor.sh` — extract `serialtest` from official S1 ZIP → ISO (unverified against actual ZIP)
- `scripts/install.sh` — conservative file installation with backups
- `scripts/uninstall.sh` — stop/disable/remove services, preserve working data
- `scripts/backup.sh` — local recovery archive (do not publish archives)
- `docs/README.de.md` — German instructions

## Privacy and safety

The example JSON uses `UNKNOWN` and contains no real device serial number. On each installed LincStation, the monitor automatically reads that machine’s own BIOS serial number from `/sys/class/dmi/id/product_serial` and displays it locally via the runtime JSON. **Never commit `/run/lincstation/state.json`**, personal backups, private logs or vendor binaries without permission: runtime JSON contains the real serial number.

## Licensing and redistribution

This repository contains community-written code only. **Do not upload the original vendor executables `serialtest` or `monitor` to a public repository unless the rights holder grants redistribution rights or a suitable license explicitly permits it.** Access to a vendor download does not itself grant redistribution rights. The original `monitor` is not needed for this solution. A license for our own source must be chosen before a public release; no license is currently granted by this draft.

## Installation safety and validation

- `scripts/install.sh` stages files and does not restart existing services. Run the installer as root from a checked-out repository.
- `scripts/configure.py` proposes network interfaces and disk names, but requires explicit confirmation; disk numbering is **not** a reliable physical bay identifier.
- `hardware-map.json` is local and ignored by Git. `/dev/sdX` names may change across boots. Stable device paths are a future improvement; do not change them without testing the sensor matching logic.
- Syntax and shell checks have been performed; a fresh-machine end-to-end installation has **not** yet been tested.

## Related projects

- [LincStation N1 LED Control](https://github.com/AndiBcool/lincstation-n1-led-control) — separate project for the LincStation N1. **Do not use the N1 installation instructions or binaries for the S1.**
