import os
import sys
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
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'common'),
  ],
)

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from solarman_server import SolarmanServer
from deye_registers_holder import DeyeRegistersHolder

DeyeUtils.turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = DeyeUtils.time_format_str,
)

log = logging.getLogger()
loggers = DeyeLoggers()

if not loggers.is_test_loggers:
  log.info('ERROR: your loggers are not test loggers')
  sys.exit(1)

servers: List[SolarmanServer] = []

for logger in loggers.loggers:
  server = SolarmanServer(
    name = logger.name,
    address = logger.address,
    serial = logger.serial,
    port = logger.port,
  )

  server.set_random_mode(True)
  servers.append(server)

holder_kwargs = {
  'name': 'test',
  'socket_timeout': 1,
  'caching_time': 0,
  'verbose': True,
}

# should be local to avoid issues with locks
holder = DeyeRegistersHolder(
  loggers = loggers.loggers,
  **holder_kwargs,
)

try:
  holder.read_registers()
finally:
  holder.disconnect()

# Test types match for accumulated registers
for register in holder.master_registers.all_registers:
  register_type = type(register.value).__name__

  accumulated_register = holder.accumulated_registers.get_register_by_name(register.name)
  if accumulated_register is None:
    print(f"Unable to get accumulated register '{register.name}'")
    sys.exit(1)

  accumulated_register_type = type(accumulated_register.value).__name__

  if register_type != accumulated_register_type:
    print(f"Original ({register_type}) and accumulated ({accumulated_register_type}) register "
          f"value type doesn't match for register '{register.name}'")
    sys.exit(1)
  else:
    print(f"Register value type '{register_type}' matched for accumulated register '{register.name}'")

log.info('All accumulated registers types matched. Test is ok')
