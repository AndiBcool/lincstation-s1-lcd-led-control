#!/usr/bin/env python3
"""Generate proposed mappings without changing the running services."""
import json
import os
import subprocess
from pathlib import Path

BASE = Path('/root/lincstation-test')
TEMPLATE = BASE / 'state-template.json'
MAP = BASE / 'hardware-map.json'

def devices():
    out = subprocess.check_output(['lsblk', '-J', '-d', '-o', 'NAME,TYPE,TRAN'], text=True)
    rows = json.loads(out)['blockdevices']
    nvme = sorted('/dev/' + x['name'] for x in rows if x['type'] == 'disk' and x['name'].startswith('nvme'))
    sata = sorted('/dev/' + x['name'] for x in rows if x['type'] == 'disk' and x.get('tran') == 'sata')
    return nvme, sata

nvme, sata = devices()
interfaces = sorted(x.name for x in Path('/sys/class/net').iterdir() if x.name != 'lo' and (x / 'device').exists())
print('Detected NVMe:', nvme)
print('Detected SATA:', sata)
print('Detected network interfaces:', interfaces)
if len(nvme) != 2 or len(sata) != 2:
    raise SystemExit('Expected exactly 2 NVMe and 2 SATA disks; no configuration changed. Map slots manually.')
print('Proposed slot mapping: 5 ->', nvme[0], ', 6 ->', nvme[1], ', 1 ->', sata[0], ', 2 ->', sata[1])
print('WARNING: Linux disk order does NOT guarantee physical bay order! Confirm against the installed hardware.')
if input('I verified the physical slot mapping. Type YES to apply: ').strip() != 'YES':
    raise SystemExit('No changes made.')
map_data = {'disks': {'5': nvme[0], '6': nvme[1], '1': sata[0], '2': sata[1]}}
if MAP.exists():
    raise SystemExit(f'{MAP} exists; refusing to overwrite it.')
if not TEMPLATE.exists():
    raise SystemExit(f'{TEMPLATE} missing.')
data = json.loads(TEMPLATE.read_text())
data.setdefault('deviceInfo', {})['serialNumber'] = 'UNKNOWN'
data['networkInterfaces'] = [
    {'interface': name, 'ip': ['0.0.0.0'], 'throughput': {'in': 0, 'out': 0}}
    for name in interfaces[:2]
]
MAP.write_text(json.dumps(map_data, indent=2) + '\n')
TEMPLATE.write_text(json.dumps(data, indent=2) + '\n')
print('Configuration written. Inspect before enabling services.')
