import os
import sys
import logging
import shutil
import subprocess

from typing import List
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

  def remove_mypy_cache(dirs: List[str]):
    for path in dirs:
      # Convert to absolute path
      path = os.path.abspath(os.path.join(base_path, path))
      log.info(f"Resolved base path: {path}")

      if not os.path.exists(path):
        log.info(f"Path not found: {path}")
        return

      for root, dirs, _ in os.walk(path, topdown = False):
        if '.mypy_cache' in dirs:
          cache_dir = os.path.join(root, '.mypy_cache')
          try:
            shutil.rmtree(cache_dir)
            log.info(f"Deleted: {cache_dir}")
          except Exception as e:
            log.info(f"Error deleting {cache_dir}: {e}")

  def run_tests(dirs: List[str]):
    for path in dirs:
      log.info(f'Running mypy for {path}...')

      commands = [
        "mypy",
        "--ignore-missing-imports",
        "--check-untyped-defs",
        os.path.join(base_path, path),
      ]

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

  remove_mypy_cache(CODE_CHECK_DIRS)
  run_tests(CODE_CHECK_DIRS)
  remove_mypy_cache(CODE_CHECK_DIRS)

if __name__ == "__main__":
  main()
