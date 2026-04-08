import io
import os
import sys
import asyncio
import logging

from typing import List
from pathlib import Path
from contextlib import redirect_stdout

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
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from solarman_test_server import SolarmanTestServer
from deye_test_helper import DeyeTestHelper

from deye import main as deye_main

async def main_test_logic(
  servers: List[SolarmanTestServer],
  log: logging.Logger,
):
  loggers = DeyeLoggers()
  registers = DeyeRegisters()

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

      fake_args = [
        '-v',
        f'-i',
        slave.name,
        f"--set-{register.name.replace('_', '-')}",
        f'{value}',
      ]

      log.info(f'Command to execute: {" ".join(fake_args)}')

      async with DeyeTestUtils.collect_output() as buffer:
        try:
          await deye_main(fake_args)
        except SystemExit:
          pass
        output = buffer.getvalue().strip()

      log.info(f'Write command output: {output}')

      resp_message = 'An exception occurred: You can write only to master inverter'

      if resp_message.lower() not in output.lower():
        log.error(f"Response message is incorrect. Should be: '{resp_message}'")
        sys.exit(1)

      for server in servers:
        if server.is_something_written():
          log.error(f"Changes on server '{server.name}' detected. We should not write to slaves")
          sys.exit(1)

  log.info('No changes on server side tedected. Test is ok')

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

  async with DeyeTestUtils.solarman_servers(loggers.loggers) as servers:
    await main_test_logic(
      servers = servers,
      log = log,
    )

if __name__ == "__main__":
  asyncio.run(main())
