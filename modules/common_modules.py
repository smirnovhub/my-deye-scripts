import sys
from typing import List
from pathlib import Path

# Determine the absolute path to the directory containing this file
modules_dir = Path(__file__).parent

# List of common modules
modules = [
  'uModbus',
  'pysolarmanv5',
  'pyTelegramBotAPI'
]

# Add specific module directories to sys.path so they can be imported
for module in modules:
  sys.path.append(f'{str(modules_dir)}/{module}')

# Recursively add all subdirectories of the given base directories to sys.path,
# excluding hidden folders (names starting with '.') and '__pycache__' folders
# 
# Args:
#   base_dirs (List[str]): A list of base directory paths to scan
# 
# Behavior:
#   - Walks through each base directory recursively
#   - Checks every subdirectory
#   - Skips hidden directories (e.g., .git, .venv) and '__pycache__'
#   - Adds valid directories to sys.path so that Python can import modules from them
def import_dirs(base_dirs: List[str]):
  for base in base_dirs:
    for subdir in Path(base).glob('**/'):
      if subdir.is_dir() and not subdir.name.startswith('.') and subdir.name != '__pycache__':
        sys.path.append(str(subdir))
