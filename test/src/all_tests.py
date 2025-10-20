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

success_count = 0
failed_count = 0

for i, script in enumerate(scripts):
  br = '\n' if i > 0 else ''
  print(f"{br}--- RUNNING {i + 1}/{len(scripts)} {script} ---\n")

  time.sleep(3)

  test_start_time = datetime.datetime.now()

  result = subprocess.run([sys.executable, "-u", script])

  t = DeyeUtils.format_timedelta(datetime.datetime.now() - test_start_time, add_seconds = True)
  if result.returncode != 0:
    print(f"\nError: {script} exited with code {result.returncode}. Test failed after {t}")
    failed_count += 1
  else:
    print(f"\n{script}: test completed successfully after {t}")
    success_count += 1

t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)

if success_count == 0:
  print(f'\nAll tests failed after {t}')
elif success_count == len(scripts):
  print(f'\nAll tests completed successfully after {t}')
else:
  print(f'\n{failed_count} test(s) failed and {success_count} test(s) completed successfully after {t}')
