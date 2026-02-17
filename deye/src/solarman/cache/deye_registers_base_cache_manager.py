import json
import time

from typing import Any, Dict, Optional

from abc import ABC, abstractmethod
from contextlib import contextmanager

from deye_exceptions import DeyeCacheException, DeyeKnownException
from deye_register_cache_data import DeyeRegisterCacheData

# ------------------------------------
# Base class for caching register data
# ------------------------------------
class DeyeRegistersBaseCacheManager(ABC):
  def __init__(self, name: str, verbose = False):
    self.name = name
    self.verbose = verbose

  def get_cached_registers(
    self,
    registers_to_check: Dict[int, DeyeRegisterCacheData],
  ) -> Dict[int, DeyeRegisterCacheData]:
    if self.verbose:
      start_time = time.perf_counter()

    results: Dict[int, DeyeRegisterCacheData] = {}

    try:
      content: Optional[str] = None

      with self._shared_lock_context():
        content = self._get_json()
        if not content or not content.strip():
          return results

      try:
        cache_content = json.loads(content)
      except (json.JSONDecodeError, ValueError) as e:
        raise DeyeCacheException(f"{self.name}: cache json parse error after get: {e}") from e

      current_time = int(time.time())
      cached_registry = cache_content.get("registers", {})

      # Iterate through the registers we are interested in
      for addr, reg in registers_to_check.items():
        addr_str = str(addr)
        if addr_str in cached_registry:
          entry = cached_registry[addr_str]
          # Check if the cached data is still valid
          if (current_time - entry.get("time", 0)) <= reg.caching_time:
            results[addr] = DeyeRegisterCacheData(
              address = reg.address,
              quantity = reg.quantity,
              caching_time = reg.caching_time,
              values = entry.get("data", []),
            )
    except DeyeKnownException:
      raise
    except Exception as ee:
      raise DeyeCacheException(f"{self.name}: cache read error: {ee}") from ee

    if self.verbose:
      end_time = time.perf_counter()
      duration_ms = (end_time - start_time) * 1000
      if self.verbose:
        print(f"{self.name} cache read took {duration_ms:.3f} ms")

    return results

  def save_to_cache(
    self,
    registers_to_save: Dict[int, DeyeRegisterCacheData],
  ) -> None:
    if not registers_to_save:
      return

    if self.verbose:
      start_time = time.perf_counter()

    with self._exclusive_lock_context():
      try:
        cache_content: Dict[str, Any] = {
          "inverter": self.name,
          "registers": {},
        }

        content = self._read_json()
        if content:
          try:
            cache_content = json.loads(content)
          except (json.JSONDecodeError, ValueError) as e:
            raise DeyeCacheException(f"{self.name}: cache json parse error after read: {e}") from e

        current_time = int(time.time())

        # Now iterating over dictionary items
        for addr, reg in registers_to_save.items():
          # Store using the address as a string key for JSON compatibility
          cache_content["registers"][str(addr)] = {
            "time": current_time,
            "data": reg.values,
          }

        json_string = json.dumps(
          cache_content,
          ensure_ascii = False,
        )

        self._save_json(json_string)
      except DeyeKnownException:
        raise
      except Exception as ee:
        raise DeyeCacheException(f"{self.name}: cache write error: {ee}") from ee

    if self.verbose:
      end_time = time.perf_counter()
      duration_ms = (end_time - start_time) * 1000
      if self.verbose:
        print(f"{self.name} cache save took {duration_ms:.3f} ms")

  def reset_cache(self) -> None:
    with self._exclusive_lock_context():
      try:
        self._reset()
      except DeyeKnownException:
        raise
      except Exception as ee:
        raise DeyeCacheException(f"{self.name}: cache reset error: {ee}") from ee

  @contextmanager
  def _shared_lock_context(self):
    yield

  @contextmanager
  def _exclusive_lock_context(self):
    yield

  @abstractmethod
  def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    pass

  @abstractmethod
  def _read_json(self) -> str:
    """
    Used specifically for the read-before-write cycle.
    Fetches existing data to merge with new updates. Can be overridden to return 
    an empty string if the storage backend (e.g., a smart server) handles merging automatically.
    """
    pass

  @abstractmethod
  def _save_json(self, json_string: str) -> None:
    pass

  @abstractmethod
  def _reset(self) -> None:
    pass

  def close(self):
    pass
