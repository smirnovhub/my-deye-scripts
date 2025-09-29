import os
import sys
import logging
import subprocess

from pathlib import Path

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
  registers.pv1_power_register: 12345,
  registers.battery_soc_register: 777,
  registers.battery_capacity_register: 54321,
  registers.ct_ratio_register: 15,
}

server = AioSolarmanServer(
  address = loggers.master.address,
  serial = loggers.master.serial,
  port = loggers.master.port,
)

all_found = True

for register, value in test_registers.items():
  server.set_expected_register_address(register.address)
  server.set_expected_register_value(value)

  print(f"Getting '{register.name}' with expected value {value}...")

  commands = [
    sys.executable,
    "../../deye/deye",
    f"--get-{register.name.replace('_', '-')}",
  ]

  print(f'Command to execute: {commands}')

  result = subprocess.run(
    commands,
    capture_output = True,
    text = True,
  )

  output = result.stdout.strip()
  print(f'Command output: {output}')

  name = f'{loggers.master.name}_{register.name} = {value} {register.suffix}'.strip()
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
