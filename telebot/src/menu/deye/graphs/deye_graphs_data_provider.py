from typing import List, Optional
from datetime import date
from email.message import Message
from urllib.parse import urljoin, unquote
from http import HTTPStatus
from io import BytesIO

from env_utils import EnvUtils
from telebot_utils import TelebotUtils
from deye_graph_inverters import DeyeGraphInverters
from deye_graph_inverter_data import DeyeGraphInverterData
from http_session_singleton import HttpSessionSingleton

class DeyeGraphsDataProvider:
  def __init__(self):
    self._server_url = EnvUtils.get_remote_graph_server_url()
    self._session = HttpSessionSingleton().session
    self._dates: List[date] = []
    self._inverters: List[DeyeGraphInverterData] = []
    self._selected_date: Optional[date] = None
    self._selected_inverter: Optional[str] = None
    self._selected_group: Optional[str] = None
    self._selected_graph_name: Optional[str] = None

  @property
  def dates(self) -> List[date]:
    # Return the currently available dates
    return self._dates

  @property
  def inverters(self) -> List[DeyeGraphInverterData]:
    # Return the currently available inverters
    return self._inverters

  @property
  def selected_date(self) -> date:
    # Return the currently selected date
    if not self._selected_date:
      raise RuntimeError("Date is not selected")
    return self._selected_date

  def set_selected_date(self, value: date) -> None:
    # Update the selected date value
    self._selected_date = value

  @property
  def selected_inverter(self) -> str:
    # Return the currently selected inverter name
    if not self._selected_inverter:
      raise RuntimeError("Inverter is not selected")
    return self._selected_inverter

  @property
  def selected_group(self) -> str:
    # Return the currently selected group name
    if not self._selected_group:
      raise RuntimeError("Group is not selected")
    return self._selected_group

  def set_selected_inverter(self, value: str) -> None:
    # Update the selected inverter value
    self._selected_inverter = value

  def set_selected_group(self, value: str) -> None:
    # Update the selected group value
    self._selected_group = value

  @property
  def selected_graph_name(self) -> str:
    # Return the name of the selected graph
    if not self._selected_graph_name:
      raise RuntimeError("Graph name is not selected")
    return self._selected_graph_name

  def set_selected_graph_name(self, value: str) -> None:
    # Update the selected graph name value
    self._selected_graph_name = value

  def is_graph_server_available(self) -> bool:
    ping_endpoint = urljoin(self._server_url, "/ping")
    with self._session.get(ping_endpoint, timeout = 3) as response:
      response.raise_for_status()
      return response.status_code == HTTPStatus.OK

  def load_graph_dates(self) -> List[date]:
    url = urljoin(self._server_url, "/graphs")
    with self._session.get(url, timeout = 5) as response:
      if response.status_code != HTTPStatus.OK:
        raise RuntimeError(TelebotUtils.get_response_message(response.text))

      # Check if the response body is valid JSON
      data = response.json()

    if not isinstance(data, dict):
      raise RuntimeError(f"Graphs server {self._server_url} returned wrong json type")

    if 'dates' not in data:
      raise RuntimeError("No field 'dates' in graphs server response")

    self._dates = sorted([date.fromisoformat(d) for d in data['dates']], reverse = True)
    return self._dates

  def load_graph_inverters(self, graph_date: date) -> List[DeyeGraphInverterData]:
    url = urljoin(self._server_url, f"/graphs/{graph_date.isoformat()}")
    with self._session.get(url, timeout = 5) as response:
      if response.status_code != HTTPStatus.OK:
        raise RuntimeError(TelebotUtils.get_response_message(response.text))

      self._inverters = DeyeGraphInverters.from_json(response.text).inverters
      return self._inverters

  def get_graph_image(
    self,
    graph_date: date,
    inverter: str,
    graph_name: str,
  ) -> BytesIO:
    format = EnvUtils.get_deye_graphs_format()
    url = urljoin(self._server_url, f"/graphs/{format}/{graph_date.isoformat()}/{inverter}/{graph_name}")
    with self._session.get(url) as response:
      if response.status_code != HTTPStatus.OK:
        raise RuntimeError(TelebotUtils.get_response_message(response.text))

      file = BytesIO(response.content)

    file.name = f"deye-{graph_date}-{inverter}-{graph_name}.{format}"
    return file

  def get_graph_data(
    self,
    graph_date: date,
    format: str,
  ) -> BytesIO:
    url = urljoin(self._server_url, f"/graphs/{format}/{graph_date.isoformat()}")
    with self._session.get(url) as response:
      if response.status_code != HTTPStatus.OK:
        raise RuntimeError(TelebotUtils.get_response_message(response.text))

      content = response.content
      content_disposition = response.headers.get("Content-Disposition", "")

    filename = f"deye.{format}"

    if content_disposition:
      msg = Message()
      msg["Content-Disposition"] = content_disposition

      # RFC 6266: filename* has a high priprity
      filename_ext = msg.get_param("filename*", header = "Content-Disposition")

      if filename_ext:
        if isinstance(filename_ext, tuple):
          charset, _, value = filename_ext
          filename = unquote(value, encoding = charset or "utf-8", errors = "replace")
        else:
          filename = unquote(filename_ext)
      else:
        filename_simple = msg.get_param("filename", header = "Content-Disposition")
        if filename_simple:
          if isinstance(filename_simple, str):
            filename = filename_simple

    file = BytesIO(content)
    file.name = filename

    return file
