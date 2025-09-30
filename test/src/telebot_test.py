import os
import sys
import subprocess

from pathlib import Path

base_path = '../..'
current_path = Path(__file__).parent.resolve()

os.chdir(current_path)

commands = [
  sys.executable,
  '-u',
  os.path.join(base_path, 'telebot/telebot'),
]

print(f'Command to execute: {commands}')

result = subprocess.run(
  commands,
  capture_output = True,
  text = True,
)

output = result.stdout.strip() + result.stderr.strip()
print(f'Command output: {output}')

str_to_find = 'telebot is running'

if str_to_find in output.lower():
  print(f"String '{str_to_find}' found. Test is ok")
  sys.exit(0)
else:
  print(f"String '{str_to_find}' not found. Test failed")
  sys.exit(1)
