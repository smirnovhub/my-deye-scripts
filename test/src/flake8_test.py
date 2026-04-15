import os
import sys
import logging
import subprocess

from pathlib import Path
from codespell_test import CODE_CHECK_DIRS

base_path = '../..'
current_path = Path(__file__).parent.resolve()

os.chdir(current_path)

def main():
  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
  )

  log = logging.getLogger()

  def run_test(path: str):
    commands = [
      "flake8",
      os.path.join(base_path, path),
      "--count",
      "--select=E9,F63,F7,F82",
      "--show-source",
      "--statistics",
      "--jobs=1",
    ]

    log.info(f'Running flake8 for {path}...')
    log.info(f'Command to execute: {commands}')

    result = subprocess.run(
      commands,
      capture_output = True,
      text = True,
    )

    output = result.stdout.strip() + '\n' + result.stderr.strip()
    log.info(f'Command output: {output}')

    if result.returncode != 0:
      log.error(f'Command returned non-zero exit code: {result.returncode}. Test failed.')
      sys.exit(1)

  for dir in CODE_CHECK_DIRS:
    run_test(dir)

if __name__ == "__main__":
  main()
