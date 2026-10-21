# LincStation S1 – LCD Display & LED Control on Debian / OpenMediaVault

**🌐 Language / Sprache:** **English** | [Deutsch](docs/README.de.md)

**Unofficial community project — not affiliated with LincStation.**

This project restores the original LCD pages and status LEDs on a LincStation S1 running Debian 12 and OpenMediaVault. On our machine, after switching from the vendor operating system, the LCD repeatedly restarted and the drive LEDs remained off. Our Python monitor supplies system metrics to the original vendor executable `serialtest`.

> **Beta (`v0.5.0-beta`):** The LCD, disk LEDs and network LED work on our S1, including after reboot. The complete installation process using these scripts has not yet been tested on a second machine.

## Confirmed working setup

- LincStation S1 running Debian 12 and OpenMediaVault (one tested machine)
- Four original LCD pages, drive LEDs and network LED
- CPU usage and frequency, RAM, network/IP/throughput
- Disk temperatures, SMART health and other temperature readings
- Automatic local detection of each machine's own BIOS serial number
- Two systemd services configured to start on boot

Hardware revisions, interface names and physical disk mappings may differ on other systems.

## How it works

`src/debian-monitor.py` writes metrics to `/run/lincstation/state.json`. The compatibility symlink `/var/unraid-systemMonitor/state.json` lets the original `serialtest` read those metrics. On the tested machine, the display controller communicates over `/dev/ttyS0` at 9600 baud.

The original vendor `monitor` executable is **not required** because our Python monitor replaces it. No display firmware is flashed.

## Obtain the original vendor `serialtest`

The vendor executable is **not distributed** through this GitHub repository. Download the [official LincStation S1 recovery package (Google Drive)](https://drive.google.com/file/d/1cnAWnFPu-5ryIhjftFlg71YqRRDEZJa-/view?usp=sharing).

Package filename: `LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip`

**Vendor package layout:**

```text
LincStation S1 ... .zip
└── 7321-unRAIDServer-...
    └── UNRAID.iso
        └── config/
            ├── serial/
            │   ├── serialtest
            │   └── test.sh
            └── pkg/
                └── i2c-tools-4.1-x86_64-1_slonly.txz
```

On Debian, **do not install** the Unraid `.txz` package. Our installer uses Debian APT to install `i2c-tools` and loads the `i2c-dev` kernel module.

## Installation on a new S1

**Before starting:** Install Debian 12 / OpenMediaVault. Confirm `/dev/ttyS0` exists and is not in use by another service. Run these commands from the root directory of the downloaded GitHub repository.

**1. Install prerequisites:**

```bash
sudo apt update
sudo apt install python3 smartmontools util-linux kmod unzip p7zip-full
```

**2. Download the official S1 ZIP** and copy it to your Debian S1. You do not need to manually unpack the ISO.

**3. Extract `serialtest`:**

```bash
sudo bash scripts/extract-vendor.sh "/path/to/LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip"
```

The script searches for `serialtest` inside the ISO and places it at `/root/lincstation-test/serialtest`. It checks the executable and will not overwrite an existing copy. **Extraction has not yet been tested against the full vendor ZIP.** Alternatively, manually place a lawfully obtained `serialtest` at that path and make it executable with `chmod 755`.

**4. Install the project:**

```bash
sudo bash scripts/install.sh
```

If needed, the installer installs `i2c-tools` through Debian APT, loads `i2c-dev`, and configures the module to load at boot. It copies the project files and service units, but **does not start them yet**. It refuses to overwrite an installation while either LincStation service is active.

**5. Configure hardware mapping:**

```bash
sudo python3 scripts/configure.py
```

Review detected disks and network interfaces carefully. Physical bay mapping requires confirmation: `/dev/sda` is not guaranteed to be bay 1 on another machine. Review `/root/lincstation-test/hardware-map.json` and `/root/lincstation-test/state-template.json`.

**6. Enable services only after reviewing the configuration:**

```bash
sudo systemctl enable --now lincstation-monitor.service lincstation-display.service
```

**7. Verify operation:**

```bash
systemctl status lincstation-monitor.service lincstation-display.service
```

Also inspect `/run/lincstation/state.json`, the LCD pages, and the disk/network LEDs.

**Important:** Unraid instructions such as `installpkg`, editing `/boot/config/go`, or launching `test.sh` do not apply to Debian. Do not install the Unraid I²C `.txz` on Debian.

## Protect an existing installation

Do **not** rerun the installer on a working S1 without reviewing it first. `bash scripts/backup.sh` creates a local backup. Backups can contain private settings and vendor binaries and must not be uploaded publicly.

`bash scripts/uninstall.sh` can remove the installed services while preserving files under `/root/lincstation-test` as a safety copy. Review the script before uninstalling.

## Repository structure

```text
lincstation-s1-lcd-led-control/
├── README.md
├── NOTICE.md
├── RELEASE_CHECKLIST.md
├── .gitignore
├── docs/
│   └── README.de.md
├── src/
│   └── debian-monitor.py
├── config/
│   └── state-template.json
├── scripts/
│   ├── extract-vendor.sh
│   ├── install.sh
│   ├── configure.py
│   ├── backup.sh
│   └── uninstall.sh
└── systemd/
    ├── lincstation-monitor.service
    ├── lincstation-display.service
    └── quiet.conf
```

## Privacy

The published example JSON contains `UNKNOWN`, not a real serial number. The Python monitor reads each machine's **own** BIOS serial from `/sys/class/dmi/id/product_serial` at runtime. Never upload `/run/lincstation/state.json`, private logs, backups or vendor executables without redistribution permission.

## Known limitations

- Tested bay mapping: slots 5/6 NVMe and slots 1/2 SATA. Device names may differ across machines or boots.
- Disk and network mapping is not universal; SMART output varies by drive.
- The physical location of the `acpitz` temperature sensor is not confirmed.
- The LCD shows `FW 30.17`, but its interpretation as controller firmware has not been independently verified. `serialtest -v` reports `V22.22`.
- The vendor bundles I²C tooling; a direct dependency of `serialtest` on these tools has not been separately demonstrated.
- Full fresh installation, including ZIP/ISO extraction, has not been tested on another machine.

## Licensing and vendor rights

Do not redistribute the original `serialtest` or `monitor` executables in a public repository without appropriate permission. A public vendor download link does not itself grant redistribution rights. A license for the community-written code still needs to be selected.

## Related projects

[LincStation N1 LED Control](https://github.com/AndiBcool/lincstation-n1-led-control) — separate project for the LincStation N1. **N1 and S1 executables and installation instructions are not interchangeable.**
