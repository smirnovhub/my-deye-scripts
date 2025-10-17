import os
import re
import sys
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

logger = loggers.master

server = SolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

for register in registers.all_registers:
  if not register.can_write:
    continue

  value = DeyeTestHelper.get_random_by_register_value_type(register)
  if value is None:
    log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
    continue

  server.clear_registers()

  register_value = f'{register.name} = {value}'

  log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
  log.info(f'Trying to write: {register_value}')

  write_command = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-v',
    f"--set-{register.name.replace('_', '-')}",
    f'{value}',
  ]

  command_str = ' '.join(write_command)
  command_str = command_str[command_str.find('deye'):].replace('deye/deye', 'deye')

  log.info(f'Command to execute: {command_str}')

  write_result = subprocess.run(
    write_command,
    capture_output = True,
    text = True,
  )

  write_output = write_result.stdout.strip() + write_result.stderr.strip()
  log.info(f'Write command output: {write_output}')

  if not server.is_registers_written(register.address, register.quantity):
    log.info(f"No changes on the server side after writing '{register.name}'")
    sys.exit(1)

  log.info(f'Trying to read: {register_value}')

  read_command = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-v',
    '-c 0',
    f"--get-{register.name.replace('_', '-')}",
  ]

  command_str = ' '.join(read_command)
  command_str = command_str[command_str.find('deye'):].replace('deye/deye', 'deye')

  log.info(f'Command to execute: {command_str}')

  read_result = subprocess.run(
    read_command,
    capture_output = True,
    text = True,
  )

  read_output = read_result.stdout.strip() + read_result.stderr.strip()
  log.info(f'Read command output: {read_output}')

  if not server.is_registers_readed(register.address, register.quantity):
    log.info(f"No request for read on the server side after reading '{register.name}'")
    sys.exit(1)

  reg_name = f'{logger.name}_{register.name}'
  pattern = rf"^{reg_name}\s+=\s+(.+)$"

  write_match = re.search(pattern, write_output, re.MULTILINE)
  if write_match:
    value = write_match.group(1).strip()
    log.info(f"Write passed for register '{register.name}' and value '{value}'")

    if f'{reg_name} = {value}' in read_output:
      log.info(f"Read passed for register '{register.name}' and value '{value}'")
    else:
      log.info(f"Read failed for register '{register.name}' and value '{value}'")
      sys.exit(1)
  else:
    log.info(f"Write failed for '{register.name}'")
    sys.exit(1)

log.info('All registers have been written and read correctly. Test is ok')
