import json
import asyncio
import logging
import sys
import time
import uvicorn

from typing import Dict, Any
from datetime import datetime

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from src.deyecache_config import DeyeCacheConfig

# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Manage the lifespan of the FastAPI application.

  This function handles startup and shutdown events for the Deye Cache service.
  """
  logger = logging.getLogger("uvicorn.default")

  # This code runs on startup
  logger.info(f"----- Deye Cache started -----")
  config.print_config(logger)
  logger.info(f"------------------------------")

  # The application runs here
  yield

  # This code runs on shutdown
  logger.info("DeyeCache service is shutting down...")

app = FastAPI(
  lifespan = lifespan,
  docs_url = "/",
  # This setting hides the "Schemas" section at the bottom
  swagger_ui_parameters = {"defaultModelsExpandDepth": -1})

config = DeyeCacheConfig()

# In-memory storage for any JSON data
cache_storage: Dict[str, Any] = {}

# Lock per inverter
locks: Dict[str, asyncio.Lock] = {}
# Global lock to protect access to the locks dictionary
locks_lock = asyncio.Lock()

def deep_merge(source: Dict[str, Any], update: Dict[str, Any]) -> None:
  """
  Recursively merges 'update' into 'source'.
  """
  for key, value in update.items():
    if isinstance(value, dict) and key in source and isinstance(source[key], dict):
      # If both are dicts, go deeper
      deep_merge(source[key], value)
    else:
      # Otherwise, just overwrite or add the value
      source[key] = value

async def get_lock(key: str) -> asyncio.Lock:
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
  async with locks_lock:
    if key not in locks:
      locks[key] = asyncio.Lock()
    return locks[key]

@app.get("/ping")
def ping():
  """
  Health check endpoint that verifies the service is running
  """
  return {"status": "success"}

@app.get("/cache/{key}")
async def get_cache_by_key(key: str):
  """
  Returns cached data for the specified key
  """
  data = cache_storage.get(key)
  if data is None:
    # Return 404 if the key was not found in the cache
    raise HTTPException(status_code = 404, detail = f"Key not found")

  return data

@app.post("/cache/{key}")
async def update_cache_by_key(key: str, json_data: Dict[str, Any], request: Request):
  """
  Updates the cache data for the specified key using a recursive deep merge.
  Works with any nested JSON structure
  """
  # Check for maximum JSON size limit by checking Content-Length header
  content_length = request.headers.get("Content-Length")
  if content_length:
    if not content_length.isdigit():
      raise HTTPException(status_code = 400, detail = "Invalid Content-Length header")
    if int(content_length) > config.MAX_JSON_SIZE:
      raise HTTPException(status_code = 413, detail = "JSON body size exceeded")

  # Check for maximum JSON size limit
  # Get raw body to calculate actual byte size accurately
  body = await request.body()
  if len(body) > config.MAX_JSON_SIZE:
    raise HTTPException(status_code = 413, detail = "JSON body size exceeded")

  async with locks_lock:
    is_new_key = key not in cache_storage
    if is_new_key and len(cache_storage) >= config.MAX_KEYS_COUNT:
      raise HTTPException(status_code = 403, detail = "Maximum number of cache keys exceeded")

    # Can't use get_lock() here, because we need to
    # check keys and get new lock inssde locks_lock
    if key not in locks:
      locks[key] = asyncio.Lock()

    lock = locks[key]

  async with lock:
    header = {
      "last_update_ts": int(time.time()),
      "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "last_update_by": request.client.host if request.client else "unknown",
    }

    current_data = cache_storage.get(key)
    if not current_data:
      current_data = header.copy()

    current_data_json_str = json.dumps(current_data).encode("utf-8")
    if len(current_data_json_str) > config.MAX_JSON_STORAGE_SIZE:
      raise HTTPException(status_code = 413, detail = f"JSON storage size exceeded")

    # Perform the recursive merge
    deep_merge(current_data, json_data)
    current_data.update(header)

    cache_storage[key] = current_data

  return {"status": "success"}

@app.delete("/cache/{key}")
async def reset_cache_by_key(key: str):
  """
  Clears the cache data for the specific key
  """
  async with locks_lock:
    if key not in cache_storage:
      raise HTTPException(status_code = 404, detail = "Key not found")

    # Getting key lock inside locks_lock
    lock = locks[key]

  async with lock:
    del cache_storage[key]
    return {"status": "success"}

@app.delete("/cache")
async def reset_all_cache():
  """
  Clears all cached data for all keys
  """
  async with locks_lock:
    cache_storage.clear()
  return {"status": "success"}

@app.get("/stat")
async def get_cache_stat():
  """
  Get cache statistics
  """
  total_bytes = 0

  for data in cache_storage.values():
    # Calculate raw JSON size in bytes
    entry_json = json.dumps(data).encode("utf-8")
    total_bytes += len(entry_json)

  # Max possible size if every key reached its limit
  max_possible_bytes = config.MAX_KEYS_COUNT * config.MAX_JSON_STORAGE_SIZE

  return {
    "keys_used": len(cache_storage),
    "keys_limit": config.MAX_KEYS_COUNT,
    "bytes_used": total_bytes,
    "bytes_limit": max_possible_bytes,
    "usage_percent": {
      "keys": round((len(cache_storage) / config.MAX_KEYS_COUNT) * 100),
      "memory": round((total_bytes / max_possible_bytes) * 100),
    },
  }

if __name__ == "__main__":
  config.print_usage()

  # Load the config from the JSON file
  try:
    with open("log_config.json", "r") as f:
      log_config = json.load(f)
  except Exception as e:
    print(f"Failed to load logging config: {e}")
    sys.exit(1)

  uvicorn.run(
    app,
    host = config.SERVER_HOST,
    port = config.SERVER_PORT,
    timeout_keep_alive = 15,
    proxy_headers = False,
    forwarded_allow_ips = None,
    log_config = log_config,
    use_colors = False,
  )
