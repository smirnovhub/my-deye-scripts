import os
import json
import time

from typing import Any, Dict

from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock
from deye_register_cache_data import DeyeRegisterCacheData

# -------------------------------
# Class for caching register data
# -------------------------------
class DeyeRegistersCacheManager:
  def __init__(self, name: str, cache_path: str, verbose = False):
    self.name = name
    self.cache_filename = os.path.join(cache_path, f"registers-{self.name}.json")
    self.verbose = verbose

    DeyeUtils.ensure_file_exists(self.cache_filename, mode = 0o666)

  def get_cached_registers(
    self,
    registers_to_check: Dict[int, DeyeRegisterCacheData],
  ) -> Dict[int, DeyeRegisterCacheData]:
    """
    Retrieves valid register data from the local JSON cache.
    
    This method performs a thread-safe read (using shared locks) of the cache file.
    It iterates through the requested registers and checks if their cached data
    is still valid based on the time since the last update and each register's
    specific cache_time (TTL).

    Args:
        registers_to_check (Dict[int, DeyeRegisterCacheData]): A dictionary where keys 
            are register addresses and values are data objects containing TTL 
            and quantity requirements.

    Returns:
        Dict[int, DeyeRegisterCacheData]: A dictionary containing only those registers 
            that were found in the cache and haven't expired. Each entry is a new 
            DeyeRegisterCacheData instance with populated values.

    Note:
        - If the cache file does not exist or is corrupted, an empty dictionary is returned.
        - Shared locking (LOCK_SH) is used to allow multiple concurrent readers while 
          preventing inconsistencies during write operations.
    """
    if self.verbose:
      start_time = time.perf_counter()

    results: Dict[int, DeyeRegisterCacheData] = {}

    if not os.path.exists(self.cache_filename):
      return results

    # Open in read-only mode and acquire shared lock
    with open(self.cache_filename, "r", encoding = "utf-8") as f:
      try:
        # Use shared lock (LOCK_SH) because we are only reading
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_SH)

        content = f.read()
        if not content:
          return results

        try:
          cache_content = json.loads(content)
        except (json.JSONDecodeError, ValueError):
          pass

        current_time = int(time.time())
        cached_registry = cache_content.get("registers", {})

        # Iterate through the registers we are interested in
        for addr, reg in registers_to_check.items():
          addr_str = str(addr)
          if addr_str in cached_registry:
            entry = cached_registry[addr_str]
            # Check if the cached data is still valid
            if (current_time - entry.get("time", 0)) <= reg.cache_time:
              results[addr] = DeyeRegisterCacheData(
                address = reg.address,
                quantity = reg.quantity,
                cache_time = reg.cache_time,
                values = entry.get("data", []),
              )
      except Exception as e:
        print(f"{self.name} cache read error {e}")
      finally:
        # Release the shared lock
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

    if self.verbose:
      end_time = time.perf_counter()
      duration_ms = (end_time - start_time) * 1000
      print(f"{self.name} cache read took {duration_ms:.3f} ms")

    return results

  def save_to_cache(
    self,
    registers_to_save: Dict[int, DeyeRegisterCacheData],
  ) -> None:
    """
    Updates the local JSON cache with new register data in a thread-safe manner.

    This method implements a Read-Modify-Write cycle protected by an exclusive 
    file lock (LOCK_EX). It preserves existing cached data for registers not 
    included in the current update, ensuring that the cache file remains a 
    complete record of all known register states.

    Args:
        registers_to_save (Dict[int, DeyeRegisterCacheData]): A dictionary of 
            register addresses and their corresponding data objects to be 
            persisted.
    """
    if not registers_to_save:
      return

    if self.verbose:
      start_time = time.perf_counter()

    # Open in "a+" to handle existence, reading, and locking in one go
    with open(self.cache_filename, "a+", encoding = "utf-8") as f:
      try:
        # Acquire exclusive lock
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_EX)

        # Read and parse existing content
        f.seek(0)

        cache_content: Dict[str, Any] = {
          "inverter": self.name,
          "registers": {},
        }

        content = f.read()
        if content:
          try:
            cache_content = json.loads(content)
          except (json.JSONDecodeError, ValueError):
            pass

        current_time = int(time.time())

        # Now iterating over dictionary items
        for addr, reg in registers_to_save.items():
          # Store using the address as a string key for JSON compatibility
          cache_content["registers"][str(addr)] = {
            "time": current_time,
            "data": reg.values,
          }

        # Clear file and save updated structure
        f.seek(0)
        f.truncate(0)

        json.dump(
          cache_content,
          f,
          ensure_ascii = False,
        )

        # Flush to physical storage
        f.flush()
      except Exception as e:
        print(f"{self.name} cache write error {e}")
      finally:
        # Release lock
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

    if self.verbose:
      end_time = time.perf_counter()
      duration_ms = (end_time - start_time) * 1000
      print(f"{self.name} cache save took {duration_ms:.3f} ms")
