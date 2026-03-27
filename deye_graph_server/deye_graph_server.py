import asyncio
import os
import sys
import logging
import uvicorn

from dataclasses import asdict
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import gzip

common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../common"))

for dir, dirs, files in os.walk(common_path):
  if dir not in sys.path:
    sys.path.append(dir)

from log_utils import LogUtils
from common_utils import CommonUtils
from src.deye_graph_server_config import DeyeGraphServerConfig
from src.deye_graph_manager import DeyeGraphManager

config = DeyeGraphServerConfig()

DATA_DIR = f"data/{config.LOG_NAME}"

logger = LogUtils.setup_hourly_overwrite_file_logger(
  log_dir = DATA_DIR,
  log_file_template = "deye-graph-server-{0}.log",
)

# Define the lifespan context manager
@asynccontextmanager
async def lifespan_handler(app: FastAPI):
  """
  Manage the lifespan of the FastAPI application.

  This function handles startup and shutdown events for the Deye Storage service.
  """
  # This code runs on startup
  logger.info("----- Deye Graph server started -----")
  config.print_config(logger)
  logger.info("------------------------------")

  external_ip = CommonUtils.get_external_ip()
  actual_ip = external_ip if external_ip else config.SERVER_HOST

  logger.info(f"Listening on: {actual_ip}:{config.SERVER_PORT}")

  # The application runs here
  yield

  # This code runs on shutdown
  logger.info("Deye Graph server is shutting down...")

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
gzip.DEFAULT_EXCLUDED_CONTENT_TYPES = ("image/png", )

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
      "detail": f"deye-graph-server: {error_message}",
      "path": request.url.path,
    },
  )

graph_manager = DeyeGraphManager(
  config = config,
  logger = logger,
)

graph_manager.check_data_dir_exist()

@app.get("/ping", tags = ["Server Health Operations"])
def ping():
  """
  Health check endpoint that verifies the service is running
  """
  return {"status": "success"}

@app.get("/graphs", tags = ["Graphs Operations"])
def get_graphs():
  dates = graph_manager.get_available_dates()
  return {"dates": sorted([d.isoformat() for d in dates], reverse = True)}

@app.get("/graphs/{graph_date}", tags = ["Graphs Operations"])
async def get_graphs_by_date(graph_date: str):
  target_date = datetime.strptime(graph_date, "%Y-%m-%d").date()
  inverters = graph_manager.get_inverters_by_date(target_date)
  return asdict(inverters)

@app.get("/graphs/png/{graph_date}/{inverter}/{graph_name}", tags = ["Graphs Operations"])
async def get_graphs_png(graph_date: str, inverter: str, graph_name: str):
  target_date = datetime.strptime(graph_date, "%Y-%m-%d").date()

  loop = asyncio.get_running_loop()

  image_bytes = await loop.run_in_executor(
    None,
    graph_manager.generate_graph_png,
    target_date,
    inverter,
    graph_name,
  )

  return Response(
    content = image_bytes,
    media_type = "image/png",
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
