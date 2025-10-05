import os
import sys
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

from deye_loggers import DeyeLoggers
from deye_utils import turn_tests_on

turn_tests_on()

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

loggers = DeyeLoggers()
log = logging.getLogger()

if not loggers.is_test_loggers:
  log.info('Your loggers are not test loggers')
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

str_to_find = 'all tests passed'

if str_to_find in output.lower():
  log.info(f"String '{str_to_find}' found. Test is ok")
  sys.exit(0)
else:
  log.info(f"String '{str_to_find}' not found. Test failed")
  sys.exit(1)
