#!/usr/bin/env python3
import json
import os
import time
import glob
import subprocess
import signal
import socket
import fcntl
import struct

SOURCE = "/root/lincstation-test/state-template.json"
TARGET = "/run/lincstation/state.json"

FAST_INTERVAL = 2
TEMPERATURE_INTERVAL = 30
SMART_INTERVAL = 300

# Tested fallback; configure.py writes hardware-map.json with detected candidates.
DISKS = {
    "5": "/dev/nvme0n1", "6": "/dev/nvme1n1",
    "1": "/dev/sda", "2": "/dev/sdb",
}
HARDWARE_MAP = "/root/lincstation-test/hardware-map.json"

def configured_disks():
    try:
        with open(HARDWARE_MAP) as f:
            mapping = json.load(f)["disks"]
        if set(mapping) != set(DISKS) or not all(
            isinstance(v, str) and v.startswith("/dev/") for v in mapping.values()
        ):
            raise ValueError("Invalid disk mapping")
        return mapping
    except FileNotFoundError:
        return DISKS.copy()


running = True


def stop(signum, frame):
    global running
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def cpu_counters():
    result = {}
    with open("/proc/stat") as f:
        for line in f:
            parts = line.split()
            if not parts or not parts[0].startswith("cpu"):
                continue
            values = list(map(int, parts[1:]))
            result[parts[0]] = (
                values[3] + values[4],
                sum(values[:8])
            )
    return result


def cpu_usage(before, after):
    def usage(name):
        if name not in before or name not in after:
            return 0.0
        idle = after[name][0] - before[name][0]
        total = after[name][1] - before[name][1]
        if total <= 0:
            return 0.0
        return round(max(0, min(100, 100 * (1 - idle / total))), 1)

    cores = sorted(
        (k for k in before if k.startswith("cpu") and k != "cpu"),
        key=lambda k: int(k[3:])
    )

    return {
        "total": usage("cpu"),
        "cores": [usage(k) for k in cores]
    }


def cpu_frequency():
    base = "/sys/devices/system/cpu/cpu0/cpufreq"

    result = {}

    for key, filename in (
        ("currentFrequency", "scaling_cur_freq"),
        ("maxFrequency", "cpuinfo_max_freq"),
    ):
        try:
            with open(base + "/" + filename) as f:
                khz = int(f.read().strip())
            result[key] = f"{round(khz / 1000)}MHz"
        except (OSError, ValueError):
            pass

    return result


def memory_usage():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            info[key] = int(value.strip().split()[0]) * 1024

    total = info["MemTotal"]
    available = info["MemAvailable"]

    return {
        "total": total,
        "used": total - available,
        "free": available
    }


def network_counters(interface):
    base = f"/sys/class/net/{interface}/statistics"
    try:
        with open(base + "/rx_bytes") as f:
            rx = int(f.read())
        with open(base + "/tx_bytes") as f:
            tx = int(f.read())
        return rx, tx
    except (OSError, ValueError):
        return None


def network_ip(interface):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", interface[:15].encode())
        result = fcntl.ioctl(sock.fileno(), 0x8915, request)
        return socket.inet_ntoa(result[20:24])
    except OSError:
        return "0.0.0.0"
    finally:
        sock.close()


def sensors():
    result = {}
    for hw in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            with open(hw + "/name") as f:
                name = f.read().strip()
            device = os.path.realpath(hw + "/device")
            with open(hw + "/temp1_input") as f:
                value = float(f.read()) / 1000
            result[(name, device)] = round(value, 1)
        except (OSError, ValueError):
            pass
    return result


def temperature_for(device, readings):
    device_path = os.path.realpath(
        "/sys/block/" + os.path.basename(device) + "/device"
    )

    for (name, path), temp in readings.items():
        if device.startswith("/dev/nvme") and name == "nvme":
            controller = os.path.basename(device).rsplit("n", 1)[0]
            if path.endswith("/" + controller):
                return temp

        if device.startswith("/dev/sd") and name == "drivetemp":
            if path == device_path:
                return temp

    return None


def smart_health(device):
    try:
        p = subprocess.run(
            ["smartctl", "-H", device],
            capture_output=True,
            text=True,
            timeout=15
        )
        for line in p.stdout.splitlines():
            if "overall-health" in line.lower():
                return "PASSED" in line.upper()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def write_json(data):
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    tmp = TARGET + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, TARGET)


def main():
    with open(SOURCE) as f:
        data = json.load(f)

    data.setdefault("processor", {})
    disks_map = configured_disks()

    last_temperature = float("-inf")
    last_smart = float("-inf")

    print("LincStation Debian-Monitor gestartet", flush=True)

    while running:
        start = time.monotonic()

        before_cpu = cpu_counters()

        interfaces = data.get("networkInterfaces", [])
        before_net = {
            net["interface"]: network_counters(net["interface"])
            for net in interfaces
        }

        # Gemeinsames Messfenster für CPU und Netzwerk
        time.sleep(1)

        after_cpu = cpu_counters()
        data["processor"]["usage"] = cpu_usage(
            before_cpu, after_cpu
        )

        # Geräte-Seriennummer lokal aus dem BIOS übernehmen
        try:
            with open("/sys/class/dmi/id/product_serial") as f:
                serial = f.read().strip()
            if serial and serial.lower() not in (
                "unknown", "none", "to be filled by o.e.m."
            ):
                data.setdefault("deviceInfo", {})["serialNumber"] = serial
        except OSError:
            pass

        # CPU-Modell direkt aus Debian lesen
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        data["processor"]["model"] = (
                            line.split(":", 1)[1].strip()
                        )
                        break
        except OSError:
            pass

        # Aktuelle und maximale CPU-Frequenz
        data["processor"].update(cpu_frequency())

        data["memory"] = memory_usage()

        elapsed = max(time.monotonic() - start, 0.001)

        for net in interfaces:
            name = net["interface"]
            old = before_net.get(name)
            new = network_counters(name)

            net["ip"] = [network_ip(name)]

            if old is not None and new is not None:
                net["throughput"] = {
                    "in": max(0, round((new[0] - old[0]) / elapsed)),
                    "out": max(0, round((new[1] - old[1]) / elapsed))
                }

        now = time.monotonic()

        if now - last_temperature >= TEMPERATURE_INTERVAL:
            readings = sensors()

            # ACPI-Systemtemperatur für die Geräteanzeige übernehmen
            for (name, sensor_path), temp in readings.items():
                if name == "acpitz":
                    data.setdefault("deviceInfo", {})["temperature"] = temp
                    break

            for (name, path), temp in readings.items():
                if name == "coretemp":
                    data["processor"]["temperature"] = temp
                    break

            for disk in data.get("disks", []):
                device = disks_map.get(str(disk.get("slot")))
                if not device:
                    continue

                temp = temperature_for(device, readings)
                if temp is not None:
                    disk["temperature"] = temp

            last_temperature = now

        if now - last_smart >= SMART_INTERVAL:
            for disk in data.get("disks", []):
                device = disks_map.get(str(disk.get("slot")))
                if not device:
                    continue

                health = smart_health(device)
                if health is not None:
                    disk["healthy"] = health

            last_smart = time.monotonic()

        write_json(data)

        print(
            "CPU:", data["processor"]["usage"]["total"],
            "% | RAM:",
            round(
                100 * data["memory"]["used"] /
                max(1, data["memory"]["total"]), 1
            ),
            "% | JSON aktualisiert",
            flush=True
        )

        remaining = FAST_INTERVAL - (time.monotonic() - start)
        if remaining > 0:
            time.sleep(remaining)

    print("LincStation Debian-Monitor beendet", flush=True)


if __name__ == "__main__":
    main()
