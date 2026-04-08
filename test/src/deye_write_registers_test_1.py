import os
import re
import sys
import asyncio
import logging

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
  server = await DeyeTestUtils.start_solarman_server(logger)

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

    write_fake_args = [
      f"--set-{register.name.replace('_', '-')}",
      f'{value}',
    ]

    log.info(f'Command to execute: {" ".join(write_fake_args)}')

    async with DeyeTestUtils.collect_output() as buffer:
      try:
        await deye_main(write_fake_args)
      except SystemExit:
        pass
      write_output = buffer.getvalue().strip()

    log.info(f'Write command output: {write_output}')

    if not server.is_registers_written(register.address, register.quantity):
      log.error(f"No changes on the server side after writing '{register.name}'")
      sys.exit(1)

    log.info(f'Trying to read: {register_value}')

    read_fake_args = [
      '-c 0',
      f"--get-{register.name.replace('_', '-')}",
    ]

    log.info(f'Command to execute: {" ".join(read_fake_args)}')

    async with DeyeTestUtils.collect_output() as buffer:
      try:
        await deye_main(read_fake_args)
      except SystemExit:
        pass
      read_output = buffer.getvalue().strip()

    log.info(f'Read command output: {read_output}')

    if not server.is_registers_readed(register.address, register.quantity):
      log.error(f"No request for read on the server side after reading '{register.name}'")
      sys.exit(1)

    reg_name = f'{logger.name}_{register.name}'
    pattern = rf"^{reg_name}\s+=\s+(.+?){register.suffix}"

    write_match = re.search(pattern, write_output, re.MULTILINE)
    if write_match:
      value = write_match.group(1).strip()
      log.info(f"Write passed for register '{register.name}' and value '{value}'")

      if f'{reg_name} = {value}' in read_output:
        log.info(f"Read passed for register '{reg_name}' and value '{value}'")
      else:
        log.error(f"Read failed for register '{reg_name}' and value '{value}'")
        sys.exit(1)
    else:
      log.error(f"Write failed for '{register.name}'")
      sys.exit(1)

  log.info('All registers have been written and read correctly. Test is ok')

if __name__ == "__main__":
  asyncio.run(main())
