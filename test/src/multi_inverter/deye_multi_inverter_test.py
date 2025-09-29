import os
import sys
import time
import random
import logging
import subprocess

from pathlib import Path
from typing import List

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../../deye/src', '../../common'])

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

from deye_loggers import DeyeLoggers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer

loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

test_registers = {
  registers.pv1_power_register: random.randint(10, 9999),
  registers.load_power_register: random.randint(10, 9999),
}

servers: List[AioSolarmanServer] = []

for logger in loggers.loggers:
  server = AioSolarmanServer(
    address = logger.address,
    serial = logger.serial,
    port = logger.port,
  )

  print(f'logger.address = {logger.address}, logger.port = {logger.port}')

  servers.append(server)

all_found = True

for register, value in test_registers.items():
  for i, server in enumerate(servers):
    server.set_expected_register_address(register.address)
    server.set_expected_register_value(value * (i + 1))

  print(f"Getting '{register.name}' with expected value {value}...")

  inverters = ",".join(logger.name for logger in loggers.loggers)

  commands = [
    sys.executable,
    "../../deye/deye",
    f'-i {inverters}',
    f"--get-{register.name.replace('_', '-')}",
  ]

  print(f'Command to execute: {commands}')

  for i in range(10):
    result = subprocess.run(
      commands,
      capture_output = True,
      text = True,
    )

    output = result.stdout.strip() + result.stderr.strip()
    print(f'Command output: {output}')

    if 'exception' not in output and 'error' not in output:
      break

    print('An exception occurred. Retrying...')
    time.sleep(3)

  for i, logger in enumerate(loggers.loggers):
    name = f'{logger.name}_{register.name} = {value * (i + 1)} {register.suffix}'.strip()
    print(f"Finding '{name}'...")
    if name not in output:
      print('Register or value not found')
      all_found = False
    else:
      print('Register and value found')

if all_found:
  print('All registers and values found. Test is ok')
  sys.exit(0)
else:
  print('Some registers and/or values not found. Test failed')
  sys.exit(1)
