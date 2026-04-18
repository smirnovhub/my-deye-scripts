import os
import logging
import sys
import uvicorn

from typing import Dict, Any

from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, status
from fastapi.middleware.gzip import GZipMiddleware

utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../common/utils"))
sys.path.append(utils_path)

from log_utils import LogUtils
from common_utils import CommonUtils
from src.deye_storage_config import DeyeStorageConfig
from src.deye_storage_manager import DeyeStorageManager

config = DeyeStorageConfig()

DATA_DIR = f"data/{config.LOG_NAME}"
# Path for the persistent storage file
STORAGE_FILE_PATH = os.path.join(DATA_DIR, "storage.json")
CACHE_FILE_PATH = os.path.join(DATA_DIR, "cache.json")
AVERAGE_FILE_PATH = os.path.join(DATA_DIR, "average.json")

logger = LogUtils.setup_hourly_overwrite_file_logger(
  log_dir = DATA_DIR,
  log_file_template = "deye-storage-{0}.log",
)

cache_manager = DeyeStorageManager(
  config = config,
  logger = logger,
)

average_manager = DeyeStorageManager(
  config = config,
  logger = logger,
)

storage_manager = DeyeStorageManager(
  config = config,
  logger = logger,
)

# Define the lifespan context manager
@asynccontextmanager
async def lifespan_handler(app: FastAPI):
  """
  Manage the lifespan of the FastAPI application.

  This function handles startup and shutdown events for the Deye Storage service.
  """
  # This code runs on startup
  logger.info("----- Deye Storage started -----")
  config.print_config(logger)
  logger.info("------------------------------")

  external_ip = CommonUtils.get_external_ip()
  actual_ip = external_ip if external_ip else config.SERVER_HOST

  logger.info(f"Listening on: {actual_ip}:{config.SERVER_PORT}")

  # Storage restoring logic
  storage_manager.load_from_file(STORAGE_FILE_PATH)

  # The application runs here
  yield

  try:
    # Ensure directory exists before saving
    os.makedirs(DATA_DIR, exist_ok = True)
  except Exception:
    pass

  # Storage save logic
  storage_manager.save_to_file(STORAGE_FILE_PATH)
  cache_manager.save_to_file(CACHE_FILE_PATH)
  average_manager.save_to_file(AVERAGE_FILE_PATH)

  # This code runs on shutdown
  logger.info("Deye Storage service is shutting down...")

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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
  # Log the path and stack trace once for the entire application
  original_exc = CommonUtils.get_original_error(exc)
  # Extract clean message
  error_message = str(original_exc)

  if isinstance(original_exc, KeyError):
    error_message = f"KeyError: {error_message}"

  logger.error(f"Exception at {request.url.path}: {error_message}", exc_info = exc)
  return JSONResponse(
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
    content = {
      "detail": f"deyestorage: {error_message}",
      "path": request.url.path,
    },
  )

@app.get("/ping", tags = ["Server Health Operations"])
def ping():
  """
  Health check endpoint that verifies the service is running
  """
  return {"status": "success"}

#######################################
### CACHE LOGIC (TEMPORARY STORAGE) ###
#######################################

@app.get("/cache/{key}", tags = ["Cache Read Operations"])
async def get_cache_by_key(key: str):
  """
  Returns cached data for the specified key
  """
  return cache_manager.get(key)

@app.post("/cache/{key}", tags = ["Cache Update Operations"])
async def update_cache_by_key(key: str, json_data: Dict[str, Any], request: Request):
  """
  Updates the storage data for the specified key using a recursive deep merge.
  Works with any nested JSON structure
  """
  return await cache_manager.update(
    key = key,
    json_data = json_data,
    request = request,
  )

@app.delete("/cache/{key}", tags = ["Cache Remove Operations"])
async def remove_cache_by_key(key: str):
  """
  Remove the cache data for the specific key
  """
  return await cache_manager.remove(key = key)

@app.delete("/cache", tags = ["Cache Remove Operations"])
async def remove_all_cache():
  """
  Remove all cached data for all keys
  """
  return await cache_manager.clear()

@app.options("/cache", tags = ["Cache Statistics Operations"])
async def get_cache_stat():
  return cache_manager.get_stat()

#########################################
### STORAGE LOGIC (PERMANENT STORAGE) ###
#########################################

@app.get("/storage/{key}", tags = ["Storage Read Operations"])
async def get_storage_by_key(key: str):
  """
  Returns stored data for the specified key
  """
  return storage_manager.get(key)

@app.post("/storage/{key}", tags = ["Storage Update Operations"])
async def update_storage_by_key(key: str, json_data: Dict[str, Any], request: Request):
  """
  Updates the storage data for the specified key using a recursive deep merge.
  Works with any nested JSON structure
  """
  return await storage_manager.update(
    key = key,
    json_data = json_data,
    request = request,
  )

@app.delete("/storage/{key}", tags = ["Storage Remove Operations"])
async def remove_storage_by_key(key: str):
  """
  Remove the storage data for the specific key
  """
  return await storage_manager.remove(key = key)

@app.options("/storage", tags = ["Storage Statistics Operations"])
async def get_storage_stat():
  return storage_manager.get_stat()

#########################################
### AVERAGE LOGIC (TEMPORARY STORAGE) ###
#########################################

@app.get("/average/{key}", tags = ["Average Operations"])
async def get_average(key: str):
  """
  Get the current calculated average and both totals for the specified key.
  """
  return average_manager.get_average(key)

@app.delete("/average/{key}", tags = ["Average Operations"])
async def remove_average(key: str):
  """
  Remove the calculated average for the specified key.
  """
  return await average_manager.remove(key = key)

@app.post("/average/{key}/{count1}/{count2}", tags = ["Average Operations"])
async def update_average(key: str, count1: float, count2: float, request: Request):
  """
  Update totals using path parameters: /average/my_key/10.5/20
  Returns the calculated weighted average: total1 / (total1 + total2)
  """
  return await average_manager.update_average(
    key = key,
    count1 = count1,
    count2 = count2,
    request = request,
  )

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
