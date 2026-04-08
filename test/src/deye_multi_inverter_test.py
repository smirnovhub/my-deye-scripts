import math
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
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_test_utils import DeyeTestUtils
from solarman_test_server import SolarmanTestServer
from deye_test_helper import DeyeTestHelper
from float_deye_register import FloatDeyeRegister
from deye_register_average_type import DeyeRegisterAverageType
from system_time_diff_deye_register import SystemTimeDiffDeyeRegister

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

  if not loggers.slaves:
    log.error("ERROR: you don't have slave loggers to run this test")
    sys.exit(1)

  servers = await DeyeTestUtils.start_solarman_servers(loggers.loggers)

  for register in registers.all_registers:
    log.info(f"Processing register '{register.name}' with type {type(register).__name__}")

    if register.avg_type not in (
        DeyeRegisterAverageType.average,
        DeyeRegisterAverageType.accumulate,
        DeyeRegisterAverageType.only_master,
    ):
      log.info(f"Register '{register.name}' is skipped")
      continue

    total_value = 0.0
    values: List[str] = []

    random_value = DeyeTestHelper.get_random_by_register_type(register)
    if random_value is None:
      continue

    divider = loggers.count if register.avg_type == DeyeRegisterAverageType.average else 1

    for server in servers:
      random_value = DeyeTestHelper.get_random_by_register_type(register)
      if random_value is None:
        continue

      server.set_register_values(random_value.register.addresses, random_value.values)

      digits = round(math.log10(register.scale)) if isinstance(register, FloatDeyeRegister) else 2

      if isinstance(register.value, int) or isinstance(register.value, float):
        total_value += round(float(random_value.value) / divider, digits)

      total_value = round(total_value, digits)

      values.append(random_value.value)

    if isinstance(register, SystemTimeDiffDeyeRegister):
      total_value = round(total_value)

    total_val = DeyeUtils.custom_round(total_value)

    inverters = ','.join(logger.name for logger in loggers.loggers)

    fake_args = [
      '-v',
      '--connection-timeout',
      '5',
      '-c',
      '0',
      f'-i',
      inverters,
      f"--get-{register.name.replace('_', '-')}",
    ]

    log.info(f'Command to execute: {" ".join(fake_args)}')

    async with DeyeTestUtils.collect_output() as buffer:
      try:
        await deye_main(fake_args)
      except SystemExit:
        pass
      output = buffer.getvalue().strip()

    log.info(f'Command output:\n{output}')

    if 'exception' in output or 'error' in output:
      log.info('An exception occurred.')
      sys.exit(1)

    for server in servers:
      if register.avg_type != DeyeRegisterAverageType.only_master or server.name == loggers.master.name:
        if not server.is_registers_readed(register.address, register.quantity):
          log.error(f"No request for read on the server '{server.name}' side after reading '{register.name}'")
          sys.exit(1)

    for i, logger in enumerate(loggers.loggers):
      if register.avg_type != DeyeRegisterAverageType.only_master or logger.name == loggers.master.name:
        val = values[i]
        log.info(f"Getting '{register.name}' with expected value {val}...")

        name = f'{logger.name}_{register.name} = {val} {register.suffix}'.strip()
        log.info(f"Finding '{name}'...")
        if name not in output:
          log.error('Register or value not found. Test failed')
          sys.exit(1)
        else:
          log.info('Register and value found')

    if register.avg_type != DeyeRegisterAverageType.only_master:
      all_name = f'{loggers.accumulated_registers_prefix}_{register.name} = {total_val} {register.suffix}'.strip()
      log.info(f"Finding '{all_name}'...")
      if all_name not in output:
        log.error('Register or value not found. Test failed')
        sys.exit(1)
      else:
        log.info('Register and value found')

  log.info('All registers and values found. Test is ok')

if __name__ == "__main__":
  asyncio.run(main())
