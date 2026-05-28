import os
import glob
import asyncio
import aiofiles
import logging

from pathlib import Path
from http import HTTPStatus
from typing import List, Optional
from urllib.parse import urljoin
from datetime import datetime, timedelta, date

from env_utils import EnvUtils
from deye_graph_inverters import DeyeGraphInverters
from deye_graph_inverter_data import DeyeGraphInverterData
from src.graph_generator_config import GraphGeneratorConfig
from http_session_singleton_async import HttpSessionSingletonAsync

class GraphGenerator:
  def __init__(
    self,
    config: GraphGeneratorConfig,
    logger: logging.Logger,
  ):
    self._logger = logger
    self._period = config.PERIOD
    self._format = config.DEYE_GRAPHS_FORMAT
    self._server_url = config.REMOTE_GRAPH_SERVER_URL
    self._data_dir = f"data/{config.DEYE_GRAPHS_DIR}"

    data_dir = Path(self._data_dir)
    data_dir.mkdir(parents = True, exist_ok = True)

  async def main_logic(self) -> None:
    if not await self._is_graph_server_available():
      raise RuntimeError(f"Deye graph server {self._server_url} seems to be down")

    now = datetime.now()

    # Generate graphs for previous day at the start of the day
    if now.hour == 0 and now.minute < self._period:
      graph_date = now.date() - timedelta(days = 1)
      self._logger.warning(f"Generating graphs for previous day {graph_date.isoformat()}...")
    else:
      if now.hour == 0 and now.minute < self._period * 2:
        self._logger.info("Removing old graphs...")
        self._remove_old_files()

      graph_date = now.date()
      self._logger.info(f"Generating graphs for today {graph_date.isoformat()}...")

    inverters = await self._load_graph_inverters(graph_date)

    combined: Optional[DeyeGraphInverterData] = None
    master: Optional[DeyeGraphInverterData] = None

    for inverter in inverters.inverters:
      if inverter.inverter == "combined":
        combined = inverter
      elif inverter.inverter == "master":
        master = inverter

    if not master:
      raise RuntimeError("Master graphs not found")

    generated_list: List[str] = []

    loop = asyncio.get_running_loop()
    start_time = loop.time()

    if combined:
      generated_list = await self._generate_graph_for_inverter(
        inverter = combined,
        graph_date = graph_date,
        exclude_list = [],
      )

    await self._generate_graph_for_inverter(
      inverter = master,
      graph_date = graph_date,
      exclude_list = generated_list,
    )

    duration = loop.time() - start_time
    self._logger.info(f"All graphs generated in {duration:.3f}s")

  async def _generate_graph_for_inverter(
    self,
    inverter: DeyeGraphInverterData,
    graph_date: date,
    exclude_list: List[str],
  ) -> List[str]:
    generated_list: List[str] = []

    loop = asyncio.get_running_loop()
    self._logger.info(f"Generating graphs for {inverter.inverter} inverter...")

    for group in inverter.groups:
      for graph in group.graphs:
        if graph.name in exclude_list:
          continue

        self._logger.info(f"Generating graph for {graph.name}...")

        start_time = loop.time()

        try:
          image = await self._get_graph_image(
            graph_date = graph_date,
            inverter = inverter.inverter,
            graph_name = graph.name,
          )
        except Exception as e:
          self._logger.info(f"Can't generate {self._format} graph for {graph.name}: {e}")
          continue

        filename = os.path.join(self._data_dir, f"{graph.name}.{self._format}")
        async with aiofiles.open(filename, mode = "wb") as f:
          await f.write(image)

        generated_list.append(graph.name)

        duration = loop.time() - start_time
        self._logger.info(f"Graph {self._format} for {graph.name} generated in {duration:.3f}s")

    return generated_list

  async def _is_graph_server_available(self) -> bool:
    url = urljoin(self._server_url, "/ping")
    session = await HttpSessionSingletonAsync.get_session()
    try:
      async with session.get(url) as response:
        response.raise_for_status()
        return response.status == HTTPStatus.OK
    except Exception:
      return False

  async def _load_graph_inverters(
    self,
    graph_date: date,
  ) -> DeyeGraphInverters:
    url = urljoin(self._server_url, f"/graphs/{graph_date.isoformat()}")
    session = await HttpSessionSingletonAsync.get_session()
    async with session.get(url) as response:
      text = await response.text()
      if response.status != HTTPStatus.OK:
        raise RuntimeError(f"Can't get today graphs: response code = {response.status}, text = {text}")

      return DeyeGraphInverters.from_json(text)

  async def _get_graph_image(
    self,
    graph_date: date,
    inverter: str,
    graph_name: str,
  ) -> bytes:
    url = urljoin(self._server_url, f"/graphs/{self._format}/{graph_date.isoformat()}/{inverter}/{graph_name}")
    session = await HttpSessionSingletonAsync.get_session()
    async with session.get(url) as response:
      if response.status != HTTPStatus.OK:
        text = await response.text()
        raise RuntimeError(f"Can't get graph {self._format}: response code = {response.status}, text = {text}")
      return await response.read()

  def _remove_old_files(self) -> None:
    for ext in EnvUtils.DEYE_GRAPHS_FORMATS:
      self._delete_files_by_extension(self._data_dir, ext)

  def _delete_files_by_extension(self, folder_path: str, extension: str) -> None:
    # Ensure the extension starts with a dot
    if not extension.startswith('.'):
      extension = f'.{extension}'

    # Check if the folder exists before proceeding
    if not os.path.exists(folder_path):
      self._logger.error(f"Error: the folder '{folder_path}' does not exist")
      return

    # Create a pattern to match all files with the given extension
    search_pattern = os.path.join(folder_path, f"*{extension}")

    # Find all matching files
    files_to_delete = glob.glob(search_pattern)

    if not files_to_delete:
      self._logger.warning(f"No files with extension '{extension}' found in '{folder_path}'")
      return

    # Loop through the found files and delete them
    for file_path in files_to_delete:
      try:
        os.remove(file_path)
        self._logger.info(f"Deleted: {file_path}")
      except Exception as e:
        self._logger.error(f"Failed to delete {file_path}. Reason: {e}")
