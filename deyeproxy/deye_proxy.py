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
from deye_proxy_read_only_cache import SolarmanReadOnlyProxy
from deye_proxy_read_write import SolarmanReadWriteProxy

def run_read_write_proxy(config: DeyeProxyConfig) -> None:
  proxy = SolarmanReadWriteProxy(config)
  proxy.run()

async def run_read_only_proxy(config: DeyeProxyConfig) -> None:
  proxy = SolarmanReadOnlyProxy(config)
  await proxy.run()

if __name__ == "__main__":
  config = DeyeProxyConfig()
  config.validate_or_exit()

  if config.READ_ONLY:
    asyncio.run(run_read_only_proxy(config))
  else:
    run_read_write_proxy(config)
