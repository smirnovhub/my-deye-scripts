import json
import os
import re
import socket
import sys
import requests
import time
import unittest
import logging

import uvicorn
import multiprocessing

from pathlib import Path

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(
  current_path,
  [
    os.path.join(base_path, 'common'),
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'deyestorage'),
  ],
)

from deye_storage import app
from deye_utils import DeyeUtils
from deye_exceptions import DeyeCacheException
from deye_register_cache_data import DeyeRegisterCacheData
from deye_registers_remote_cache_manager import DeyeRegistersRemoteCacheManager

def get_safe_file_name(string: str) -> str:
  return re.sub(r'[^a-zA-Z0-9-]+', '-', string).strip('-')

cache_server_host = '127.0.0.1'
cache_server_port = 5000

BASE_URL = f"http://{cache_server_host}:{cache_server_port}"
CACHE_URL = f"{BASE_URL}/cache"

test_inverter_name = get_safe_file_name("test_inverter")
test_inverter_serial = 1234567

log = logging.getLogger()

def run_cache_server():
  """Function to run the uvicorn server."""
  # Load the config from the JSON file
  try:
    with open("log_config.json", "r") as f:
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

def wait_for_server_ready(host: str, port: int, timeout: float = 5) -> bool:
  """
  Wait until the server port is open.
  """
  log.info("Waiting for server to be ready...")
  start_time = time.time()
  while time.time() - start_time < timeout:
    try:
      with socket.create_connection((host, port), timeout = 1):
        log.info("Server is ready!")
        return True
    except (ConnectionRefusedError, OSError):
      time.sleep(0.1)

  log.info("Server did not become ready in time.")
  return False

class TestDeyeRegistersRemoteCacheManager(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    """Run once to ensure the server is even alive."""
    # Quick check if server is up
    try:
      # We use a short timeout just for the ping
      requests.get(CACHE_URL, timeout = 3)
    except Exception as e:
      raise RuntimeError(f"Abort: Cache server is unreachable at {CACHE_URL}")

  def setUp(self):
    # The base endpoint for the cache server
    self.cache_manager = DeyeRegistersRemoteCacheManager(test_inverter_name, test_inverter_serial, CACHE_URL)

    # This will now fail the test suite immediately if the server is down
    # as reset_cache() will raise an exception.
    try:
      self.cache_manager.reset_cache()
    except Exception as e:
      self.fail(f"Failed to reset cache before test: {e}")

    # Shared test data
    self.reg_100 = DeyeRegisterCacheData(100, 1, 60, [123])
    self.reg_100_json = {self.reg_100.address: self.reg_100}

  def tearDown(self):
    # Always close the session to prevent ResourceWarnings
    self.cache_manager.close()

  def test_endpoint_construction(self):
    """
    LOGIC: Verify that the manager correctly appends the inverter name to the URL.
    """
    expected_url = f"{CACHE_URL}/{test_inverter_name}-{test_inverter_serial}"
    self.assertEqual(self.cache_manager._inverter_cache_endpoint, expected_url)

  def test_remote_save_and_retrieve_integrity(self):
    """
    LOGIC: Ensure data sent via POST is retrievable via GET and maintains integrity.
    """
    # 1. Save data to remote server
    self.cache_manager.save_to_cache(self.reg_100_json)

    # 2. Retrieve data
    # Base class calls _get_json() which should return the data we just saved
    results = self.cache_manager.get_cached_registers(self.reg_100_json)

    self.assertIn(self.reg_100.address, results)
    self.assertEqual(results[self.reg_100.address].values, self.reg_100.values)
    self.assertEqual(results[self.reg_100.address].address, self.reg_100.address)

  def test_remote_404_as_empty_cache(self):
    """
    EDGE CASE: Verify that HTTP 404 from server is handled as "no data" 
    rather than a crash, returning an empty dictionary.
    """
    # Manager for an inverter that definitely has no data yet
    ghost_manager = DeyeRegistersRemoteCacheManager("UnknownInverter", 6263423454, CACHE_URL)

    # Should not raise exception, should return empty dict
    results = ghost_manager.get_cached_registers(self.reg_100_json)
    self.assertEqual(results, {})
    ghost_manager.close()

  def test_remote_ttl_enforcement_mixed_data(self):
    """
    BASE LOGIC: Verify that only expired registers are filtered out, 
    while valid ones remain in the result.
    """
    # 1. Prepare 3 registers:
    # Reg 500: Short TTL (1s) -> should expire
    # Reg 600: Long TTL (60s) -> should stay
    # Reg 700: Long TTL (60s) -> should stay
    short_ttl_reg = DeyeRegisterCacheData(500, 1, 1, [555])
    long_ttl_reg1 = DeyeRegisterCacheData(600, 3, 30, [666, 777, 100])
    long_ttl_reg2 = DeyeRegisterCacheData(700, 2, 60, [888, 999])

    registers_map = {
      short_ttl_reg.address: short_ttl_reg,
      long_ttl_reg1.address: long_ttl_reg1,
      long_ttl_reg2.address: long_ttl_reg2,
    }

    # 2. Save all to remote cache
    self.cache_manager.save_to_cache(registers_map)

    # 3. Verify they all exist initially
    res_initial = self.cache_manager.get_cached_registers(registers_map)
    self.assertEqual(len(res_initial), 3, "Initially all 3 registers should be in cache")

    # 4. Wait for the short TTL to expire (TTL=1, wait 2s for stability)
    time.sleep(3)

    # 5. Retrieve again
    res_after = self.cache_manager.get_cached_registers(registers_map)

    # 6. Assertions
    self.assertEqual(len(res_after), 2, "Only 2 registers should remain after partial expiration")
    self.assertNotIn(short_ttl_reg.address, res_after, "Register 500 should be filtered out (expired)")
    self.assertIn(long_ttl_reg1.address, res_after, "Register 600 should still be in cache")
    self.assertIn(long_ttl_reg2.address, res_after, "Register 700 should still be in cache")

    # Verify values of remaining registers
    self.assertEqual(res_after[long_ttl_reg1.address].values, long_ttl_reg1.values)
    self.assertEqual(res_after[long_ttl_reg2.address].values, long_ttl_reg2.values)

  def test_remote_server_side_merge(self):
    """
    LOGIC: Verify that multiple saves result in merged data on the server.
    Since _read_json is empty, we rely entirely on server's dict.update().
    """
    # Save first register
    reg1 = DeyeRegisterCacheData(101, 1, 60, [563])
    self.cache_manager.save_to_cache({reg1.address: reg1})

    # Save second register separately
    reg2 = DeyeRegisterCacheData(102, 1, 60, [154])
    self.cache_manager.save_to_cache({reg2.address: reg2})

    # Request both - server should have merged them
    results = self.cache_manager.get_cached_registers({reg1.address: reg1, reg2.address: reg2})

    self.assertEqual(len(results), 2)
    self.assertEqual(results[reg1.address].values, reg1.values)
    self.assertEqual(results[reg2.address].values, reg2.values)

  def test_server_unavailable_raises_exception(self):
    """
    ROBUSTNESS: Verify that if the server disappears, we get an DeyeCacheException.
    """
    # Point to a completely invalid address
    manager = DeyeRegistersRemoteCacheManager(test_inverter_name, test_inverter_serial, "http://127.0.0.1:1")
    with self.assertRaises(DeyeCacheException):
      manager.get_cached_registers(self.reg_100_json)
      manager.close()

  def test_unknown_host_raises_exception(self):
    """
    ROBUSTNESS: Verify that if the cache server's host is unknown, we get an DeyeCacheException.
    """
    # Point to a completely invalid address
    manager = DeyeRegistersRemoteCacheManager(test_inverter_name, test_inverter_serial, "http://some.unknown.host")
    with self.assertRaises(DeyeCacheException):
      manager.get_cached_registers(self.reg_100_json)
      manager.close()

if __name__ == "__main__":
  logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  log.info(f"Starting cache server at {cache_server_host}:{cache_server_port}...")
  server_process = multiprocessing.Process(target = run_cache_server, daemon = True)
  server_process.start()

  if wait_for_server_ready(cache_server_host, cache_server_port):
    try:
      unittest.main(verbosity = 2)
    finally:
      server_process.terminate()
      server_process.join()
  else:
    server_process.terminate()
