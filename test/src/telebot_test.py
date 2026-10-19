import os
import sys
import time
import logging
import subprocess
import threading
import queue

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

from env_utils import EnvUtils
from deye_utils import DeyeUtils
from deye_test_utils import DeyeTestUtils
from deye_loggers import DeyeLoggers
from deye_test_helper import DeyeTestHelper

DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
  datefmt = DeyeUtils.time_format_str,
)

loggers = DeyeLoggers()
log = logging.getLogger()
start_time = time.time()

token = EnvUtils.get_telegram_bot_api_test_token()
if not token:
  log.error('Telegram bot api test token not found in your environment')
  sys.exit(1)

if not loggers.is_test_loggers:
  log.error('ERROR: your loggers are not test loggers')
  sys.exit(1)

commands = [
  sys.executable,
  '-u',
  os.path.join(base_path, 'telebot_async_new/deyetelebot.py'),
]

log.info(f'Command to execute: {commands}')
log.info('Command output:')

# Timeout for test execution in seconds (e.g., 300 seconds / 5 minutes)
TEST_TIMEOUT_SEC = 180

process = subprocess.Popen(
  commands,
  stdout = subprocess.PIPE,
  stderr = subprocess.STDOUT,
  text = True,
  bufsize = 1,
)

output_lines = []
output_queue = queue.Queue()

# Read process output in a background thread to prevent blocking
def read_output(pipe, q):
  try:
    for line in iter(pipe.readline, ''):
      q.put(line)
  finally:
    pipe.close()

reader_thread = threading.Thread(target = read_output, args = (process.stdout, output_queue))
reader_thread.daemon = True
reader_thread.start()

exec_start_time = time.time()

# Stream output in real-time and check for timeout
while True:
  if process.poll() is not None and output_queue.empty():
    break

  if time.time() - exec_start_time > TEST_TIMEOUT_SEC:
    process.kill()
    reader_thread.join()
    log.error(f'Test execution timed out after {TEST_TIMEOUT_SEC} seconds')
    sys.exit(1)

  try:
    line = output_queue.get(timeout = 0.1)
    stripped_line = line.strip()
    if stripped_line:
      log.info(stripped_line)
      output_lines.append(line)
  except queue.Empty:
    continue

output = ''.join(output_lines)
str_to_find = DeyeTestHelper.test_success_str.lower()

if str_to_find in output.lower():
  log.info(f"String '{str_to_find}' found. Test is ok")
  log.info(f"Execution time: {round(time.time() - start_time, 3)} sec")
  sys.exit(0)
else:
  log.error(f"String '{str_to_find}' not found. Test failed")
  sys.exit(1)
