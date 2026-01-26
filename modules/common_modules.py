import sys
from typing import List
from pathlib import Path

# Determine the absolute path to the directory containing this file
modules_dir = Path(__file__).parent

# List of common modules
modules = [
  'uModbus',
  'pysolarmanv5',
  'pyTelegramBotAPI',
  'suntime',
  'dateutil/src',
]

# Add specific module directories to sys.path so they can be imported
for module in modules:
  sys.path.append(f'{str(modules_dir)}/{module}')

def import_dirs(base_path: Path, base_dirs: List[str]):
  """
  Recursively add directories to sys.path relative to a given base path

  This function allows Python to import modules from specified directories and
  all their subdirectories, while skipping hidden folders and __pycache__ directories

  Args:
      base_path (Path): The base directory from which the relative paths in `base_dirs` are resolved
      base_dirs (List[str]): List of directory paths relative to `base_path` to be added to sys.path
  """
  for base in base_dirs:
    dir_path = (base_path / base).resolve()
    if not dir_path.exists():
      continue
    for subdir in dir_path.glob('**/'):
      if subdir.is_dir() and not subdir.name.startswith('.') and subdir.name != '__pycache__':
        sys.path.append(str(subdir))
