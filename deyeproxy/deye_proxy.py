import os
import sys
import asyncio

utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../common/utils"))
sys.path.append(utils_path)

from src.deye_proxy_config import DeyeProxyConfig
from deye_proxy_read_only import main_read_only
from deye_proxy_read_write import main_read_write

if __name__ == "__main__":
  config = DeyeProxyConfig()

  if config.READ_ONLY:
    asyncio.run(main_read_only())
  else:
    main_read_write()
