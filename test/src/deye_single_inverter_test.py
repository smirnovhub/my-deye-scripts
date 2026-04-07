import io
import os
import sys
import time
import asyncio
import logging

from pathlib import Path
from typing import List
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
from deye_test_helper import DeyeRegisterRandomValue
from deye_test_helper import DeyeTestHelper

from deye import main as deye_main

async def main():
  DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)

  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  log = logging.getLogger()
  loggers = DeyeLoggers()
  registers = DeyeRegisters()

  if not loggers.is_test_loggers:
    log.error('ERROR: your loggers are not test loggers')
    sys.exit(1)

  logger = loggers.master

  server = SolarmanTestServer(
    name = logger.name,
    address = logger.address,
    serial = logger.serial,
    port = logger.port,
  )

  if not await DeyeTestUtils.wait_for_solarman_servers_ready([logger]):
    return

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
      "deye",
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

    for i in range(5):
      old_argv = sys.argv
      sys.argv = fake_args

      output_buffer = io.StringIO()

      try:
        # Redirect all print() calls to the buffer
        with redirect_stdout(output_buffer):
          try:
            await deye_main()
          except SystemExit:
            pass
      except Exception as e:
        log.error(f'An exception occurred: {e}. Retrying...')
        await asyncio.sleep(1)
        continue
      finally:
        # Restore original argv
        sys.argv = old_argv

      output = output_buffer.getvalue().strip()

      log.info(f'Command output: {output}')

      if 'exception' not in output and 'error' not in output:
        break

      log.error('An exception occurred. Retrying...')
      await asyncio.sleep(1)

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

if __name__ == "__main__":
  asyncio.run(main())
