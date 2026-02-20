import os
import sys
import json
import asyncio
import logging
import traceback
import uvicorn

from typing import Dict, Any

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from backserver_config import BackServerConfig
from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_params_processor import DeyeWebParamsProcessor
from deye_exceptions import DeyeKnownException

# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Manage the lifespan of the FastAPI application.

  This function handles startup and shutdown events for the Deye Cache service.
  """
  logger = logging.getLogger("uvicorn.default")

  # This code runs on startup
  logger.info(f"--- Deye BackServer started ---")
  config.print_config(logger)
  logger.info(f"-------------------------------")

  # The application runs here
  yield

  # This code runs on shutdown
  logger.info("Deye BackServer is shutting down...")

app = FastAPI(
  lifespan = lifespan,
  docs_url = "/",
  # This setting hides the "Schemas" section at the bottom
  swagger_ui_parameters = {"defaultModelsExpandDepth": -1})

app.add_middleware(GZipMiddleware, minimum_size = 1024)

lock = asyncio.Lock()
config = BackServerConfig()
processor = DeyeWebParamsProcessor()

def get_error_result(message: str, callstack: str = '') -> Dict[str, Any]:
  result = {
    DeyeWebConstants.result_error_field: f'Error: {message}',
  }

  if callstack and DeyeWebConstants.print_call_stack_on_exception:
    result[DeyeWebConstants.result_callstack_field] = f'<pre>{callstack}</pre>'

  return result

@app.post("/back")
async def handle_back(json_data: Dict[str, Any], request: Request):
  """
  Asynchronously handle backend requests
  """
  try:
    session_id = request.cookies.get("PHPSESSID")
    if session_id:
      json_data['session_id'] = session_id

    async with lock:
      return processor.get_params(json_data)
  except DeyeKnownException as e:
    exception_str = DeyeWebUtils.get_tail(str(e).strip('"'), ':')
    result = get_error_result(exception_str, traceback.format_exc())
    return JSONResponse(status_code = 500, content = result)
  except Exception as ee:
    result = get_error_result(str(ee), traceback.format_exc())
    return JSONResponse(status_code = 500, content = result)

if __name__ == "__main__":
  config.print_usage()

  # Load the config from the JSON file
  try:
    with open("src/backserver/log_config.json", "r") as f:
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
