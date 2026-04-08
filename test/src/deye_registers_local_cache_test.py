import os
import sys
import asyncio
import random
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
from deye_loggers import DeyeLoggers
from deye_test_utils import DeyeTestUtils

DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)

from deye_registers_cache_test_base import main_test_logic

async def main():
  DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)

  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  log = logging.getLogger()
  loggers = DeyeLoggers()

  if not loggers.is_test_loggers:
    log.error('ERROR: your loggers are not test loggers')
    sys.exit(1)

  logger = random.choice(loggers.loggers)

  async with DeyeTestUtils.solarman_server(logger) as server:
    await main_test_logic(
      server = server,
      logger = logger,
      log = log,
    )

if __name__ == "__main__":
  asyncio.run(main())
