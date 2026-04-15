import os
import sys
import logging
import subprocess

from pathlib import Path

base_path = '../..'
current_path = Path(__file__).parent.resolve()

os.chdir(current_path)

CODE_CHECK_DIRS = [
  'common',
  'data_collector',
  'demoserver',
  'deye',
  'deyestorage',
  'deye_graph_server',
  'deyeproxy',
  'deyeweb',
  'telebot',
  'test',
]

def main():
  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
  )

  log = logging.getLogger()

  def run_test(path: str):
    commands = [
      "codespell",
      os.path.join(base_path, path),
      '--skip=*.svg,*.log',
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

  for dir in CODE_CHECK_DIRS:
    run_test(dir)

if __name__ == "__main__":
  main()
