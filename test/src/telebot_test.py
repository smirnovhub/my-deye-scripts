import os
import sys
import subprocess

base_path = '../..'

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

output = result.stdout.lower().strip() + result.stderr.lower().strip()
print(f'Command output: {output}')

str_to_find = 'telebot is running'

if str_to_find in output:
  print(f"String '{str_to_find}' found. Test is ok")
  sys.exit(0)
else:
  print(f"String '{str_to_find}' not found. Test failed")
  sys.exit(1)
