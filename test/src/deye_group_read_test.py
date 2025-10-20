import os
import sys
import time
import logging
import subprocess

from pathlib import Path
from typing import Any, Dict, List

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

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from solarman_server import SolarmanServer
from deye_test_helper import DeyeTestHelper
from deye_test_helper import DeyeRegisterRandomValue
from deye_register_average_type import DeyeRegisterAverageType

DeyeUtils.turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = DeyeUtils.time_format_str,
)

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegisters()

if not loggers.is_test_loggers:
  log.info('ERROR: your loggers are not test loggers')
  sys.exit(1)

servers: List[SolarmanServer] = []

for logger in loggers.loggers:
  server = SolarmanServer(
    name = logger.name,
    address = logger.address,
    serial = logger.serial,
    port = logger.port,
  )

  servers.append(server)

registers_to_skip = [
  registers.grid_state_register.name,
  registers.inverter_system_time_diff_register.name,
]

def generate_random_register_values(server: SolarmanServer) -> Dict[str, Any]:
  random_values: Dict[str, Any] = {}
  randoms: List[DeyeRegisterRandomValue] = []

  server.clear_registers_status()

  for register in registers.all_registers:
    if register.name in registers_to_skip:
      log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
      continue

    if register.avg_type == DeyeRegisterAverageType.only_master and server.name != loggers.master.name:
      log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
      continue

    log.info(f"Processing register '{register.name}' with type {type(register).__name__}")

    random_value = DeyeTestHelper.get_random_by_register_type(register, randoms)
    if random_value is None:
      log.info(f"Register '{register.name}' is skipped")
      continue

    randoms.append(random_value)
    random_values[register.name] = random_value.value

    suffix = f' {register.suffix}'.rstrip()

    log.info(f"Generated random value for register '{register.name}' is {random_value.value}{suffix}...")

    if random_value.register.address > 0:
      server.set_register_values(random_value.register.addresses, random_value.values)

  return random_values

def run_command(cmds: List[str]) -> str:
  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-v',
    '--connection-timeout',
    '1',
    '-c 0',
  ]

  commands.extend(cmds)

  command_str = ' '.join(commands)
  command_str = command_str[command_str.find('deye'):].replace('deye/deye', 'deye')

  log.info(f'Command to execute: {command_str}')

  for i in range(10):
    result = subprocess.run(
      commands,
      capture_output = True,
      text = True,
    )

    output = result.stdout.strip() + result.stderr.strip()
    log.info(f'Command output: {output}')

    if 'exception' not in output and 'error' not in output:
      return output

    log.info('An exception occurred. Retrying...')
    time.sleep(1)
  else:
    log.info('Retry count exceeded')
    sys.exit(1)

def check_results(server: SolarmanServer, output: str, random_values: Dict[str, Any]):
  for register in registers.all_registers:
    if register.name in registers_to_skip:
      log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
      continue

    if register.avg_type == DeyeRegisterAverageType.only_master and server.name != loggers.master.name:
      log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
      continue

    if not server.is_registers_readed(register.address, register.quantity):
      log.info(f"No request for read on the server side after reading '{register.name}'")
      sys.exit(1)

    suffix = f' {register.suffix}'.rstrip()
    random_value = random_values.get(register.name, 0)
    name = f'{server.name}_{register.name} = {random_value}{suffix}'.strip()

    log.info(f"Finding '{name}'...")

    if name not in output:
      log.info('Register or value not found. Test failed')
      sys.exit(1)
    else:
      log.info('Register and value found')

for server in servers:
  random_values = generate_random_register_values(server)
  output = run_command([f"--get-{r.name.replace('_', '-')}" for r in registers.all_registers] + [f'-i {server.name}'])
  check_results(server, output, random_values)

  random_values = generate_random_register_values(server)
  output = run_command(['-a', f'-i {server.name}'])
  check_results(server, output, random_values)

  log.info('All registers and values found. Test is ok')
