import asyncio
import json
import logging
import os
from pathlib import Path
import socket
import sys
import time
import uvicorn
import logging.config
import multiprocessing

from typing import List
from contextlib import contextmanager
from env_utils import EnvUtils
from deye_logger import DeyeLogger

class DeyeTestUtils:
  storage_server_host = '127.0.0.1'
  storage_server_port = 5000

  @staticmethod
  def setup_test_environment(log_name: str) -> None:
    os.environ[EnvUtils.IS_TEST_RUN] = 'true'
    os.environ[EnvUtils.DEYE_LOG_NAME] = log_name

    num = 1
    port = 7000

    os.environ[EnvUtils.DEYE_MASTER_LOGGER_HOST] = '127.0.0.1'
    os.environ[EnvUtils.DEYE_MASTER_LOGGER_SERIAL] = str(num)
    os.environ[EnvUtils.DEYE_MASTER_LOGGER_PORT] = str(port)

    for i in range(1, 4):
      num += 1
      port += 1
      os.environ[EnvUtils.DEYE_SLAVE_LOGGER_HOST.format(i)] = '127.0.0.1'
      os.environ[EnvUtils.DEYE_SLAVE_LOGGER_SERIAL.format(i)] = str(num)
      os.environ[EnvUtils.DEYE_SLAVE_LOGGER_PORT.format(i)] = str(port)

    os.environ[EnvUtils.REMOTE_CACHE_SERVER_URL] = ""

  @staticmethod
  def turn_on_remote_cache() -> None:
    os.environ[EnvUtils.REMOTE_CACHE_SERVER_URL] = (f"http://{DeyeTestUtils.storage_server_host}:"
                                                    f"{DeyeTestUtils.storage_server_port}/cache")

  @staticmethod
  @contextmanager
  def storage_server():
    # Start the server process
    server_process = DeyeTestUtils._run_storage_server()
    try:
      yield
    finally:
      # Stop the server process automatically when exiting the 'with' block
      DeyeTestUtils._stop_storage_server(server_process)

  @staticmethod
  def _run_storage_server() -> multiprocessing.Process:
    logger = logging.getLogger()
    logger.info(f"Starting cache server at {DeyeTestUtils.storage_server_host}:"
                f"{DeyeTestUtils.storage_server_port}...")
    server_process = multiprocessing.Process(target = DeyeTestUtils._run_server, daemon = True)
    server_process.start()

    # Waiting for server start
    DeyeTestUtils._wait_for_storage_server_ready()

    # Check if server is alive
    if not server_process.is_alive():
      exit_code = server_process.exitcode
      logger.error(f"Storage server died with exit code {exit_code}")
      sys.exit(1)

    return server_process

  @staticmethod
  def _stop_storage_server(process: multiprocessing.Process) -> None:
    logger = logging.getLogger()
    logger.info("Shutting cache server down...")
    process.terminate()
    process.join()

  @staticmethod
  def _run_server() -> None:
    # Load the config from the JSON file
    current_dir = Path(__file__).parent.resolve()
    config_path = current_dir / "log_config.json"

    if not config_path.exists():
      print(f"Config not found at: {config_path}")
      sys.exit(1)

    try:
      with open(config_path, "r") as f:
        log_config = json.load(f)
      logging.config.dictConfig(log_config)
      logger = logging.getLogger(__name__)
    except Exception as e:
      print(f"Failed to load logging config: {e}")
      sys.exit(1)

    try:
      for logger_name in ["uvicorn", "uvicorn.default", "uvicorn.error", "uvicorn.access"]:
        l = logging.getLogger(logger_name)
        l.propagate = False

      from deye_storage import app

      uvicorn.run(
        app,
        host = DeyeTestUtils.storage_server_host,
        port = DeyeTestUtils.storage_server_port,
        log_config = log_config,
        proxy_headers = False,
        forwarded_allow_ips = None,
        use_colors = False,
      )
    except Exception as e:
      logger.error(f"Failed to run storage server: {e}")
      sys.exit(1)

  @staticmethod
  def _wait_for_storage_server_ready(timeout: float = 5) -> bool:
    """
    Wait until the server port is open.
    """
    logger = logging.getLogger()
    logger.info("Waiting for storage server to be ready...")

    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        with socket.create_connection(
          (
            DeyeTestUtils.storage_server_host,
            DeyeTestUtils.storage_server_port,
          ),
            timeout = 0.1,
        ):
          logger.info("Storage server is ready!")
          return True
      except (ConnectionRefusedError, OSError):
        time.sleep(0.1)

    logger.error("Storage server did not become ready in time.")
    return False

  @staticmethod
  async def wait_for_solarman_servers_ready(loggers: List[DeyeLogger], timeout: float = 5) -> bool:
    """
    Wait until all solarman server ports for all loggers are open.
    """
    logger_tools = logging.getLogger()
    logger_tools.info(f"Waiting for {len(loggers)} solarman server(s) to be ready...")

    async def check_single_logger(deye_logger: DeyeLogger) -> bool:
      """
      Internal helper to check one specific logger with a timeout.
      """
      start_time = asyncio.get_running_loop().time()
      while asyncio.get_running_loop().time() - start_time < timeout:
        try:
          # Try to open a connection to the specific logger's address and port
          reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
              deye_logger.address,
              deye_logger.port,
            ),
            timeout = 0.5,
          )
          writer.close()
          await writer.wait_closed()
          return True
        except (ConnectionRefusedError, OSError, asyncio.TimeoutError):
          await asyncio.sleep(0.2)

      logger_tools.error(
        f"Logger '{deye_logger.name}' ({deye_logger.address}:{deye_logger.port}) did not become ready.")
      return False

    # Run all checks concurrently
    results = await asyncio.gather(*(check_single_logger(l) for l in loggers))

    # Return True only if ALL loggers are ready
    if all(results):
      logger_tools.info("All solarman servers are ready!")
      return True

    return False
