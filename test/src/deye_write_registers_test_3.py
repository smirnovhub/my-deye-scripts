import os
import sys
import logging
import subprocess

from typing import List
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

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from solarman_server import SolarmanServer
from deye_test_helper import DeyeTestHelper

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
  log.info('Your loggers are not test loggers')
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

for register in registers.all_registers:
  if not register.can_write:
    continue

  value = DeyeTestHelper.get_random_by_register_value_type(register)
  if value is None:
    log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
    continue

  for slave in loggers.slaves:
    register_value = f'{register.name} = {value}'

    log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
    log.info(f'Trying to write: {register_value}')

    write_command = [
      sys.executable,
      '-u',
      os.path.join(base_path, 'deye/deye'),
      '-v',
      f'-i',
      slave.name,
      f"--set-{register.name.replace('_', '-')}",
      f'{value}',
    ]

    command_str = ' '.join(write_command)
    command_str = command_str[command_str.find('deye'):].replace('deye/deye', 'deye')

    log.info(f'Command to execute: {command_str}')

    result = subprocess.run(
      write_command,
      capture_output = True,
      text = True,
    )

    output = result.stdout.strip() + result.stderr.strip()
    log.info(f'Write command output: {output}')

    resp_message = 'An exception occurred: You can write only to master inverter'

    if resp_message.lower() not in output.lower():
      log.info(f"Response message is incorrect. Should be: '{resp_message}'")
      sys.exit(1)

    for server in servers:
      if server.is_something_written():
        log.info(f"Changes on server '{server.name}' detected. We should not write to slaves")
        sys.exit(1)

log.info('No changes on server side tedected. Test is ok')
