import os
import json
import logging
import time
import asyncio

from typing import Dict, Any, Optional, Union
from datetime import datetime
from fastapi import HTTPException, Request

from src.deye_storage_config import DeyeStorageConfig

class DeyeStorageManager:
  def __init__(
    self,
    config: DeyeStorageConfig,
    logger: logging.Logger,
  ):
    self._config = config
    self._logger = logger
    # In-memory storage for any JSON data
    self._storage: Dict[str, Any] = {}
    # Lock per inverter
    self._locks: Dict[str, asyncio.Lock] = {}
    # Global lock to protect access to the locks dictionary
    self._locks_lock = asyncio.Lock()

  def get(self, key: str) -> Optional[Dict[str, Any]]:
    """
    Returns stored data for the specified key
    """
    data = self._storage.get(key)
    if data is None:
      # Return 404 if the key was not found in the storage
      raise HTTPException(status_code = 404, detail = f"Key not found")

    # Here better to make deep copy of the object to
    # prevent unexpected storage change from client side
    # return copy.deepcopy(data)
    return data

  async def clear(self) -> Dict[str, Any]:
    """
    Remove all stored data for all keys
    """
    async with self._locks_lock:
      self._storage.clear()
    return {"status": "success"}

  async def remove(self, key: str) -> Dict[str, Any]:
    """
    Remove the store data for the specific key
    """
    async with self._locks_lock:
      if key not in self._storage:
        raise HTTPException(status_code = 404, detail = "Key not found")

      # Getting key lock inside locks_lock
      lock = self._locks[key]

    async with lock:
      del self._storage[key]
      return {"status": "success"}

  async def update(
    self,
    key: str,
    json_data: Dict[str, Any],
    request: Request,
  ) -> Dict[str, Any]:
    """
    Updates the storage data for the specified key using a recursive deep merge.
    Works with any nested JSON structure
    """
    # Check for maximum JSON size limit by checking Content-Length header
    content_length = request.headers.get("Content-Length")
    if content_length:
      if not content_length.isdigit():
        raise HTTPException(status_code = 400, detail = "Invalid Content-Length header")
      if int(content_length) > self._config.MAX_JSON_SIZE:
        raise HTTPException(status_code = 413, detail = "JSON body size exceeded")

    # Check for maximum JSON size limit
    # Get raw body to calculate actual byte size accurately
    body = await request.body()
    if len(body) > self._config.MAX_JSON_SIZE:
      raise HTTPException(status_code = 413, detail = "JSON body size exceeded")

    async with self._locks_lock:
      is_new_key = key not in self._storage
      if is_new_key and len(self._storage) >= self._config.MAX_KEYS_COUNT:
        raise HTTPException(status_code = 403, detail = "Maximum number of keys exceeded")

      # Can't use get_lock() here, because we need to
      # check keys and get new lock inssde locks_lock
      if key not in self._locks:
        self._locks[key] = asyncio.Lock()

      lock = self._locks[key]

    async with lock:
      header = {
        "last_update_ts": int(time.time()),
        "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_update_by": request.client.host if request.client else "unknown",
      }

      current_data = self._storage.get(key)
      if not current_data:
        current_data = header.copy()

      current_data_json_str = json.dumps(current_data).encode("utf-8")
      if len(current_data_json_str) > self._config.MAX_JSON_STORAGE_SIZE:
        raise HTTPException(status_code = 413, detail = f"JSON storage size exceeded")

      # Perform the recursive merge
      self._deep_merge(current_data, json_data)
      current_data.update(header)

      self._storage[key] = current_data

    return {"status": "success"}

  def get_stat(self) -> Dict[str, Any]:
    """
    Get storage statistics
    """
    total_bytes = 0

    for data in self._storage.values():
      # Calculate raw JSON size in bytes
      entry_json = json.dumps(data).encode("utf-8")
      total_bytes += len(entry_json)

    # Max possible size if every key reached its limit
    max_possible_bytes = self._config.MAX_KEYS_COUNT * self._config.MAX_JSON_STORAGE_SIZE

    return {
      "keys_used": len(self._storage),
      "keys_limit": self._config.MAX_KEYS_COUNT,
      "bytes_used": total_bytes,
      "bytes_limit": max_possible_bytes,
      "usage_percent": {
        "keys": round((len(self._storage) / self._config.MAX_KEYS_COUNT) * 100),
        "memory": round((total_bytes / max_possible_bytes) * 100),
      },
    }

  def save_to_file(self, filename: str) -> None:
    # Storage save logic
    self._logger.info(f"Saving storage to {filename}...")
    try:
      with open(filename, "w", encoding = "utf-8") as f:
        json.dump(self._storage, f, ensure_ascii = False, indent = 2)
      self._logger.info(f"Successfully saved {len(self._storage)} keys to {filename}")
    except Exception as e:
      self._logger.error(f"Failed to save storage to {filename}: {e}")

  def load_from_file(self, filename: str) -> None:
    # Storage restoring logic
    self._logger.info(f"Restoring storage from {filename}...")
    if os.path.exists(filename):
      try:
        with open(filename, "r", encoding = "utf-8") as f:
          loaded_data = json.load(f)

          if not isinstance(loaded_data, dict):
            raise ValueError("Invalid storage format")

          self._storage.update(loaded_data)
          self._locks = {key: asyncio.Lock() for key in self._storage}
          self._logger.info(f"Restored {len(loaded_data)} keys from {filename}")
      except Exception as e:
        self._logger.error(f"Failed to load storage from {filename}: {e}")
    else:
      self._logger.warning(f"File {filename} doesn't exist.")

  def get_average(self, key: str) -> Dict[str, Any]:
    """
    Retrieves the current average and totals for the specified key.
    Returns the data directly from storage.
    """
    # Use existing get method to handle 404 if key is missing
    data = self.get(key)

    if not data:
      raise HTTPException(status_code = 404, detail = "Key not found")

    return {
      "status": "success",
      "key": key,
      "count1": self._clean_num(data.get("count1", 0.0)),
      "count2": self._clean_num(data.get("count2", 0.0)),
      "total": self._clean_num(data.get("total", 0.0)),
      "average": self._clean_num(data.get("average", 0.0)),
    }

  async def update_average(
    self,
    key: str,
    count1: float,
    count2: float,
    request: Request,
  ) -> Dict[str, Any]:
    """
    Updates two totals and returns the calculated average in the response.
    Formula: average = count1 / (count1 + count2)
    """
    async with self._locks_lock:
      # Key initialization and storage limit check
      if key not in self._locks:
        if len(self._storage) >= self._config.MAX_KEYS_COUNT:
          raise HTTPException(status_code = 403, detail = "Maximum number of keys exceeded")
        self._locks[key] = asyncio.Lock()
      lock = self._locks[key]

    async with lock:
      # Metadata for the update process
      header = {
        "last_update_ts": int(time.time()),
        "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_update_by": request.client.host if request.client else "unknown",
      }

      # Get current state from storage or set defaults
      data = self._storage.get(key, {})

      new_count1 = data.get("count1", 0.0) + count1
      new_count2 = data.get("count2", 0.0) + count2

      total = new_count1 + new_count2
      average = new_count1 / total if total != 0 else 0.0

      raw_values = {
        "count1": new_count1,
        "count2": new_count2,
        "total": total,
        "average": average,
      }

      self._storage[key] = {**header, **raw_values}

      clean_values = {k: self._clean_num(v) for k, v in raw_values.items()}

      # The response body will contain the new average immediately
      return {
        "status": "success",
        "key": key,
        **clean_values,
      }

  def _deep_merge(
    self,
    source: Dict[str, Any],
    update: Dict[str, Any],
  ) -> None:
    """
      Recursively merge dictionary 'update' into 'source' with race condition protection.

      The merge is performed in-place. If a dictionary contains a 'time' key, 
      the update is only applied if the incoming timestamp is strictly newer.
      """
    for key, value in update.items():
      src_value = source.get(key)

      # Check if we are dealing with an object that has a timestamp
      if isinstance(value, dict) and isinstance(src_value, dict):
        value_time = value.get("ts_label")
        src_time = src_value.get("ts_label")

        # If the cached timestamp is newer or equal, skip updating this specific object.
        # This prevents older network packets from overwriting fresh data.
        if isinstance(value_time, (int, float)) and isinstance(src_time, (int, float)) and src_time >= value_time:
          # Log the skip event with details for debugging
          self._logger.warning(
            "Stale data ignored for key '%s': incoming time (%s) <= cached time (%s)",
            key,
            value_time,
            src_time,
          )
          continue

      # Standard recursive logic for nested structures
      if isinstance(value, dict) and isinstance(src_value, dict):
        # If both are dictionaries, proceed deeper into the tree
        self._deep_merge(src_value, value)
      else:
        # Otherwise, just overwrite or add the value
        source[key] = value

  def _clean_num(self, v: Union[float, int]) -> Union[float, int]:
    """
    Normalizes a float value by rounding and type conversion.
    
    Rounds the input to 10 decimal places to eliminate floating-point 
    arithmetic artifacts (IEEE 754). If the resulting value is a 
    whole number, it returns an integer to ensure a clean JSON 
    representation without trailing zeros. Otherwise, returns the 
    rounded float.
    
    Args:
        v: The float value to be cleaned.
        
    Returns:
        int | float: An integer if v has no fractional part, else a rounded float.
    """
    if isinstance(v, int):
      return v

    v = round(v, 10)
    return int(v) if v.is_integer() else v
