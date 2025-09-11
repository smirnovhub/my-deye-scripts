#!/usr/bin/python

import os
import sys

from typing import List
from pathlib import Path

sys.path.append('modules')
import common_modules

settings_text = """{
  "python.pythonPath": ".venv/bin/python",
  "python.analysis.extraPaths": [
    MODULES,
    INCLUDES
  ],
  "python.analysis.useImportHeuristic": true,
  "python.languageServer": "Pylance",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": false,
  "python.formatting.provider": "yapf",
  "python.envFile": "${workspaceFolder}/.env"
}
"""

def get_dirs(path: str, base_dirs: List[str]):
  pathes = []
  for base in base_dirs:
    for subdir in Path(os.path.join(path, base)).glob('**/'):
      if subdir.is_dir() and not subdir.name.startswith('.') and subdir.name != '__pycache__':
        next_path = str(subdir).replace(f'{path}{os.sep}', '')
        pathes.append(f'"{next_path}"')
  return sorted(pathes)

def process(path: str, base_dirs: List[str]):
  pathes = get_dirs(path, base_dirs)
  text = settings_text.replace('INCLUDES', ',\n    '.join(pathes))

  modules_path = os.path.relpath(common_modules.modules_dir, Path.cwd() / path)

  modules_str = f'"{modules_path}",\n' +  '    "' + modules_path + '/' + (f'",\n    "{modules_path}/'.join(common_modules.modules)) + '"'
  text = text.replace('MODULES', modules_str)
  text = text.replace('\\', '/')

  with open(os.path.join(path, '.vscode/settings.json'), 'w', newline = '') as f:
    f.write(text)
    f.flush()

process('deye', ['src', '../common'])
process('telebot', ['src', '../common', '../deye/src'])
