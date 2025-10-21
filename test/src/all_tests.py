import os
import sys
import time
import datetime
import subprocess

from typing import List
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

success: List[str] = []
failed: List[str] = []

for i, script in enumerate(scripts):
  br = '\n' if i > 0 else ''
  print(f"{br}--- RUNNING {i + 1}/{len(scripts)} {script} ---\n")

  time.sleep(3)

  test_start_time = datetime.datetime.now()

  result = subprocess.run([sys.executable, "-u", script])

  t = DeyeUtils.format_timedelta(datetime.datetime.now() - test_start_time, add_seconds = True)
  if result.returncode != 0:
    print(f"\nError: {script} exited with code {result.returncode}. Test failed after {t}")
    failed.append(script)
  else:
    print(f"\n{script}: test completed successfully after {t}")
    success.append(script)

t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)

if len(success) == 0:
  print(f'\nAll tests failed after {t}')
elif len(success) == len(scripts):
  print(f'\nAll tests completed successfully after {t}')
else:
  print(f'\n{len(failed)} test(s) failed and {len(success)} test(s) completed successfully after {t}\n')
  success_tests = '\n  '.join(success)
  failed_tests = '\n  '.join(failed)
  print(f"Success tests:\n  {success_tests}\n")
  print(f"Failed tests:\n  {failed_tests}")
