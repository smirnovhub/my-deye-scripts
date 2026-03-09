import os
import sys
import json
import logging

from pathlib import Path

import uvicorn
import multiprocessing

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(
  current_path,
  [
    'src',
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'deyestorage'),
    os.path.join(base_path, 'common'),
  ],
)

from deyestorage import app
from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from deye_test_utils import DeyeTestUtils

cache_server_host = '127.0.0.1'
cache_server_port = 5000

DeyeTestUtils.setup_test_environment()

os.environ['REMOTE_CACHE_SERVER_URL'] = f'http://{cache_server_host}:{cache_server_port}/cache'

from deye_registers_cache_test_base import main_test_logic

log = logging.getLogger()
loggers = DeyeLoggers()

if not loggers.is_test_loggers:
  log.info('ERROR: your loggers are not test loggers')
  sys.exit(1)

def run_cache_server():
  """Function to run the uvicorn server."""

  # Load the config from the JSON file
  try:
    with open(f"{base_path}/deyestorage/log_config.json", "r") as f:
      log_config = json.load(f)
  except Exception as e:
    print(f"Failed to load logging config: {e}")
    sys.exit(1)

  for logger_name in ["uvicorn", "uvicorn.default", "uvicorn.error", "uvicorn.access"]:
    l = logging.getLogger(logger_name)
    l.propagate = False

  uvicorn.run(
    app,
    host = cache_server_host,
    port = cache_server_port,
    log_config = log_config,
    proxy_headers = False,
    forwarded_allow_ips = None,
    use_colors = False,
  )

if __name__ == '__main__':
  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  log.info(f"Starting cache server at {cache_server_host}:{cache_server_port}...")
  server_process = multiprocessing.Process(target = run_cache_server, daemon = True)
  server_process.start()

  try:
    main_test_logic()
  finally:
    log.info("Shutting cache server down...")
    server_process.terminate()
    server_process.join()
