import os
import sys
import json
import asyncio
import logging
import traceback
import uvicorn

from typing import Dict, Any

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from backserver_config import BackServerConfig
from deye_web_dependency_provider import DeyeWebDependencyProvider

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
  swagger_ui_parameters = {"defaultModelsExpandDepth": -1},
)

app.add_middleware(GZipMiddleware, minimum_size = 1024)

lock = asyncio.Lock()
config = BackServerConfig()
dependency_provider = DeyeWebDependencyProvider()

@app.get("/front", tags = ["Frontend Operations"])
async def handle_front_requests():
  builder = dependency_provider.front_builder
  if builder:
    try:
      html = builder.get_front_html()
      return HTMLResponse(content = html, status_code = 200)
    except Exception as e:
      return HTMLResponse(
        content = f"<h1>Frontend Error</h1><pre>{str(e)}\n{traceback.format_exc()}</pre>",
        status_code = 500,
      )

  # Get all errors as a formatted string
  all_errors = dependency_provider.get_all_errors()
  error_text = "\n".join(f"{name}: {err}" for name, err in all_errors.items())
  return HTMLResponse(
    content = f"<h1>Frontend Error</h1><pre>{error_text}</pre>",
    status_code = 500,
  )

@app.post("/back", tags = ["Backend Operations"])
async def handle_back_requests(json_data: Dict[str, Any]):
  processor = dependency_provider.back_params_processor
  if not processor:
    return get_error_result("Params processor module not available")

  try:
    async with lock:
      return processor.get_params(json_data)
  except Exception as e:
    known_exception_class = dependency_provider.known_exception
    utils_class = dependency_provider.utils

    if known_exception_class and isinstance(known_exception_class, type) and isinstance(
        e, known_exception_class) and utils_class:
      # Handle deye known exceptions
      exception_str = str(e)
      if utils_class:
        exception_str = utils_class.get_tail(exception_str.strip('"'), ':')
      return get_error_result(exception_str, traceback.format_exc())
    else:
      # Handle all other exceptions
      return get_error_result(str(e), traceback.format_exc())

def get_error_result(message: str, callstack: str = '') -> Dict[str, Any]:
  constants = dependency_provider.constants
  if not constants:
    return {"error": f"Error: {message} (constants module not available)"}

  result = {
    constants.result_error_field: f'Error: {message}',
  }

  if callstack and constants.print_call_stack_on_exception:
    result[constants.result_callstack_field] = f'<pre>{callstack}</pre>'

  return result

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
