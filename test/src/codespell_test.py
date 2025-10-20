import os
import logging
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

def run_test(path: str):
  commands = [
    "codespell",
    os.path.join(base_path, path),
  ]

  log.info(f'Running codespell for {path}...')
  log.info(f'Command to execute: {commands}')

  result = subprocess.run(
    commands,
    capture_output = True,
    text = True,
  )

  output = (result.stdout.strip() + '\n' + result.stderr.strip()).strip()
  log.info(f'Command output: {output}')

  if result.returncode != 0:
    log.info(f'Command returned non-zero exit code: {result.returncode}. Test failed.')
    sys.exit(1)

run_test('common')
run_test('deye')
run_test('telebot')
run_test('test')
