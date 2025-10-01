import os
import sys
import time
import logging
import subprocess

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

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

if not loggers.is_test_loggers:
  log.info('Your loggers are not test loggers')
  sys.exit(1)

logger = loggers.master

server = AioSolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

def execute_command(register: DeyeRegister, cache_time: int) -> str:
  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    f'-c {cache_time}',
    f'-i {logger.name}',
    f"--get-{register.name.replace('_', '-')}",
  ]

  log.info(f'Command to execute: {commands}')

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
    time.sleep(3)

  log.info('Max retry count exceeded')
  sys.exit(1)

register = registers.load_power_register

value1 = 12345

server.clear_registers()
server.set_register_value(register.address, 12345)

log.info(f"Getting '{register.name}'...")

# first read with -c 0 doesn't use cached values, but will cache new values
output1 = execute_command(register, cache_time = 0)

if not server.is_registers_readed(register.address, register.quantity):
  log.info(f"No request for read on the server side after reading '{register.name}'")
  sys.exit(1)

if str(value1) not in output1:
  log.info(f"Register value {value1} not found for '{register.name}'")
  sys.exit(1)

# second read from cache
server.clear_registers()
server.set_register_value(register.address, 777)

output2 = execute_command(register, cache_time = 10)

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
server.clear_registers()
server.set_register_value(register.address, value3)
output3 = execute_command(register, cache_time = 10)

if not server.is_registers_readed(register.address, register.quantity):
  log.info(f"No request for read on the server side after reading '{register.name}'")
  sys.exit(1)

if str(value3) not in output3:
  log.info(f"Register value {value3} not found for '{register.name}'")
  sys.exit(1)

log.info('Cache logic works properly. Test is ok')
