import os
import sys
import time
import logging
import subprocess

from pathlib import Path
from typing import List

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

from deye_loggers import DeyeLoggers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer
from int_deye_register import IntDeyeRegister
from float_deye_register import FloatDeyeRegister
from deye_register_average_type import DeyeRegisterAverageType
from deye_test_helper import get_random_by_register_type
from deye_utils import custom_round

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

if not loggers.is_test_loggers:
  log.info('Your loggers are not test loggers')
  sys.exit(1)

servers: List[AioSolarmanServer] = []

for logger in loggers.loggers:
  server = AioSolarmanServer(
    name = logger.name,
    address = logger.address,
    serial = logger.serial,
    port = logger.port,
  )

  servers.append(server)

for register in registers.all_registers:
  if register.avg_type not in (
      DeyeRegisterAverageType.average,
      DeyeRegisterAverageType.accumulate,
  ):
    continue

  if not isinstance(register, FloatDeyeRegister) and not isinstance(register, IntDeyeRegister):
    continue

  total_value = 0.0
  values: List[str] = []

  for server in servers:
    random_value = get_random_by_register_type(register)
    server.set_register_values(random_value.register.address, random_value.values)
    total_value += float(random_value.value)
    values.append(random_value.value)

  if register.avg_type == DeyeRegisterAverageType.average:
    total_value /= loggers.count

  total_val = custom_round(total_value)

  inverters = ','.join(logger.name for logger in loggers.loggers)

  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    f'-i {inverters}',
    f"--get-{register.name.replace('_', '-')}",
  ]

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
    log.info(f'Command output:\n{output}')

    if 'exception' not in output and 'error' not in output:
      break

    log.info('An exception occurred. Retrying...')
    time.sleep(3)

  for server in servers:
    if not server.is_registers_readed(register.address, register.quantity):
      log.info(f"No request for read on the server side after reading '{register.name}'")
      sys.exit(1)

  for i, logger in enumerate(loggers.loggers):
    val = values[i]
    log.info(f"Getting '{register.name}' with expected value {val}...")

    name = f'{logger.name}_{register.name} = {val} {register.suffix}'.strip()
    log.info(f"Finding '{name}'...")
    if name not in output:
      log.info('Register or value not found. Test failed')
      sys.exit(1)
    else:
      log.info('Register and value found')

  all_name = f'{loggers.accumulated_registers_prefix}_{register.name} = {total_val} {register.suffix}'.strip()
  log.info(f"Finding '{all_name}'...")
  if all_name not in output:
    log.info('Register or value not found. Test failed')
    sys.exit(1)
  else:
    log.info('Register and value found')

log.info('All registers and values found. Test is ok')
