import os
import sys
import logging
import subprocess

from pathlib import Path

base_path = '../..'
current_path = Path(__file__).parent.resolve()

os.chdir(current_path)

logging.basicConfig(
  level = logging.INFO,
  format = "[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt = "%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger()

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

output = result.stdout.strip() + result.stderr.strip()
log.info(f'Command output: {output}')

str_to_find = 'telebot is running'

if str_to_find in output.lower():
  log.info(f"String '{str_to_find}' found. Test is ok")
  sys.exit(0)
else:
  log.info(f"String '{str_to_find}' not found. Test failed")
  sys.exit(1)
