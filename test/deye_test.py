import os
import sys
import time
import logging
import subprocess

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from solarman_server import AioSolarmanServer

server = AioSolarmanServer('127.0.0.1', 8899)

result = subprocess.run(
  [
    sys.executable,
    '../deye/deye',
    '--get-pv1-power',
  ],
  capture_output = True,
  text = True,
)

print(f'Output:\n{result.stdout}')

for line in result.stdout.splitlines():
  if 'pv1_power' in line:
    print('Line found. Test is ok')
    sys.exit(0)

print('Line not found. Test failed')
sys.exit(1)
