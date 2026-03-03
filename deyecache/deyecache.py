import os
import json
import asyncio
import logging
import socket
import sys
import time
import uvicorn

from typing import Dict, Any, Optional
from datetime import datetime

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware

utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../common/utils"))
sys.path.append(utils_path)

from src.deyecache_config import DeyeCacheConfig
from hourly_overwrite_file_handler import HourlyOverwriteFileHandler

config = DeyeCacheConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
  "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
  "%Y-%m-%d %H:%M:%S",
)

DATA_DIR = f"data/{config.LOG_NAME}"

# Path for the persistent cache storage file
CACHE_FILE_PATH = os.path.join(DATA_DIR, "cache-storage.json")

file_handler = HourlyOverwriteFileHandler(
  directory = DATA_DIR,
  log_file_template = "deye-cache-{0}.log",
)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console = logging.StreamHandler(sys.stdout)
console.setFormatter(formatter)
logger.addHandler(console)

# Define the lifespan context manager
@asynccontextmanager
async def lifespan_handler(app: FastAPI):
  """
  Manage the lifespan of the FastAPI application.

  This function handles startup and shutdown events for the Deye Cache service.
  """
  # This code runs on startup
  logger.info("----- Deye Cache started -----")
  config.print_config(logger)
  logger.info("------------------------------")

  external_ip = get_external_ip("8.8.8.8", 53)
  actual_ip = external_ip if external_ip else config.SERVER_HOST

  logger.info(f"Listening on: {actual_ip}:{config.SERVER_PORT}")

  # Cache restoring logic
  logger.info(f"Restoring cache from {CACHE_FILE_PATH}...")
  if os.path.exists(CACHE_FILE_PATH):
    try:
      with open(CACHE_FILE_PATH, "r", encoding = "utf-8") as f:
        loaded_data = json.load(f)
        cache_storage.update(loaded_data)
        logger.info(f"Restored {len(loaded_data)} keys from {CACHE_FILE_PATH}")
    except Exception as e:
      logger.error(f"Failed to load cache from {CACHE_FILE_PATH}: {e}")
  else:
    logger.warning(f"File {CACHE_FILE_PATH} doesn't exist.")

  # The application runs here
  yield

  # Cache save logic
  logger.info(f"Saving cache to {CACHE_FILE_PATH}...")
  try:
    # Ensure directory exists before saving
    os.makedirs(DATA_DIR, exist_ok = True)
    with open(CACHE_FILE_PATH, "w", encoding = "utf-8") as f:
      json.dump(cache_storage, f, ensure_ascii = False, indent = 2)
    logger.info(f"Successfully saved {len(cache_storage)} keys to {CACHE_FILE_PATH}")
  except Exception as e:
    logger.error(f"Failed to save cache to {CACHE_FILE_PATH}: {e}")

  # This code runs on shutdown
  logger.info("DeyeCache service is shutting down...")

  for handler in logging.getLogger().handlers:
    handler.flush()

  sys.stdout.flush()
  sys.stderr.flush()

app = FastAPI(
  lifespan = lifespan_handler,
  docs_url = "/",
  # This setting hides the "Schemas" section at the bottom
  swagger_ui_parameters = {"defaultModelsExpandDepth": -1},
)

app.add_middleware(GZipMiddleware, minimum_size = 1024)

# In-memory storage for any JSON data
cache_storage: Dict[str, Any] = {}

# Lock per inverter
locks: Dict[str, asyncio.Lock] = {}
# Global lock to protect access to the locks dictionary
locks_lock = asyncio.Lock()

def get_external_ip(host: str, port: int) -> Optional[str]:
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.connect((host, port))
      return s.getsockname()[0]
  except Exception:
    return None

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

@app.get("/ping", tags = ["Server Health Operations"])
def ping():
  """
  Health check endpoint that verifies the service is running
  """
  return {"status": "success"}

@app.get("/cache/{key}", tags = ["Cache Read Operations"])
async def get_cache_by_key(key: str):
  """
  Returns cached data for the specified key
  """
  data = cache_storage.get(key)
  if data is None:
    # Return 404 if the key was not found in the cache
    raise HTTPException(status_code = 404, detail = f"Key not found")

  return data

@app.post("/cache/{key}", tags = ["Cache Update Operations"])
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

@app.delete("/cache/{key}", tags = ["Cache Remove Operations"])
async def remove_cache_by_key(key: str):
  """
  Remove the cache data for the specific key
  """
  async with locks_lock:
    if key not in cache_storage:
      raise HTTPException(status_code = 404, detail = "Key not found")

    # Getting key lock inside locks_lock
    lock = locks[key]

  async with lock:
    del cache_storage[key]
    return {"status": "success"}

@app.delete("/cache", tags = ["Cache Remove Operations"])
async def remove_all_cache():
  """
  Remove all cached data for all keys
  """
  async with locks_lock:
    cache_storage.clear()
  return {"status": "success"}

@app.get("/stat", tags = ["Cache Statistics Operations"])
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
  config.print_usage(logger)

  uvicorn.run(
    app,
    host = config.SERVER_HOST,
    port = config.SERVER_PORT,
    timeout_keep_alive = 15,
    proxy_headers = False,
    forwarded_allow_ips = None,
    log_config = None,
    use_colors = False,
  )
