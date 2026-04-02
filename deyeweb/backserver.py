import os
import sys
import logging
import traceback
import uvicorn

from typing import Dict, Any

from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware

from contextlib import asynccontextmanager

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from log_utils import LogUtils
from common_utils import CommonUtils
from backserver_config import BackServerConfig
from deye_web_dependency_provider import DeyeWebDependencyProvider
from http_session_singleton_async import HttpSessionSingletonAsync

config = BackServerConfig()

logger = LogUtils.setup_hourly_overwrite_file_logger(
  log_dir = f"data/{config.LOG_NAME}",
  log_file_template = "back-server-{0}.log",
)

# Define the lifespan context manager
@asynccontextmanager
async def lifespan_handler(app: FastAPI):
  """
  Manage the lifespan of the FastAPI application.

  This function handles startup and shutdown events for the Deye Cache service.
  """
  # This code runs on startup
  logger.info(f"--- Deye BackServer started ---")
  config.print_config(logger)
  logger.info(f"-------------------------------")

  external_ip = CommonUtils.get_external_ip()
  actual_ip = external_ip if external_ip else config.SERVER_HOST

  logger.info(f"Listening on: {actual_ip}:{config.SERVER_PORT}")

  # The application runs here
  yield

  # This code runs on shutdown
  logger.info("Deye BackServer is shutting down...")

  await HttpSessionSingletonAsync.close_session()

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

dependency_provider = DeyeWebDependencyProvider()

@app.get("/front", tags = ["Frontend Operations"])
async def handle_front_requests():
  headers = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
  }

  builder = dependency_provider.front_builder
  if builder:
    try:
      html = await builder.get_front_html()
      return HTMLResponse(
        content = html,
        headers = headers,
        status_code = status.HTTP_200_OK,
      )
    except Exception as e:
      logger.error(traceback.format_exc())
      return HTMLResponse(
        content = f"<h1>Frontend Error</h1><pre>{str(e)}\n{traceback.format_exc()}</pre>",
        headers = headers,
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
      )

  # Get all errors as a formatted string
  all_errors = dependency_provider.get_all_errors()
  error_text = "\n".join(f"{name}: {err}" for name, err in all_errors.items())
  logger.error(error_text)
  return HTMLResponse(
    content = f"<h1>Frontend Error</h1><pre>{error_text}</pre>",
    headers = headers,
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
  )

@app.post("/back", tags = ["Backend Operations"])
async def handle_back_requests(json_data: Dict[str, Any]):
  processor = dependency_provider.back_params_processor
  if not processor:
    return get_error_result("Params processor module not available")

  try:
    return await processor.get_params(json_data = json_data, logger = logger)
  except Exception as e:
    logger.error(traceback.format_exc())
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
