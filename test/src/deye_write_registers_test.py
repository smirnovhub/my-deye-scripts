import os
import sys
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

from datetime import datetime, timedelta
from deye_loggers import DeyeLoggers
from deye_base_enum import DeyeBaseEnum
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

if not loggers.is_test_loggers:
  log.info('your loggers are not test loggers')
  sys.exit(1)

logger = loggers.master

server = AioSolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

all_found = True

for register in registers.all_registers:
  if not register.can_write:
    continue

  value = ''
  if isinstance(register.value, int):
    value = round(random.uniform(register.min_value, register.max_value))
  elif isinstance(register.value, float):
    value = round(random.uniform(register.min_value, register.max_value), 2)
  elif isinstance(register.value, datetime):
    start = datetime(2000, 1, 1)
    end = datetime.now()
    random_date = start + timedelta(seconds = random.randint(0, int((end - start).total_seconds())))
    value = random_date.strftime("%Y-%m-%d %H:%M:%S")
  elif isinstance(register.value, DeyeBaseEnum):
    valid_values = [v for v in type(register.value) if v.value >= 0]
    value = random.choice(valid_values)

  server.clear_registers()

  log.info(f'trying to write: {register.name} = {value}...')

  write_command = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    f"--set-{register.name.replace('_', '-')}",
    f'{value}',
  ]

  write_result = subprocess.run(
    write_command,
    capture_output = True,
    text = True,
  )

  write_output = write_result.stdout.strip() + write_result.stderr.strip()
  log.info(f'write_output = {write_output}')

  if not server.is_registers_written(register.address, register.quantity):
    log.info(f"no changes on the server side after writing '{register.name}'")
    sys.exit(1)

  read_command = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-c 0',
    f"--get-{register.name.replace('_', '-')}",
  ]

  read_result = subprocess.run(
    read_command,
    capture_output = True,
    text = True,
  )

  read_output = read_result.stdout.strip() + read_result.stderr.strip()
  log.info(f'read_output = {read_output}')

  if not server.is_registers_readed(register.address, register.quantity):
    log.info(f"no request for read on the server side after reading '{register.name}'")
    sys.exit(1)

  if write_output == read_output:
    log.info(f'write/read passed')
  else:
    log.info(f"write/read failed for register '{register.name}'")
    sys.exit(1)

log.info('All registers have been written and read correctly. Test is ok')
