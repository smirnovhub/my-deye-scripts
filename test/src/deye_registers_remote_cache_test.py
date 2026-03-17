import os
import sys
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
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'deyestorage'),
    os.path.join(base_path, 'common'),
  ],
)

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_test_utils import DeyeTestUtils

from deye_registers_cache_test_base import main_test_logic

if __name__ == '__main__':
  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)
  DeyeTestUtils.turn_on_remote_cache()

  logger = logging.getLogger()

  if not DeyeLoggers().is_test_loggers:
    logger.info('ERROR: your loggers are not test loggers')
    sys.exit(1)

  server_process = DeyeTestUtils.run_storage_server()

  try:
    main_test_logic()
  finally:
    DeyeTestUtils.stop_storage_server(server_process)
