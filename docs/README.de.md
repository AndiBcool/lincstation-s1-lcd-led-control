# LincStation S1 – LCD-Display und LEDs unter Debian / OpenMediaVault

**🌐 Sprache / Language:** [English](../README.md) | **Deutsch**

**Inoffizielles Community-Projekt – keine Verbindung zum Hersteller LincStation.**

Dieses Projekt stellt auf einer LincStation S1 mit Debian 12 und OpenMediaVault die originalen LCD-Anzeigen und Status-LEDs wieder her. Nach dem Wechsel vom Herstellersystem startete das LCD auf unserem Gerät wiederholt neu und die Laufwerks-LEDs blieben aus. Ein eigener Python-Monitor liefert die Systemdaten an das originale Herstellerprogramm `serialtest`.

> **Beta-Version (`v0.5.0-beta`):** LCD, Laufwerks-LEDs und Netzwerk-LED funktionieren auf unserer S1, auch nach einem Neustart. Die vollständige Neuinstallation mit den bereitgestellten Skripten wurde auf einem zweiten Gerät noch nicht getestet.

## Erfolgreich getestet

- LincStation S1 mit Debian 12 und OpenMediaVault (ein Gerät)
- Vier originale LCD-Seiten, Laufwerks-LEDs und Netzwerk-LED
- CPU-Auslastung, CPU-Takt, RAM, Netzwerk/IP/Datenrate
- Laufwerkstemperaturen, SMART-Status und weitere Temperaturwerte
- Automatische Erkennung der eigenen BIOS-Seriennummer zur Laufzeit
- Zwei systemd-Dienste mit automatischem Start nach dem Neustart

Andere Hardwarestände, Schnittstellennamen und Laufwerkszuordnungen sind nicht automatisch identisch.

## Funktionsweise

`src/debian-monitor.py` schreibt aktuelle Messwerte nach `/run/lincstation/state.json`. Über den Kompatibilitätslink `/var/unraid-systemMonitor/state.json` kann das originale `serialtest` diese Daten lesen. Die Kommunikation mit dem LCD-Controller erfolgt auf dem getesteten Gerät über `/dev/ttyS0` (9600 Baud).

Die originale Herstellerdatei `monitor` wird **nicht benötigt**, da unser Python-Programm diese Aufgabe übernimmt. Es wird keine Display-Firmware geflasht.

## Originaldatei `serialtest` vom Hersteller beziehen

Die ausführbare Herstellerdatei wird **nicht** auf GitHub verteilt. Sie stammt aus dem offiziellen [LincStation-S1-Wiederherstellungspaket (Google Drive)](https://drive.google.com/file/d/1cnAWnFPu-5ryIhjftFlg71YqRRDEZJa-/view?usp=sharing).

Dateiname: `LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip`

Aufbau des Herstellerpakets:

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

Unter Debian wird **nicht** das Unraid-`.txz`-Paket verwendet. Stattdessen installiert unser Installer `i2c-tools` über APT und lädt das Kernelmodul `i2c-dev`.

## Installation auf einer neuen S1

**Vorbereitung:** Debian 12 / OpenMediaVault installieren. Sicherstellen, dass `/dev/ttyS0` vorhanden und nicht anderweitig belegt ist. Die folgenden Befehle werden im Hauptverzeichnis des heruntergeladenen GitHub-Repositories ausgeführt.

**1. Voraussetzungen installieren:**

```bash
sudo apt update
sudo apt install python3 smartmontools util-linux kmod unzip p7zip-full
```

**2. Originales S1-ZIP herunterladen** und auf die Debian-S1 kopieren. Die enthaltene ISO muss nicht manuell entpackt werden.

**3. `serialtest` extrahieren:**

```bash
sudo bash scripts/extract-vendor.sh "/pfad/zum/LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip"
```

Das Skript sucht `serialtest` innerhalb der ISO und legt es unter `/root/lincstation-test/serialtest` ab. Es prüft die Datei und überschreibt keine vorhandene ausführbare Datei. **Die Extraktion wurde noch nicht mit dem vollständigen Hersteller-ZIP getestet.** Alternativ kann eine rechtmäßig bezogene `serialtest`-Datei manuell an diesen Zielpfad kopiert und mit `chmod 755` ausführbar gemacht werden.

**4. Projekt installieren:**

```bash
sudo bash scripts/install.sh
```

Der Installer installiert bei Bedarf `i2c-tools` über Debian-APT, lädt `i2c-dev` und richtet das Laden des Moduls beim Systemstart ein. Er kopiert die Projektdateien und Dienste, startet sie aber **noch nicht**. Bei bereits aktiven LincStation-Diensten verweigert er die Installation zum Schutz der laufenden Einrichtung.

**5. Hardwarezuordnung konfigurieren:**

```bash
sudo python3 scripts/configure.py
```

Die erkannten Laufwerke und Netzwerkschnittstellen sorgfältig prüfen. Die physische Schachtzuordnung muss bestätigt werden; `/dev/sda` ist nicht auf jedem System zwangsläufig Schacht 1. Die lokale Zuordnung wird unter `/root/lincstation-test/hardware-map.json` gespeichert. Auch `/root/lincstation-test/state-template.json` prüfen.

**6. Dienste erst nach der Prüfung aktivieren:**

```bash
sudo systemctl enable --now lincstation-monitor.service lincstation-display.service
```

**7. Funktion kontrollieren:**

```bash
systemctl status lincstation-monitor.service lincstation-display.service
```

Zusätzlich `/run/lincstation/state.json`, die LCD-Seiten sowie Laufwerks- und Netzwerk-LEDs kontrollieren.

**Wichtig:** Die Unraid-Anweisungen `installpkg`, Änderungen an `/boot/config/go` und der Start über `test.sh` gelten nicht für Debian. Das originale Unraid-I²C-Paket nicht auf Debian installieren.

## Vorhandene Installation schützen

Auf einer bereits funktionierenden S1 den Installer **nicht einfach erneut ausführen**. Mit `bash scripts/backup.sh` lässt sich zuvor eine lokale Sicherung erstellen. Sicherungsarchive können private Konfigurationen und Herstellerdateien enthalten und dürfen nicht öffentlich hochgeladen werden.

Mit `bash scripts/uninstall.sh` können die installierten Dienste entfernt werden; die Dateien unter `/root/lincstation-test` bleiben als Sicherheitskopie erhalten. Vor einer Deinstallation das Skript prüfen.

## Projektdateien

- `src/debian-monitor.py` – Python-Monitor der getesteten Einrichtung
- `config/state-template.json` – anonymisierte JSON-Vorlage
- `systemd/` – systemd-Dienste und Protokollierungs-Konfiguration
- `scripts/extract-vendor.sh` – `serialtest` aus dem Hersteller-ZIP und der ISO extrahieren
- `scripts/install.sh` – Projektdateien installieren, I²C-Voraussetzungen einrichten
- `scripts/configure.py` – Laufwerke und Netzwerk zuordnen
- `scripts/backup.sh` – lokale Sicherung erstellen
- `scripts/uninstall.sh` – Dienste entfernen

## Datenschutz

Die veröffentlichte Beispiel-JSON enthält keine echte Seriennummer, sondern `UNKNOWN`. Der Python-Monitor liest auf jedem Gerät die **eigene** BIOS-Seriennummer aus `/sys/class/dmi/id/product_serial`. Daher darf die lokale Laufzeitdatei `/run/lincstation/state.json` nicht auf GitHub hochgeladen werden. Gleiches gilt für private Logs, Backups und nicht zur Weitergabe freigegebene Herstellerprogramme.

## Bekannte Einschränkungen

- Die getestete Schachtbelegung war: Slot 5/6 NVMe und Slot 1/2 SATA. Auf anderen Geräten und nach Neustarts können Gerätenamen abweichen.
- Die Laufwerks- und Netzwerkkonfiguration ist nicht universell; SMART-Ausgaben variieren je nach Laufwerk.
- `acpitz` liefert einen ACPI-Temperaturwert, dessen physischer Messort nicht bestätigt ist.
- Das LCD zeigt `FW 30.17`; die Bedeutung als Controller-Firmwarestand ist nicht unabhängig verifiziert. `serialtest -v` meldet `V22.22`.
- Der Hersteller liefert I²C-Werkzeuge mit. Ob `serialtest` selbst unmittelbar auf I²C angewiesen ist, wurde nicht gesondert nachgewiesen.
- Die komplette Erstinstallation einschließlich ZIP-/ISO-Extraktion wurde noch nicht auf einem weiteren Gerät getestet.

## Lizenz und Herstellerrechte

Das originale `serialtest` und das originale `monitor` dürfen nicht ohne entsprechende Erlaubnis im öffentlichen Repository verteilt werden. Ein offizieller Downloadlink allein erteilt keine Weiterverbreitungsrechte. 

## Lizenz

Dieses Projekt steht unter der GNU General Public License Version 3 (GPL-3.0). Einzelheiten stehen in der [LICENSE-Datei](../LICENSE).

Die originale LincStation-Firmware und herstellereigene Programme wie `serialtest` fallen nicht unter die GPL-Lizenz dieses Projekts und werden nicht im Repository mitgeliefert.

## Weitere Projekte

[LincStation N1 LED Control](https://github.com/AndiBcool/lincstation-n1-led-control) – separates Projekt für die LincStation N1. **Programme und Installationsanleitungen von N1 und S1 sind nicht austauschbar.**
