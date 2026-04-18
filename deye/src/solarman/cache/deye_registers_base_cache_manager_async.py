import re
import json
import time
import logging

from typing import Any, Dict, Optional

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from deye_utils import DeyeUtils
from deye_exceptions import DeyeCacheException, DeyeKnownException
from deye_register_cache_data import DeyeRegisterCacheData

# ------------------------------------
# Base class for caching register data
# ------------------------------------
class DeyeRegistersBaseCacheManagerAsync(ABC):
  def __init__(
    self,
    name: str,
    serial: int,
  ):
    self._name = re.sub(r'[^a-zA-Z0-9-]+', '-', name).strip('-')
    self._serial = abs(serial)
    self._cache_available = False
    self._logger = logging.getLogger()
    # 1000 means milliseconds
    self._ts_multiplier = 1000

  async def get_cached_registers(
    self,
    registers_to_check: Dict[int, DeyeRegisterCacheData],
    current_ts: float,
  ) -> Dict[int, DeyeRegisterCacheData]:
    if not self._cache_available:
      self._cache_available = await self._is_cache_available()

    start_time = time.perf_counter()
    results: Dict[int, DeyeRegisterCacheData] = {}

    try:
      content: Optional[str] = None

      async with self._shared_lock_context():
        content = await self._get_json()
        if not content or not content.strip():
          return results

      try:
        cache_content = json.loads(content)
      except (json.JSONDecodeError, ValueError) as e:
        raise DeyeCacheException(f"{self._name}: cache json parse error after get: {e}") from e

      current_time = int(current_ts * self._ts_multiplier)
      cached_registry = cache_content.get("registers", {})

      # Iterate through the registers we are interested in
      for addr, reg in registers_to_check.items():
        self._check_address_match(addr, reg.address)
        addr_str = str(addr)
        if addr_str in cached_registry:
          entry = cached_registry[addr_str]
          cached_time = entry.get("ts_label", 0)

          # Check if the cached data is still valid by time duration
          if (current_time - cached_time) > (reg.caching_time * self._ts_multiplier):
            continue

          # Check if midnight was crossed since the last cache update
          # Cache becomes invalid if a new day has started
          if not DeyeUtils.is_same_day(cached_time, current_time):
            continue

          results[addr] = DeyeRegisterCacheData(
            address = reg.address,
            quantity = reg.quantity,
            caching_time = reg.caching_time,
            values = entry.get("data", []),
          )
    except DeyeKnownException as e:
      self._logger.error("%s: cache read error: %s", self._name, e, exc_info = True)
      raise
    except Exception as ee:
      self._logger.error("%s: cache read error: %s", self._name, ee, exc_info = True)
      raise DeyeCacheException(f"{self._name}: cache read error: {ee}") from ee

    end_time = time.perf_counter()
    duration_ms = round((end_time - start_time) * 1000)
    self._logger.info(f"{self._name} cache read took {duration_ms} ms")
    self._logger.info(f'{self._name} got {len(results)} registers from cache')

    return results

  async def save_to_cache(
    self,
    registers_to_save: Dict[int, DeyeRegisterCacheData],
  ) -> None:
    if not registers_to_save:
      return

    if not self._cache_available:
      self._cache_available = await self._is_cache_available()

    start_time = time.perf_counter()

    try:
      async with self._exclusive_lock_context():
        cache_content: Dict[str, Any] = {
          "inverter": self._name,
          "serial": self._serial,
          "registers": {},
        }

        content = await self._read_json()
        if content:
          try:
            cache_content = json.loads(content)
          except (json.JSONDecodeError, ValueError) as e:
            raise DeyeCacheException(f"{self._name}: cache json parse error after read: {e}") from e

        # Now iterating over dictionary items
        for addr, reg in registers_to_save.items():
          if reg.read_ts < 1776451743: # It's just my current time)
            raise RuntimeError("Register read timestamp is empty")

          self._check_address_match(addr, reg.address)
          # Store using the address as a string key for JSON compatibility
          cache_content["registers"][str(addr)] = {
            "ts_label": int(reg.read_ts * self._ts_multiplier),
            "data": reg.values,
          }

        json_string = json.dumps(
          cache_content,
          ensure_ascii = False,
        )

        await self._save_json(json_string)
        self._logger.info(f'{self._name} saved {len(registers_to_save)} registers to cache')
    except DeyeKnownException as e:
      self._logger.error("%s: cache write error: %s", self._name, e, exc_info = True)
      raise
    except Exception as ee:
      self._logger.error("%s: cache write error: %s", self._name, ee, exc_info = True)
      raise DeyeCacheException(f"{self._name}: cache write error: {ee}") from ee

    end_time = time.perf_counter()
    duration_ms = round((end_time - start_time) * 1000)
    self._logger.info(f"{self._name} cache save took {duration_ms} ms")

  async def reset_cache(self) -> None:
    if not self._cache_available:
      self._cache_available = await self._is_cache_available()

    try:
      async with self._exclusive_lock_context():
        await self._reset()
      self._logger.info(f'{self._name} cache reset successful')
    except DeyeKnownException:
      raise
    except Exception as ee:
      raise DeyeCacheException(f"{self._name}: cache reset error: {ee}") from ee

  def _check_address_match(self, key: int, address: int) -> None:
    """
    Validates that the dictionary key matches the register address.

    Args:
      key: The dictionary key to validate.
      address: The register address to compare against.

    Raises:
      DeyeCacheException: If the key does not match the address, with a message
        indicating the mismatch between the dictionary key and register address.
    """
    if key != address:
      raise DeyeCacheException(f"{self._name}: register address mismatch - "
                               f"dictionary key is {key}, but register address is {address}")

  @abstractmethod
  async def _is_cache_available(self) -> bool:
    """
    Check if the cache is available.

    This method verifies whether the cache is currently available for use.

    Returns:
      bool: True if cache is available for use or False if not available
    """
    pass

  @asynccontextmanager
  async def _shared_lock_context(self):
    yield

  @asynccontextmanager
  async def _exclusive_lock_context(self):
    yield

  @abstractmethod
  async def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    pass

  @abstractmethod
  async def _read_json(self) -> str:
    """
    Used specifically for the read-before-write cycle.
    Fetches existing data to merge with new updates. Can be overridden to return 
    an empty string if the storage backend (e.g., a smart server) handles merging automatically.
    """
    pass

  @abstractmethod
  async def _save_json(self, json_string: str) -> None:
    pass

  @abstractmethod
  async def _reset(self) -> None:
    pass

  @abstractmethod
  async def update_cache_hit_rate(
    self,
    got_from_cache: int,
    got_from_inverter: int,
  ) -> None:
    pass

  @abstractmethod
  async def reset_cache_hit_rate(self) -> None:
    pass
