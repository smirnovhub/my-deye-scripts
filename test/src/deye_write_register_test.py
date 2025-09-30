import os
import sys
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

from datetime import datetime, timedelta
from deye_loggers import DeyeLoggers
from deye_base_enum import DeyeBaseEnum
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer

log = logging.getLogger()
loggers = DeyeLoggers()
registers = DeyeRegistersFactory.create_registers()

test_registers = [
  registers.ac_couple_frz_high_register,
  registers.backup_delay_register,
  registers.battery_gen_charge_current_register,
  registers.battery_grid_charge_current_register,
  registers.battery_low_batt_soc_register,
  registers.battery_max_charge_current_register,
  registers.battery_max_discharge_current_register,
  registers.battery_restart_soc_register,
  registers.battery_shutdown_soc_register,
  registers.ct_ratio_register,
  registers.grid_charging_start_soc_register,
  registers.grid_connect_voltage_low_register,
  registers.grid_connect_voltage_high_register,
  registers.grid_reconnect_voltage_low_register,
  registers.grid_reconnect_voltage_high_register,
  registers.grid_reconnection_time_register,
  registers.grid_peak_shaving_power_register,
  registers.gen_peak_shaving_power_register,
  registers.time_of_use_power_register,
  registers.time_of_use_soc_register,
  registers.zero_export_power_register,
  registers.inverter_system_time_register,
  registers.gen_port_mode_register,
  registers.system_work_mode_register,
]

logger = loggers.master

server = AioSolarmanServer(
  name = logger.name,
  address = logger.address,
  serial = logger.serial,
  port = logger.port,
)

all_found = True

for register in test_registers:
  value = ''
  if isinstance(register.value, int):
    value = round(random.uniform(register.min_value, register.max_value))
  elif isinstance(register.value, float):
    value = random.uniform(register.min_value, register.max_value)
  elif isinstance(register.value, datetime):
    start = datetime(2000, 1, 1)
    end = datetime.now()
    random_date = start + timedelta(seconds = random.randint(0, int((end - start).total_seconds())))
    value = random_date.strftime("%Y-%m-%d %H:%M:%S")
  elif isinstance(register.value, DeyeBaseEnum):
    valid_values = [v for v in type(register.value) if v.value >= 0]
    value = random.choice(valid_values)

  write_command = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    f"--set-{register.name.replace('_', '-')}",
    f'{value}',
  ]

  write_result = subprocess.run(
    write_command,
    capture_output = True,
    text = True,
  )

  write_output = write_result.stdout.strip() + write_result.stderr.strip()
  log.info(f'write_output = {write_output}')

  read_command = [
    sys.executable,
    '-u',
    os.path.join(base_path, 'deye/deye'),
    '-c 0',
    f"--get-{register.name.replace('_', '-')}",
  ]

  read_result = subprocess.run(
    read_command,
    capture_output = True,
    text = True,
  )

  read_output = read_result.stdout.strip() + read_result.stderr.strip()
  log.info(f'read_output = {read_output}')

  if write_output == read_output:
    log.info(f'write/read passed')
  else:
    log.info(f"write/read failed for register '{register.name}'")
    sys.exit(1)

log.info('All registers have been written and read correctly. Test is ok')
