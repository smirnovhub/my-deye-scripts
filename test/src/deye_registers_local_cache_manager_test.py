import os
import re
import sys
import time
import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

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
  ],
)

from deye_exceptions import DeyeCacheException
from deye_register_cache_data import DeyeRegisterCacheData
from deye_registers_local_cache_manager import DeyeRegistersLocalCacheManager

class TestDeyeRegistersLocalCacheManager(unittest.TestCase):
  # Annotations for mypy
  temp_dir: tempfile.TemporaryDirectory
  cache_manager: DeyeRegistersLocalCacheManager

  def get_safe_file_name(self, string: str) -> str:
    return re.sub(r'[^a-zA-Z0-9-]+', '-', string).strip('-')

  def setUp(self):
    # 1. Create a truly isolated temporary directory for this test run
    self.temp_dir = tempfile.TemporaryDirectory()

    # 2. Patch the lock_path BEFORE initializing the manager
    # This redirects all DeyeUtils and path logic to our temp folder
    self.patcher = patch('deye_file_lock.DeyeFileLock.lock_path', self.temp_dir.name)
    self.patcher.start()

    self.name = "test_inverter"
    self.serial = 1234567
    self.cache_manager = DeyeRegistersLocalCacheManager(self.name, self.serial, verbose = False)

    safe_name = self.get_safe_file_name(self.name)

    # Path to the file created by the manager
    self.expected_file_path = os.path.join(self.temp_dir.name, f"registers-cache-{safe_name}-{self.serial}.json")

    # Sample register for base logic testing
    self.reg_100 = DeyeRegisterCacheData(
      address = 100,
      quantity = 1,
      caching_time = 60,
      values = [42],
    )

  def tearDown(self):
    self.patcher.stop()
    self.temp_dir.cleanup()

  def test_initialization(self):
    """
    Verify that LocalCacheManager correctly triggers directory and file creation during init.
    """
    self.assertTrue(os.path.exists(self.expected_file_path), "Cache file should be created on init")

  def test_save_and_retrieve(self):
    """
    Verify the full cycle from save_to_cache to get_cached_registers.
    This tests the inheritance flow: Base calls child's _save_json, then Base calls child's _get_json.
    """
    # Save
    self.cache_manager.save_to_cache({100: self.reg_100})

    # Retrieve
    results = self.cache_manager.get_cached_registers({100: self.reg_100})

    self.assertIn(100, results)
    self.assertEqual(results[100].values, [42])
    self.assertEqual(results[100].address, 100)

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
    long_ttl_reg1 = DeyeRegisterCacheData(600, 2, 30, [666, 777])
    long_ttl_reg2 = DeyeRegisterCacheData(700, 1, 60, [888])

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

  def test_read_modify_write(self):
    """
    Verify the 'merge' behavior in save_to_cache.
    When saving a new register, the existing ones shouldn't disappear.
    """
    # 1. Save first
    self.cache_manager.save_to_cache({100: self.reg_100})

    # 2. Save second
    reg_200 = DeyeRegisterCacheData(200, 1, 60, [84])
    self.cache_manager.save_to_cache({200: reg_200})

    # 3. Check both via base class method
    results = self.cache_manager.get_cached_registers({100: self.reg_100, 200: reg_200})
    self.assertEqual(len(results), 2)
    self.assertEqual(results[100].values, [42])
    self.assertEqual(results[200].values, [84])

  def test_malformed_json_exception(self):
    """
    If the file is corrupted, the base class must raise DeyeCacheException.
    """
    # Manually corrupt the file
    with open(self.expected_file_path, 'w') as f:
      f.write("{ broken json ...")

    with self.assertRaises(DeyeCacheException) as cm:
      self.cache_manager.get_cached_registers({100: self.reg_100})

    self.assertIn("json parse error", str(cm.exception))

  def test_reset(self):
    """
    Verify reset_cache() effectively clears data.
    """
    self.cache_manager.save_to_cache({100: self.reg_100})
    self.cache_manager.reset_cache()

    results = self.cache_manager.get_cached_registers({100: self.reg_100})
    self.assertEqual(len(results), 0)

  def test_save_to_cache_permission_error_preserves_old_data(self):
    """
    Test that old cache data is preserved when a permission error occurs during save.
    """
    # 1. Save valid data
    reg = DeyeRegisterCacheData(100, 1, 60, [111])
    self.cache_manager.save_to_cache({100: reg})

    # 2. Make file Read-Only
    os.chmod(self.expected_file_path, 0o444)

    try:
      # 3. Try to update - should fail
      with self.assertRaises(DeyeCacheException):
        self.cache_manager.save_to_cache({100: DeyeRegisterCacheData(100, 1, 60, [999])})
    finally:
      # Restore permissions for cleanup
      os.chmod(self.expected_file_path, 0o666)

    # 4. Check data is still 111
    res = self.cache_manager.get_cached_registers({100: reg})
    self.assertEqual(res[100].values, [111])

  def test_empty_register_data_retrieval(self):
    """
    EDGE CASE: Verify handling of empty data lists.
    The class defaults empty values to [0] * quantity.
    """
    quantity = 2
    # Passing [] should result in [0, 0] due to class logic
    empty_data_reg = DeyeRegisterCacheData(100, quantity, 60, [])
    self.cache_manager.save_to_cache({100: empty_data_reg})

    results = self.cache_manager.get_cached_registers({100: empty_data_reg})

    # Expecting the default zeros based on quantity
    self.assertEqual(results[100].values, [0] * quantity)

  def test_permission_denied_handling(self):
    """
    SECURITY/ROBUSTNESS: Handle cases where the cache file is read-only.
    """
    # Create the file and remove write permissions
    with open(self.expected_file_path, 'w') as f:
      f.write("{}")
    os.chmod(self.expected_file_path, 0o444) # Read-only

    with self.assertRaises(DeyeCacheException) as cm:
      self.cache_manager.save_to_cache({100: self.reg_100})
    self.assertIn("cache write error", str(cm.exception).lower())

  def test_concurrent_merging(self):
    """
    CONCURRENCY: Two managers updating different registers in the same file.
    """
    manager1 = DeyeRegistersLocalCacheManager(self.name, self.serial)
    manager2 = DeyeRegistersLocalCacheManager(self.name, self.serial)

    # Use same file for both
    manager1._cache_filename = self.expected_file_path
    manager2._cache_filename = self.expected_file_path

    reg1 = DeyeRegisterCacheData(101, 1, 60, [1])
    reg2 = DeyeRegisterCacheData(102, 1, 60, [2])

    manager1.save_to_cache({101: reg1})
    manager2.save_to_cache({102: reg2})

    results = manager1.get_cached_registers({101: reg1, 102: reg2})
    self.assertEqual(len(results), 2, "Should contain data from both managers")

  def test_dangerous_inverter_names(self):
    """
    SECURITY: Ensure that names like '../../etc/passwd' don't cause issues.
    (Actually, your code uses os.path.join, so it might create a file there).
    """
    dangerous_name = "../traversal_test"
    dm = DeyeRegistersLocalCacheManager(dangerous_name, self.serial)
    # Check if the filename is properly constructed or escaped
    safe_name = self.get_safe_file_name(dangerous_name)
    self.assertIn(safe_name, dm._cache_filename)

if __name__ == "__main__":
  unittest.main(verbosity = 2)
