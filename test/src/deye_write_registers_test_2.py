import os
import sys
import asyncio
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
from deye_test_utils import DeyeTestUtils
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_base_enum import DeyeBaseEnum
from solarman_test_server import SolarmanTestServer
from deye_registers_holder_async import DeyeRegistersHolderAsync
from deye_test_helper import DeyeTestHelper

async def main_test_logic(
  server: SolarmanTestServer,
  logger: DeyeLogger,
  log: logging.Logger,
):
  holder_kwargs = {
    'name': 'test',
    'socket_timeout': 1,
    'caching_time': 0,
    'verbose': False,
  }

  # should be local to avoid issues with locks
  holder = DeyeRegistersHolderAsync(
    loggers = [logger],
    **holder_kwargs,
  )

  write_values: Dict[str, Any] = {}

  try:
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

      write_value = value

      if isinstance(register.value, DeyeBaseEnum):
        val = register.value.parse(value)
        await holder.write_register(register, val)
        write_values[register.name] = val.pretty
      else:
        await holder.write_register(register, write_value)
        write_values[register.name] = write_value

    log.info(f'Reading of all registers...')

    await holder.read_registers()
  finally:
    holder.disconnect()

  for register in holder.master_registers.all_registers:
    if not register.can_write:
      continue

    if register.pretty_value != write_values[register.name]:
      log.error(f"Register value after read {register.pretty_value} doesn't match "
                f"value after write {write_values[register.name]} for '{register.name}'")
      sys.exit(1)
    else:
      log.info(f"Register values successfully matched for '{register.name}'")

  log.info('All registers have been written and read correctly. Test is ok')

async def main():
  DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)

  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  log = logging.getLogger()
  loggers = DeyeLoggers()

  if not loggers.is_test_loggers:
    log.error('ERROR: your loggers are not test loggers')
    sys.exit(1)

  logger = loggers.master

  async with DeyeTestUtils.solarman_server(logger) as server:
    await main_test_logic(
      server = server,
      logger = logger,
      log = log,
    )

if __name__ == "__main__":
  asyncio.run(main())
