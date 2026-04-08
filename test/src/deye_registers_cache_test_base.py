import sys
import random
import asyncio
import logging

from typing import List

from deye_test_utils import DeyeTestUtils
from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_logger import DeyeLogger
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from solarman_test_server import SolarmanTestServer
from deye_test_helper import DeyeRegisterRandomValue
from deye_test_helper import DeyeTestHelper

from deye import main as deye_main

base_path = '../..'

log = logging.getLogger()

async def execute_command(
  logger: DeyeLogger,
  cache_time: int,
) -> str:
  """
  Execute the Deye command-line utility with the given cache time.
  Retries up to 10 times if 'exception' or 'error' is found in the output.
  """
  fake_args = [
    '-v',
    f'-c {cache_time}',
    f'-i {logger.name}',
    '-a',
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

  return output

async def read_and_check(
  *,
  logger: DeyeLogger,
  server: SolarmanTestServer,
  register: DeyeRegister,
  cache_time: int,
  expected_value: int,
  should_read_server: bool,
  delay_before: float = 0.0,
):
  """
  Perform a read of the register with cache control and verify results.

  Args:
      register: The register being tested.
      cache_time: Cache duration (seconds) passed to the command.
      expected_value: Expected value to appear in command output.
      should_read_server: True if the server should have been queried; False if value should come from cache.
      delay_before: Optional delay before executing command (seconds).
  """
  if delay_before > 0:
    log.info(f'Waiting {delay_before} seconds before reading...')
    await asyncio.sleep(delay_before)

  server.clear_registers_status()
  server.set_register_value(register.address, expected_value)

  output = await execute_command(
    logger = logger,
    cache_time = cache_time,
  )

  if should_read_server:
    if not server.is_registers_readed(register.address, register.quantity):
      log.error(f"No request for read on the server side after reading '{register.name}'")
      sys.exit(1)
  else:
    if server.is_registers_readed(register.address, register.quantity):
      log.error(f"Value should be read from the cache '{register.name}'")
      sys.exit(1)

  if str(expected_value) not in output:
    log.error(f"Register value {expected_value} not found for '{register.name}'")
    sys.exit(1)

async def main_test_logic():
  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  loggers = DeyeLoggers()

  if not loggers.is_test_loggers:
    log.error('ERROR: your loggers are not test loggers')
    sys.exit(1)

  logger = random.choice(loggers.loggers)

  server = SolarmanTestServer(
    name = logger.name,
    address = logger.address,
    serial = logger.serial,
    port = logger.port,
  )

  # ---- MAIN TEST LOGIC ----
  randoms: List[DeyeRegisterRandomValue] = []

  registers = DeyeRegisters()

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

  register = registers.load_power_register

  # 1. First read (no cache yet)
  value1 = 12345
  await read_and_check(
    logger = logger,
    server = server,
    register = register,
    cache_time = 0,
    expected_value = value1,
    should_read_server = True,
  )

  # 2. Second read (from cache)
  await read_and_check(
    logger = logger,
    server = server,
    register = register,
    cache_time = 15,
    expected_value = value1,
    should_read_server = False,
    delay_before = 1,
  )

  # 3. Third read (still from cache)
  await read_and_check(
    logger = logger,
    server = server,
    register = register,
    cache_time = 15,
    expected_value = value1,
    should_read_server = False,
    delay_before = 1,
  )

  # 4. Cache expires → should read new value from server
  log.info('Waiting for cache expiration...')

  await asyncio.sleep(5)

  value3 = 45678
  await read_and_check(
    logger = logger,
    server = server,
    register = register,
    cache_time = 3,
    expected_value = value3,
    should_read_server = True,
  )

  # 5. Next read (from cache again)
  await read_and_check(
    logger = logger,
    server = server,
    register = register,
    cache_time = 25,
    expected_value = value3,
    should_read_server = False,
    delay_before = 1,
  )

  log.info('Cache logic works properly. Test is ok')
