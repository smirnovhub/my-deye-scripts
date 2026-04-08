import os
import sys
import asyncio
import logging

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
    os.path.join(base_path, 'deye'),
    os.path.join(base_path, 'common'),
  ],
)

from deye_utils import DeyeUtils
from deye_test_utils import DeyeTestUtils
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from solarman_test_server import SolarmanTestServer
from deye_test_helper import DeyeRegisterRandomValue
from deye_test_helper import DeyeTestHelper

from deye import main as deye_main

async def main_test_logic(
  server: SolarmanTestServer,
  logger: DeyeLogger,
  log: logging.Logger,
):
  registers = DeyeRegisters()

  randoms: List[DeyeRegisterRandomValue] = []

  for register in registers.all_registers:
    log.info(f"Processing register '{register.name}' with type {type(register).__name__}")

    random_value = DeyeTestHelper.get_random_by_register_type(register, randoms)
    if random_value is None:
      log.info(f"Register '{register.name}' is skipped")
      continue

    randoms.append(random_value)

    suffix = f' {register.suffix}'.rstrip()

    log.info(f"Generated random value for register '{register.name}' is {random_value.value}{suffix}...")

    server.clear_registers_status()
    if random_value.register.address > 0:
      server.set_register_values(random_value.register.addresses, random_value.values)

    fake_args = [
      '-v',
      '--connection-timeout',
      '5',
      '-c',
      '0',
      f'-i',
      logger.name,
      f"--get-{register.name.replace('_', '-')}",
    ]

    log.info(f'Command to execute: {" ".join(fake_args)}')

    async with DeyeTestUtils.collect_output() as buffer:
      try:
        await deye_main(fake_args)
      except SystemExit:
        pass
      output = buffer.getvalue().strip()

    log.info(f'Command output: {output}')

    if 'exception' in output or 'error' in output:
      log.error('An exception occurred.')
      sys.exit(1)

    if not server.is_registers_readed(register.address, register.quantity):
      log.error(f"No request for read on the server side after reading '{register.name}'")
      sys.exit(1)

    name = f'{logger.name}_{register.name} = {random_value.value}{suffix}'.strip()
    log.info(f"Finding '{name}'...")
    if name not in output:
      log.error('Register or value not found. Test failed')
      sys.exit(1)
    else:
      log.info('Register and value found')

  log.info('All registers and values found. Test is ok')

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
