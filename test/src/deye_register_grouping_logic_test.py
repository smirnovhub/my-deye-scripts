import os
import sys
import asyncio
import logging

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
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_test_utils import DeyeTestUtils
from deye_registers import DeyeRegisters
from solarman_test_server import SolarmanTestServer
from deye_registers_holder_async import DeyeRegistersHolderAsync
from deye_custom_single_registers import DeyeCustomSingleRegisters

async def main_test_logic(
  servers: List[SolarmanTestServer],
  loggers: List[DeyeLogger],
  log: logging.Logger,
):
  for server in servers:
    server.set_sequential_mode(True)

  holder_kwargs = {
    'name': 'test',
    'socket_timeout': 1,
    'caching_time': 0,
    'verbose': False,
  }

  registers = DeyeRegisters()
  register = registers.test1_register

  # should be local to avoid issues with locks
  holder = DeyeRegistersHolderAsync(
    loggers = loggers,
    register_creator = lambda prefix: DeyeCustomSingleRegisters(register, prefix),
    **holder_kwargs,
  )

  try:
    await holder.read_registers()
  finally:
    holder.disconnect()

  # Iterate through the values to find the exact point of failure
  for i, val in enumerate(register.value):
    expected = register.address + i
    if val != expected:
      # Log the specific mismatch detail
      log.error(f"Register values mismatch at address: {register.address + i}: "
                f"expected {expected}, but got {val}")

      log.error(f"All register values: {register.value}")
      sys.exit(1)

  log.info('All register values matched. Test is ok')

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

  master = [loggers.master]

  async with DeyeTestUtils.solarman_servers(master) as servers:
    for _ in range(100):
      await main_test_logic(
        servers = servers,
        loggers = master,
        log = log,
      )

if __name__ == "__main__":
  asyncio.run(main())
