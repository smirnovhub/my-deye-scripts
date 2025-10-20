import os
import sys
import logging

from pathlib import Path
from typing import Any, Dict

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
from deye_base_enum import DeyeBaseEnum
from solarman_server import SolarmanServer
from deye_registers_holder import DeyeRegistersHolder
from deye_test_helper import DeyeTestHelper

DeyeUtils.turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = DeyeUtils.time_format_str,
)

log = logging.getLogger()
loggers = DeyeLoggers()

if not loggers.is_test_loggers:
  log.info('ERROR: your loggers are not test loggers')
  sys.exit(1)

logger = loggers.master

server = SolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

holder_kwargs = {
  'name': 'test',
  'socket_timeout': 1,
  'caching_time': 0,
  'verbose': True,
}

# should be local to avoid issues with locks
holder = DeyeRegistersHolder(
  loggers = [logger],
  **holder_kwargs,
)

write_values: Dict[str, Any] = {}

for register in holder.master_registers.all_registers:
  if not register.can_write:
    continue

  value = DeyeTestHelper.get_random_by_register_value_type(register)
  if value is None:
    log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
    continue

  register_value = f'{register.name} = {value}'

  log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
  log.info(f'Trying to write: {register_value}')

  if isinstance(register.value, DeyeBaseEnum):
    write_values[register.name] = holder.write_register(register, register.value.parse(value))
  else:
    write_values[register.name] = holder.write_register(register, value)

log.info(f'Reading of all registers...')
holder.read_registers()

for register in holder.master_registers.all_registers:
  if not register.can_write:
    continue

  if register.value != write_values[register.name]:
    log.info(f"Register value after read {register.value} doesn't match "
             f"value after write {write_values[register.name]} for '{register.name}'")
    sys.exit(1)
  else:
    log.info(f"Register values successfully matched for '{register.name}'")

log.info('All registers have been written and read correctly. Test is ok')
