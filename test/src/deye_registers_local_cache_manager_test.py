import os
import re
import sys
import asyncio
import tempfile
import time
import unittest

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
from deye_registers_local_cache_manager_async import DeyeRegistersLocalCacheManagerAsync

class TestDeyeRegistersLocalCacheManagerAsync(unittest.IsolatedAsyncioTestCase):
  # Annotations for mypy
  temp_dir: tempfile.TemporaryDirectory
  cache_manager: DeyeRegistersLocalCacheManagerAsync

  def get_safe_file_name(self, string: str) -> str:
    return re.sub(r'[^a-zA-Z0-9-]+', '-', string).strip('-')

  def setUp(self):
    # Create a truly isolated temporary directory for this test run
    self.temp_dir = tempfile.TemporaryDirectory()

    # Patch the lock_path BEFORE initializing the manager
    # This redirects all DeyeUtils and path logic to our temp folder
    self.patcher = patch('deye_file_lock.DeyeFileLock.lock_path', self.temp_dir.name)
    self.patcher.start()

    self.name = 'test_inverter'
    self.serial = 1234567
    self.cache_manager = DeyeRegistersLocalCacheManagerAsync(self.name, self.serial)

    safe_name = self.get_safe_file_name(self.name)

    # Path to the file created by the manager
    self.expected_file_path = os.path.join(self.temp_dir.name, f'registers-cache-{safe_name}-{self.serial}.json')

    # Sample register for base logic testing
    self.reg_100 = DeyeRegisterCacheData(
      address = 100,
      quantity = 1,
      caching_time = 60,
      values = [42],
      read_ts = time.time(),
    )

  def tearDown(self):
    self.patcher.stop()
    self.temp_dir.cleanup()

  async def test_initialization(self):
    """
    Verify that LocalCacheManager correctly triggers directory and file creation during init.
    """
    self.assertTrue(os.path.exists(self.expected_file_path), 'Cache file should be created on init')

  async def test_save_and_retrieve(self):
    """
    Verify the full cycle from save_to_cache to get_cached_registers.
    This tests the inheritance flow: Base calls child's _save_json, then Base calls child's _get_json.
    """
    # Save
    await self.cache_manager.save_to_cache({100: self.reg_100})

    # Retrieve
    results = await self.cache_manager.get_cached_registers(
      registers_to_check = {100: self.reg_100},
      current_ts = time.time(),
    )

    self.assertIn(100, results)
    self.assertEqual(results[100].values, [42])
    self.assertEqual(results[100].address, 100)

  async def test_remote_ttl_enforcement_mixed_data(self):
    """
    BASE LOGIC: Verify that only expired registers are filtered out,
    while valid ones remain in the result.
    """
    # Prepare 3 registers:
    # Reg 500: Short TTL (1s) -> should expire
    # Reg 600: Long TTL (30s) -> should stay
    # Reg 700: Long TTL (60s) -> should stay
    short_ttl_reg = DeyeRegisterCacheData(
      address = 500,
      quantity = 1,
      caching_time = 1,
      values = [555],
      read_ts = time.time(),
    )

    long_ttl_reg1 = DeyeRegisterCacheData(
      address = 600,
      quantity = 2,
      caching_time = 30,
      values = [666, 777],
      read_ts = time.time(),
    )

    long_ttl_reg2 = DeyeRegisterCacheData(
      address = 700,
      quantity = 1,
      caching_time = 60,
      values = [888],
      read_ts = time.time(),
    )

    registers_map = {
      short_ttl_reg.address: short_ttl_reg,
      long_ttl_reg1.address: long_ttl_reg1,
      long_ttl_reg2.address: long_ttl_reg2,
    }

    # Save all to remote cache
    await self.cache_manager.save_to_cache(registers_map)

    # Verify they all exist initially
    res_initial = await self.cache_manager.get_cached_registers(
      registers_to_check = registers_map,
      current_ts = time.time(),
    )

    self.assertEqual(len(res_initial), 3, 'Initially all 3 registers should be in cache')

    # Wait for the short TTL to expire (TTL=1, wait 3s for stability)
    await asyncio.sleep(3)

    # Retrieve again
    res_after = await self.cache_manager.get_cached_registers(
      registers_to_check = registers_map,
      current_ts = time.time(),
    )

    # Assertions
    self.assertEqual(len(res_after), 2, 'Only 2 registers should remain after partial expiration')
    self.assertNotIn(short_ttl_reg.address, res_after, 'Register 500 should be filtered out (expired)')
    self.assertIn(long_ttl_reg1.address, res_after, 'Register 600 should still be in cache')
    self.assertIn(long_ttl_reg2.address, res_after, 'Register 700 should still be in cache')

    # Verify values of remaining registers
    self.assertEqual(res_after[long_ttl_reg1.address].values, long_ttl_reg1.values)
    self.assertEqual(res_after[long_ttl_reg2.address].values, long_ttl_reg2.values)

  async def test_read_modify_write(self):
    """
    Verify the 'merge' behavior in save_to_cache.
    When saving a new register, the existing ones shouldn't disappear.
    """
    # Save first
    await self.cache_manager.save_to_cache({100: self.reg_100})

    # Save second
    reg_200 = DeyeRegisterCacheData(
      address = 200,
      quantity = 1,
      caching_time = 60,
      values = [84],
      read_ts = time.time(),
    )

    await self.cache_manager.save_to_cache({200: reg_200})

    # Check both via base class method
    results = await self.cache_manager.get_cached_registers(
      registers_to_check = {
        100: self.reg_100,
        200: reg_200,
      },
      current_ts = time.time(),
    )

    self.assertEqual(len(results), 2)
    self.assertEqual(results[100].values, [42])
    self.assertEqual(results[200].values, [84])

  async def test_malformed_json_exception(self):
    """
    If the file is corrupted, the base class must raise DeyeCacheException.
    """
    # Manually corrupt the file
    with open(self.expected_file_path, 'w') as f:
      f.write('{ broken json ...')

    with self.assertRaises(DeyeCacheException) as cm:
      await self.cache_manager.get_cached_registers(
        registers_to_check = {100: self.reg_100},
        current_ts = time.time(),
      )

    self.assertIn('json parse error', str(cm.exception))

  async def test_reset(self):
    """
    Verify reset_cache() effectively clears data.
    """
    await self.cache_manager.save_to_cache({100: self.reg_100})
    await self.cache_manager.reset_cache()

    results = await self.cache_manager.get_cached_registers(
      registers_to_check = {100: self.reg_100},
      current_ts = time.time(),
    )

    self.assertEqual(len(results), 0)

  async def test_save_to_cache_permission_error_preserves_old_data(self):
    """
    Test that old cache data is preserved when a permission error occurs during save.
    """
    # Save valid data
    reg = DeyeRegisterCacheData(
      address = 100,
      quantity = 1,
      caching_time = 60,
      values = [111],
      read_ts = time.time(),
    )

    await self.cache_manager.save_to_cache({100: reg})

    # Make file Read-Only
    os.chmod(self.expected_file_path, 0o444)

    try:
      # Try to update - should fail
      with self.assertRaises(DeyeCacheException):
        await self.cache_manager.save_to_cache({
          100:
          DeyeRegisterCacheData(
            address = 100,
            quantity = 1,
            caching_time = 60,
            values = [999],
            read_ts = time.time(),
          )
        })
    finally:
      # Restore permissions for cleanup
      os.chmod(self.expected_file_path, 0o666)

    # Check data is still 111
    res = await self.cache_manager.get_cached_registers(
      registers_to_check = {100: reg},
      current_ts = time.time(),
    )

    self.assertEqual(res[100].values, [111])

  async def test_empty_register_data(self):
    # Passing [] should raise
    with self.assertRaises(DeyeCacheException):
      DeyeRegisterCacheData(
        address = 100,
        quantity = 3,
        caching_time = 60,
        values = [],
        read_ts = time.time(),
      )

  async def test_none_register_data_retrieval(self):
    """
    EDGE CASE: Verify handling of empty data lists.
    The class defaults empty values to [0] * quantity.
    """
    quantity = 2
    # Passing None should result in [0, 0] due to class logic
    empty_data_reg = DeyeRegisterCacheData(
      address = 100,
      quantity = quantity,
      caching_time = 60,
      values = None,
      read_ts = time.time(),
    )

    await self.cache_manager.save_to_cache({100: empty_data_reg})

    results = await self.cache_manager.get_cached_registers(
      registers_to_check = {100: empty_data_reg},
      current_ts = time.time(),
    )

    # Expecting the default zeros based on quantity
    self.assertEqual(results[100].values, [0] * quantity)

  async def test_permission_denied_handling(self):
    """
    SECURITY/ROBUSTNESS: Handle cases where the cache file is read-only.
    """
    # Create the file and remove write permissions
    with open(self.expected_file_path, 'w') as f:
      f.write('{}')
    os.chmod(self.expected_file_path, 0o444) # Read-only

    try:
      with self.assertRaises(DeyeCacheException) as cm:
        await self.cache_manager.save_to_cache({100: self.reg_100})
      self.assertIn('cache write error', str(cm.exception).lower())
    finally:
      os.chmod(self.expected_file_path, 0o666)

  async def test_concurrent_merging(self):
    """
    CONCURRENCY: Two managers updating different registers in the same file.
    """
    manager1 = DeyeRegistersLocalCacheManagerAsync(self.name, self.serial)
    manager2 = DeyeRegistersLocalCacheManagerAsync(self.name, self.serial)

    # Use same file for both
    manager1._cache_filename = self.expected_file_path
    manager2._cache_filename = self.expected_file_path

    reg1 = DeyeRegisterCacheData(
      address = 101,
      quantity = 1,
      caching_time = 60,
      values = [1],
      read_ts = time.time(),
    )

    reg2 = DeyeRegisterCacheData(
      address = 102,
      quantity = 1,
      caching_time = 60,
      values = [2],
      read_ts = time.time(),
    )

    await asyncio.gather(
      manager1.save_to_cache({101: reg1}),
      manager2.save_to_cache({102: reg2}),
    )

    results = await manager1.get_cached_registers(
      registers_to_check = {
        101: reg1,
        102: reg2,
      },
      current_ts = time.time(),
    )

    self.assertEqual(len(results), 2, 'Should contain data from both managers')

  async def test_dangerous_inverter_names(self):
    """
    SECURITY: Ensure that names like '../../etc/passwd' don't cause issues.
    (Actually, your code uses os.path.join, so it might create a file there).
    """
    dangerous_name = '../traversal_test'
    dm = DeyeRegistersLocalCacheManagerAsync(dangerous_name, self.serial)
    # Check if the filename is properly constructed or escaped
    safe_name = self.get_safe_file_name(dangerous_name)
    self.assertIn(safe_name, dm._cache_filename)

if __name__ == '__main__':
  unittest.main(verbosity = 2)
