import json
import logging
import os
import socket
import sys
import time
import uvicorn
import logging.config
import multiprocessing

from contextlib import contextmanager

class DeyeTestUtils:
  storage_server_host = '127.0.0.1'
  storage_server_port = 5000

  @staticmethod
  def setup_test_environment(log_name: str) -> None:
    os.environ['IS_TEST_RUN'] = 'true'
    os.environ['DEYE_LOG_NAME'] = log_name

    num = 1
    port = 7000

    os.environ['DEYE_MASTER_LOGGER_HOST'] = '127.0.0.1'
    os.environ['DEYE_MASTER_LOGGER_SERIAL'] = str(num)
    os.environ['DEYE_MASTER_LOGGER_PORT'] = str(port)

    for i in range(1, 4):
      num += 1
      port += 1
      os.environ[f'DEYE_SLAVE{i}_LOGGER_HOST'] = '127.0.0.1'
      os.environ[f'DEYE_SLAVE{i}_LOGGER_SERIAL'] = str(num)
      os.environ[f'DEYE_SLAVE{i}_LOGGER_PORT'] = str(port)

    os.environ['REMOTE_CACHE_SERVER_URL'] = ""

  @staticmethod
  def turn_on_remote_cache() -> None:
    os.environ['REMOTE_CACHE_SERVER_URL'] = (f"http://{DeyeTestUtils.storage_server_host}:"
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
    try:
      with open("log_config.json", "r") as f:
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
