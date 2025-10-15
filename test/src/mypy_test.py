import os
import logging
import shutil
import subprocess

from pathlib import Path
import sys

base_path = '../..'
current_path = Path(__file__).parent.resolve()

os.chdir(current_path)

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger()

def remove_mypy_cache(path: str):
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

def run_test(path: str):
  log.info(f'Running mypy for {path}...')

  remove_mypy_cache(path)

  commands = [
    "mypy",
    "--ignore-missing-imports",
    "--check-untyped-defs",
    "--python-version",
    "3.8",
    os.path.join(base_path, path),
  ]

  log.info(f'Command to execute: {commands}')

  result = subprocess.run(
    commands,
    capture_output = True,
    text = True,
  )

  remove_mypy_cache(path)

  output = result.stdout.strip() + '\n' + result.stderr.strip()
  log.info(f'Command output: {output}')

  if result.returncode != 0:
    log.info(f'Command returned non-zero exit code: {result.returncode}. Test failed.')
    sys.exit(1)

run_test('deye')
run_test('telebot')
run_test('test')
