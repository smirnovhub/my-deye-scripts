import os
import sys
import time
import datetime
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
    os.path.join(base_path, 'common'),
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'telebot/src/test'),
  ],
)

from deye_utils import DeyeUtils
from telebot_test_utils import TelebotTestUtils

start_time = datetime.datetime.now()
scripts = TelebotTestUtils.find_tests()

for i, script in enumerate(scripts):
  print(f"\n--- RUNNING {i + 1}/{len(scripts)} {script} ---\n")
  time.sleep(3)
  result = subprocess.run([sys.executable, "-u", script])
  if result.returncode != 0:
    t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
    print(f"\nError: {script} exited with code {result.returncode}. Tests failed after {t}.")
    sys.exit(result.returncode)

t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
print('\nAll tests completed successfully.')
print(f"Total execution time: {t}")
