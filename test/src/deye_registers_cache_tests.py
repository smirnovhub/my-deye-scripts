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

from deye_loggers import DeyeLoggers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer
from deye_test_helper import DeyeRegisterRandomValue
from deye_test_helper import get_random_by_register_type
from deye_utils import turn_tests_on

turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

if not loggers.is_test_loggers:
  log.info('Your loggers are not test loggers')
  sys.exit(1)

logger = random.choice(loggers.loggers)

server = AioSolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

def execute_command(cache_time: int) -> str:
  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    f'-c {cache_time}',
    f'-i {logger.name}',
    '-a',
  ]

  command_str = ' '.join(commands)
  command_str = command_str[command_str.find('deye'):].replace('deye/deye', 'deye')

  log.info(f'Command to execute: {command_str}')

  for i in range(10):
    result = subprocess.run(
      commands,
      capture_output = True,
      text = True,
    )

    output = result.stdout.strip() + result.stderr.strip()
    log.info(f'Command output: {output}')

    if 'exception' not in output and 'error' not in output:
      return output

    log.info('An exception occurred. Retrying...')
    time.sleep(1)

  log.info('Max retry count exceeded')
  sys.exit(1)

randoms: List[DeyeRegisterRandomValue] = []

for register in registers.all_registers:
  log.info(f"Processing register '{register.name}' with type {type(register).__name__}")

  random_value = get_random_by_register_type(register, randoms)
  if random_value is None:
    log.info(f"Register '{register.name}' is skipped")
    continue

  randoms.append(random_value)

  suffix = f' {register.suffix}'.rstrip()

  log.info(f"Generated random value for register '{register.name}' is {random_value.value}{suffix}...")

  server.clear_registers_status()
  if random_value.register.address > 0:
    server.set_register_values(random_value.register.address, random_value.values)

register = registers.load_power_register

value1 = 12345
server.set_register_value(register.address, 12345)

log.info(f"Getting '{register.name}'...")

# first read with -c 0 doesn't use cached values, but will cache new values
output1 = execute_command(cache_time = 0)

if not server.is_registers_readed(register.address, register.quantity):
  log.info(f"No request for read on the server side after reading '{register.name}'")
  sys.exit(1)

if str(value1) not in output1:
  log.info(f"Register value {value1} not found for '{register.name}'")
  sys.exit(1)

log.info('Waiting for second read from cache...')
time.sleep(3)

# second read from cache

server.clear_registers_status()
server.set_register_value(register.address, 777)

output2 = execute_command(cache_time = 10)

if server.is_registers_readed(register.address, register.quantity):
  log.info(f"Value should be read from the cache '{register.name}'")
  sys.exit(1)

if str(value1) not in output2:
  log.info(f"Register value {value1} not found for '{register.name}'")
  sys.exit(1)

# waint for cache expiration and read again
log.info('Waiting for cache expiration...')
time.sleep(15)

# third read from server
value3 = 45678

server.clear_registers_status()
server.set_register_value(register.address, value3)
output3 = execute_command(cache_time = 10)

if not server.is_registers_readed(register.address, register.quantity):
  log.info(f"No request for read on the server side after reading '{register.name}'")
  sys.exit(1)

if str(value3) not in output3:
  log.info(f"Register value {value3} not found for '{register.name}'")
  sys.exit(1)

log.info('Cache logic works properly. Test is ok')
