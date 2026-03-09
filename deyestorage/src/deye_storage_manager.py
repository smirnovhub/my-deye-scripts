import os
import json
import logging
import time
import asyncio

from typing import Dict, Any, Optional
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
          self._storage.update(loaded_data)
          self._locks = {key: asyncio.Lock() for key in self._storage}
          self._logger.info(f"Restored {len(loaded_data)} keys from {filename}")
      except Exception as e:
        self._logger.error(f"Failed to load storage from {filename}: {e}")
    else:
      self._logger.warning(f"File {filename} doesn't exist.")

  async def _get_lock(self, key: str) -> asyncio.Lock:
    """
    Asynchronously retrieves or creates a lock for a given key.

    This function manages a dictionary of asyncio locks, ensuring thread-safe access
    to lock creation and retrieval. If a lock for the specified key doesn't exist,
    it creates a new one before returning it.

    Args:
      key (str): The identifier for the lock.

    Returns:
      asyncio.Lock: The lock object associated with the given key.
    """
    async with self._locks_lock:
      if key not in self._locks:
        self._locks[key] = asyncio.Lock()
      return self._locks[key]

  def _deep_merge(
    self,
    source: Dict[str, Any],
    update: Dict[str, Any],
  ) -> None:
    """
    Recursively merges 'update' into 'source'.
    """
    for key, value in update.items():
      if isinstance(value, dict) and key in source and isinstance(source[key], dict):
        # If both are dicts, go deeper
        self._deep_merge(source[key], value)
      else:
        # Otherwise, just overwrite or add the value
        source[key] = value
