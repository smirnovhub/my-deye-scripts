import os
import sys
import asyncio

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from src.deye_proxy_config import DeyeProxyConfig
from deye_proxy_read_only_cache import main_read_only_cache
from deye_proxy_read_write import main_read_write

if __name__ == "__main__":
  config = DeyeProxyConfig()

  if config.READ_ONLY:
    asyncio.run(main_read_only_cache())
  else:
    main_read_write()
