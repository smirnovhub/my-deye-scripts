import os
import sys
import time
import random
import logging
import subprocess

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
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'common'),
  ],
)

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from solarman_server import SolarmanServer
from deye_test_helper import DeyeRegisterRandomValue
from deye_test_helper import DeyeTestHelper

DeyeUtils.turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = DeyeUtils.time_format_str,
)

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegisters()

if not loggers.is_test_loggers:
  log.info('Your loggers are not test loggers')
  sys.exit(1)

logger = random.choice(loggers.loggers)

server = SolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

def execute_command(cache_time: int) -> str:
  """
  Execute the Deye command-line utility with the given cache time.
  Retries up to 10 times if 'exception' or 'error' is found in the output.
  """
  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-v',
    f'-c {cache_time}',
    f'-i {logger.name}',
    '-a',
  ]

  command_str = ' '.join(commands)
  command_str = command_str[command_str.find('deye'):].replace('deye/deye', 'deye')
  log.info(f'Command to execute: {command_str}')

  for i in range(10):
    result = subprocess.run(commands, capture_output = True, text = True)
    output = (result.stdout + result.stderr).strip()
    log.info(f'Command output: {output}')

    if 'exception' not in output.lower() and 'error' not in output.lower():
      return output

    log.info('An exception occurred. Retrying...')
    time.sleep(1)

  log.info('Max retry count exceeded')
  sys.exit(1)

def read_and_check(
  *,
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
    time.sleep(delay_before)

  server.clear_registers_status()
  server.set_register_value(register.address, expected_value)

  output = execute_command(cache_time)

  if should_read_server:
    if not server.is_registers_readed(register.address, register.quantity):
      log.info(f"No request for read on the server side after reading '{register.name}'")
      sys.exit(1)
  else:
    if server.is_registers_readed(register.address, register.quantity):
      log.info(f"Value should be read from the cache '{register.name}'")
      sys.exit(1)

  if str(expected_value) not in output:
    log.info(f"Register value {expected_value} not found for '{register.name}'")
    sys.exit(1)

# ---- MAIN TEST LOGIC ----
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

register = registers.load_power_register

# 1. First read (no cache yet)
value1 = 12345
read_and_check(
  register = register,
  cache_time = 0,
  expected_value = value1,
  should_read_server = True,
)

# 2. Second read (from cache)
read_and_check(
  register = register,
  cache_time = 5,
  expected_value = value1,
  should_read_server = False,
  delay_before = 1,
)

# 3. Third read (still from cache)
read_and_check(
  register = register,
  cache_time = 5,
  expected_value = value1,
  should_read_server = False,
  delay_before = 1,
)

# 4. Cache expires → should read new value from server
log.info('Waiting for cache expiration...')

time.sleep(5)

value3 = 45678
read_and_check(
  register = register,
  cache_time = 3,
  expected_value = value3,
  should_read_server = True,
)

# 5. Next read (from cache again)
read_and_check(
  register = register,
  cache_time = 10,
  expected_value = value3,
  should_read_server = False,
  delay_before = 1,
)

log.info('Cache logic works properly. Test is ok')
