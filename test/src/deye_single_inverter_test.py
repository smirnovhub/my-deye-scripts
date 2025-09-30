import os
import sys
import time
import random
import logging
import subprocess

from pathlib import Path

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(
  current_path,
  [
    'src',
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'common'),
  ],
)

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

from deye_utils import custom_round
from deye_loggers import DeyeLoggers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

max_value = 60000

test_registers = {
  registers.pv1_power_register: random.randint(1000, max_value),
  registers.battery_max_charge_current_register: random.randint(1000, max_value),
  registers.battery_voltage_register: random.randint(1000, max_value),
  registers.grid_frequency_register: random.randint(1000, max_value),
}

logger = random.choice(loggers.loggers)

server = AioSolarmanServer(
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

all_found = True

for register, value in test_registers.items():
  server.set_expected_register_address(register.address)
  server.set_expected_register_value(value)

  time.sleep(1)

  value = custom_round(value / register.scale)

  log.info(f"Getting '{register.name}' with expected value {value}...")

  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    f'-i {logger.name}',
    f"--get-{register.name.replace('_', '-')}",
  ]

  log.info(f'Command to execute: {commands}')

  for i in range(10):
    result = subprocess.run(
      commands,
      capture_output = True,
      text = True,
    )

    output = result.stdout.strip() + result.stderr.strip()
    log.info(f'Command output: {output}')

    if 'exception' not in output and 'error' not in output:
      break

    log.info('An exception occurred. Retrying...')
    time.sleep(3)

  name = f'{logger.name}_{register.name} = {value} {register.suffix}'.strip()
  log.info(f"Finding '{name}'...")
  if name not in output:
    log.info('Register or value not found')
    all_found = False
  else:
    log.info('Register and value found')

if all_found:
  log.info('All registers and values found. Test is ok')
  sys.exit(0)
else:
  log.info('Some registers and/or values not found. Test failed')
  sys.exit(1)
