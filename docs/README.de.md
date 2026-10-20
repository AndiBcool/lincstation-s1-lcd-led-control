# LincStation S1 – LCD und LEDs unter Debian / OpenMediaVault

**🌐 Sprache / Language:** [English](../README.md) | Deutsch
**Inoffizielles Community-Projekt, keine Verbindung zum Hersteller.**

## Hintergrund

Auf unserer LincStation S1 blieben nach dem Wechsel auf Debian 12 mit OpenMediaVault die Laufwerks-LEDs aus. Das originale LCD schaltete sich ein, startete jedoch wiederholt neu und zeigte keine nutzbaren Systemdaten. Dieses Projekt kombiniert einen selbst entwickelten Python-Monitor mit einem **originalen Programm des Herstellers**, um die Funktionen wiederherzustellen.

## Erfolgreich getestet

Vier originale LCD-Seiten, Laufwerks-LEDs, Netzwerk-LED, CPU- und RAM-Daten, Netzwerkinformationen, Temperaturen, SMART-Status, Seriennummer aus dem BIOS und automatischer Start nach einem NAS-Neustart. Das gilt für **ein konkret getestetes Gerät**; andere Hardware- und Softwarestände sind nicht garantiert.

## Offizielles Herstellerpaket für die S1

Der Hersteller verlinkt das [LincStation-S1-Wiederherstellungspaket auf Google Drive](https://drive.google.com/file/d/1cnAWnFPu-5ryIhjftFlg71YqRRDEZJa-/view?usp=sharing): `LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip`.

Die Struktur lautet: `ZIP → 7321-unRAIDServer-... → UNRAID.iso → config/serial/serialtest` sowie `test.sh`. Das Paket wird **nicht** in diesem Repository verteilt. Die Extraktion wurde noch nicht mit dem vollständigen Hersteller-ZIP getestet.

## Installation auf einem neuen System

1. Debian 12 / OpenMediaVault installieren; benötigte Werkzeuge: `sudo apt install python3 smartmontools util-linux kmod unzip p7zip-full`.
2. Das offizielle S1-ZIP über den Herstellerlink herunterladen und auf das Debian-System kopieren.
3. Im Repository als root ausführen: `sudo bash scripts/extract-vendor.sh "/pfad/zum/LincStation S1-unRAIDServer-0.99.16-6.12.15-20250520-171132.zip"`. Das Skript liest die ISO aus dem ZIP und kopiert ausschließlich `serialtest` nach `/root/lincstation-test/serialtest`. Bereits vorhandene Dateien werden nicht überschrieben.
4. `sudo bash scripts/install.sh` ausführen. Der Installer startet noch keine Dienste.
5. `sudo python3 scripts/configure.py` ausführen, die physische Laufwerkszuordnung und Netzwerkschnittstellen sorgfältig prüfen und bestätigen. Gerätebezeichnungen können sich ändern.
6. Erst nach erfolgreicher Prüfung: `sudo systemctl enable --now lincstation-monitor.service lincstation-display.service`.
7. `systemctl status lincstation-monitor.service lincstation-display.service` sowie LCD und LEDs kontrollieren.

**Wichtig:** Auf einer bereits funktionierenden S1 nicht einfach neu installieren. `scripts/backup.sh` erstellt vorher eine lokale Sicherung. Die Unraid-Anweisungen zu `go`, `installpkg` und `test.sh` gelten nicht für Debian. Der Installer installiert `i2c-tools` bei Bedarf automatisch über Debian-APT, lädt das Modul `i2c-dev` und richtet dessen Laden beim Systemstart ein. Das Unraid-`.txz`-Paket wird unter Debian nicht verwendet. Ob `serialtest` selbst direkt I²C benötigt, ist noch nicht nachgewiesen.

## Technischer Aufbau

Der Python-Monitor schreibt regelmäßig `/run/lincstation/state.json`. Das Originalprogramm `serialtest` steuert das Display über `/dev/ttyS0`. Die systemd-Dateien stammen aus unserer funktionierenden Installation. Der Monitor basiert auf der getesteten Installation und liest die Seriennummer zur Laufzeit aus dem BIOS; die JSON-Vorlage wurde anonymisiert.

## Einschränkungen

- `acpitz` liefert einen ACPI-Wert; dessen physischer Messort ist nicht bestätigt.
- Die LCD-Anzeige `FW 30.17` ist beobachtet, aber nicht unabhängig als Controller-Firmware verifiziert. `serialtest -v` meldet `V22.22`.
- Die Festplatten- und Netzwerkzuordnung ist derzeit statisch; vor dem Einsatz prüfen.
- Das Herstellerprogramm wird aus rechtlichen Gründen **nicht** mitgeliefert.
- Die Installation wurde **noch nicht als frische Neuinstallation** auf einem zweiten System getestet.

## Datensicherung und Deinstallation

`bash scripts/backup.sh` erzeugt ein lokales Archiv, das private Konfigurationen und ggf. die Originaldatei des Herstellers enthält – **nicht öffentlich hochladen**. `bash scripts/uninstall.sh` stoppt und entfernt die systemd-Dienste, belässt jedoch die Dateien unter `/root/lincstation-test` als Sicherheitskopie.

## Veröffentlichung

Vor einer öffentlichen Freigabe sollten Installationsablauf, Lizenzwahl und die Herkunft des Herstellerprogramms abschließend geprüft werden.

## Datenschutz und automatische Konfiguration

Die öffentliche Beispiel-JSON enthält **keine persönliche Seriennummer** (`UNKNOWN`). Der Monitor liest auf jeder installierten LincStation die **eigene BIOS-Seriennummer** automatisch aus `/sys/class/dmi/id/product_serial` aus und zeigt sie lokal an. Die Laufzeitdatei `/run/lincstation/state.json` enthält daher die echte Seriennummer und darf nicht auf GitHub veröffentlicht werden. Nach `bash scripts/install.sh` auf einer neuen Installation kann `python3 scripts/configure.py` die Laufwerks- und Netzwerkschnittstellen erkennen und eine Zuordnung **zur Bestätigung vorschlagen**. Die physische Reihenfolge der Laufwerksschächte muss manuell geprüft werden. Das Installationsskript legt den Kompatibilitäts-Symlink nur an, wenn noch keine Datei an dieser Stelle existiert. Dienste werden nicht automatisch neu gestartet.


## Hinweise zur V4-Installation

Die Reihenfolge ist **zuerst `bash scripts/install.sh`, danach `python3 scripts/configure.py`**, anschließend die Laufwerkszuordnung prüfen und erst dann beide Dienste starten. Der Installer verändert keine bereits laufende LincStation-Installation. Ein vollständiger Neuinstallationstest steht noch aus.

Die Herstellerdatei `serialtest` muss aus einer rechtmäßig nutzbaren Quelle bereitgestellt werden. Die originale `monitor`-Datei ist nicht erforderlich, weil unser Python-Monitor diese Funktion ersetzt. Ohne passende Weiterverbreitungserlaubnis dürfen die Herstellerdateien nicht ins öffentliche Repository aufgenommen werden.

Die Beispiel-JSON enthält keine echte Seriennummer; auf jedem Gerät liest der Python-Monitor die jeweilige BIOS-Seriennummer automatisch aus.

## Weitere Projekte

- [LincStation N1 LED Control](https://github.com/AndiBcool/lincstation-n1-led-control) — eigenständiges Projekt für die LincStation N1. **Die N1-Anleitungen und -Programme sind nicht für die S1 bestimmt.**
