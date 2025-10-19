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

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_test_helper import DeyeTestHelper

DeyeUtils.turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = DeyeUtils.time_format_str,
)

loggers = DeyeLoggers()
log = logging.getLogger()
start_time = time.time()

token = os.getenv('BOT_API_TEST_TOKEN', '')
if not token:
  log.info('ERROR: BOT_API_TEST_TOKEN not found in your environment')
  sys.exit(1)

if not loggers.is_test_loggers:
  log.info('ERROR: your loggers are not test loggers')
  sys.exit(1)

commands = [
  sys.executable,
  '-u',
  os.path.join(base_path, 'telebot/telebot'),
]

log.info(f'Command to execute: {commands}')

result = subprocess.run(
  commands,
  capture_output = True,
  text = True,
)

output = result.stdout.strip() + '\n' + result.stderr.strip()
log.info(f'Command output: {output}')

str_to_find = DeyeTestHelper.test_success_str.lower()

if str_to_find in output.lower():
  log.info(f"String '{str_to_find}' found. Test is ok")
  log.info(f"Execution time: {round(time.time() - start_time, 3)} sec")
  sys.exit(0)
else:
  log.info(f"String '{str_to_find}' not found. Test failed")
  sys.exit(1)
