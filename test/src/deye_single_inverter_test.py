import os
import sys
import time
import random
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
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer
from int_deye_register import IntDeyeRegister
from signed_int_deye_register import SignedIntDeyeRegister
from deye_base_enum import DeyeBaseEnum
from float_deye_register import FloatDeyeRegister
from signed_float_deye_register import SignedFloatDeyeRegister
from temperature_deye_register import TemperatureDeyeRegister
from long_float_deye_register import LongFloatDeyeRegister
from long_float_splitted_deye_register import LongFloatSplittedDeyeRegister

from deye_utils import (
  to_unsigned,
  custom_round,
  to_long_register_values,
)

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

for register in registers.all_registers:
  if register.can_write:
    continue

  if isinstance(register.value, DeyeBaseEnum):
    valid_values = [v for v in type(register.value) if v.value >= 0]
    value = random.choice(valid_values)
    server.set_register_value(register.address, value.value)
  elif isinstance(register, LongFloatSplittedDeyeRegister):
    # Compute the maximum safe value for 2 registers (32-bit unsigned)
    max_val = (2**32 - 1) // register.scale

    # Generate a random value within the allowed range
    val = int(random.uniform(0, max_val)) / register.scale

    # Get the two 16-bit registers representing the 32-bit value
    values = to_long_register_values(val, register.scale, register.quantity) # values[0], values[1]

    # Create a list of registers to write
    # The first register is at register.address
    # The second register is at register.address + split_offset
    # Any registers in between are "garbage" and set to 0
    total_registers = register.split_offset + 1 # index of the second register + 1
    regs_to_write = [0] * total_registers
    regs_to_write[0] = values[0] # first data register
    regs_to_write[register.split_offset] = values[1] # second data register at split_offset

    # Write all registers to the server
    server.clear_registers()
    server.set_register_values(register.address, regs_to_write)

    # Round the value for further use
    value = custom_round(val)
  elif isinstance(register, LongFloatDeyeRegister):
    max_val = (2**32 - 1) // register.scale
    val = int(random.uniform(0, max_val) * register.scale // register.scale) / register.scale
    values = to_long_register_values(val, register.scale, register.quantity)
    server.set_register_values(register.address, values)
    value = custom_round(val)
  elif isinstance(register, TemperatureDeyeRegister):
    val = int(random.uniform(0, (65000 + register.shift) / register.scale) * register.scale)
    server.set_register_value(register.address, val)
    value = custom_round((val + register.shift) / register.scale)
  elif isinstance(register, SignedFloatDeyeRegister):
    val = int(random.uniform(-32000 / register.scale, 32000 / register.scale) * register.scale)
    server.set_register_value(register.address, to_unsigned(val))
    value = custom_round(val / register.scale)
  elif isinstance(register, FloatDeyeRegister):
    val = int(random.uniform(0, 65000 / register.scale) * register.scale)
    server.set_register_value(register.address, val)
    value = custom_round(val / register.scale)
  elif isinstance(register, SignedIntDeyeRegister):
    value = random.randint(-32000, 32000)
    server.set_register_value(register.address, to_unsigned(value))
  elif isinstance(register, IntDeyeRegister):
    value = random.randint(0, 65000)
    server.set_register_value(register.address, value)
  else:
    log.info(f"skipping register '{register.name}' with type {type(register).__name__}")
    continue

  log.info(f"Getting '{register.name}' with expected value {value}...")

  commands = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-c 0',
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
      break

    log.info('An exception occurred. Retrying...')
    time.sleep(3)

  if not server.is_registers_readed(register.address, register.quantity):
    log.info(f"no request for read on the server side after reading '{register.name}'")
    sys.exit(1)

  name = f'{logger.name}_{register.name} = {value} {register.suffix}'.strip()
  log.info(f"Finding '{name}'...")
  if name not in output:
    log.info('Register or value not found. Test failed')
    sys.exit(1)
  else:
    log.info('Register and value found')

log.info('All registers and values found. Test is ok')
