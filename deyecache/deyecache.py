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
  logger = logging.getLogger("uvicorn.default")

  # This code runs on startup
  logger.info(f"----- Deye Cache started -----")
  config.print_config(logger)
  logger.info(f"------------------------------")

  # The application runs here
  yield

  # This code runs on shutdown
  logger.info("DeyeCache service is shutting down...")

app = FastAPI(lifespan = lifespan)
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
  Ensures thread-safe access to the locks dictionary itself.
  """
  async with locks_lock:
    if key not in locks:
      locks[key] = asyncio.Lock()
    return locks[key]

@app.get("/ping")
def ping():
  return {"status": "success"}

@app.get("/cache/{key}")
async def get_cache(key: str):
  """
  Returns the full cached data for the specified key.
  """
  return cache_storage.get(key, {})

@app.post("/cache/{key}")
async def update_cache(key: str, json_data: Dict[str, Any], request: Request):
  """
  Updates the cache using a recursive deep merge.
  Works with any nested JSON structure.
  """
  # Check for maximum number of keys limit
  if key not in cache_storage and len(cache_storage) >= config.MAX_KEYS_COUNT:
    raise HTTPException(status_code = 403, detail = "Maximum number of cache keys exceeded")

  # Check for maximum JSON size limit
  # Get raw body to calculate actual byte size accurately
  body = await request.body()
  if len(body) > config.MAX_JSON_SIZE:
    raise HTTPException(status_code = 413, detail = "JSON body size exceeds limit")

  lock = await get_lock(key)
  async with lock:
    header = {
      "last_update_ts": int(time.time()),
      "last_update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "last_update_by": request.client.host if request.client else "unknown",
    }

    # Prepare a temporary copy to validate final size before applying changes
    current_data = cache_storage.get(key, {}).copy()
    if not current_data:
      current_data = header.copy()

    # Perform a trial merge
    deep_merge(current_data, json_data)
    current_data.update(header)

    # Validate total stored size for this specific key
    # Convert back to JSON string to measure actual data size accurately
    final_json_str = json.dumps(current_data)
    if len(final_json_str) > config.MAX_JSON_STORAGE_SIZE:
      raise HTTPException(status_code = 413, detail = f"JSON storage size exceeded")

    # If all checks pass, update the real storage
    cache_storage[key] = current_data

  return {"status": "success"}

@app.delete("/cache/{key}")
async def reset_cache_item(key: str):
  """
  Clears the cache for a specific key using a lock.
  """
  lock = await get_lock(key)
  async with lock:
    if key in cache_storage:
      # Clear data for this specific resource
      del cache_storage[key]
      return {"status": "success"}
    else:
      raise HTTPException(status_code = 404, detail = "Key not found")

@app.delete("/cache")
async def reset_all_cache():
  """
  Global reset: clears all data and all locks.
  """
  async with locks_lock:
    cache_storage.clear()
    locks.clear()
  return {"status": "success"}

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
    log_config = log_config,
    use_colors = False,
  )
