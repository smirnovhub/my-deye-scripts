from typing import List, Optional
from datetime import date
from urllib.parse import urljoin
from http import HTTPStatus

from env_utils import EnvUtils
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

  def set_selected_inverter(self, value: str) -> None:
    # Update the selected inverter value
    self._selected_inverter = value

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
    response = self._session.get(ping_endpoint, timeout = 3)
    response.raise_for_status()
    return response.status_code == HTTPStatus.OK

  def load_graph_dates(self) -> List[date]:
    url = urljoin(self._server_url, "/graphs")
    response = self._session.get(url, timeout = 5)

    if response.status_code != HTTPStatus.OK:
      raise RuntimeError(f"Graphs server {self._server_url} returned error {response.status_code}: {response.text}")

    # Check if the response body is valid JSON
    data = response.json()

    if not isinstance(data, dict):
      raise RuntimeError(f"Graphs server {self._server_url} returned wrong type for skip regulation date")

    if 'dates' not in data:
      raise RuntimeError("No field 'dates' in graphs server response")

    self._dates = sorted([date.fromisoformat(d) for d in data['dates']], reverse = True)
    return self._dates

  def load_graph_inverters(self, graph_date: date) -> List[DeyeGraphInverterData]:
    url = urljoin(self._server_url, f"/graphs/{graph_date.isoformat()}")
    response = self._session.get(url, timeout = 5)
    response.raise_for_status()

    self._inverters = DeyeGraphInverters.from_json(response.text).inverters
    return self._inverters

  def get_graph_png(
    self,
    graph_date: date,
    graph_type: str,
    graph_name: str,
  ) -> bytes:
    url = urljoin(self._server_url, f"/graphs/png/{graph_date.isoformat()}/{graph_type}/{graph_name}")
    response = self._session.get(url)

    if response.status_code != HTTPStatus.OK:
      raise RuntimeError(f"Graphs server {self._server_url} returned error {response.status_code}: {response.text}")

    # Check if the response body is valid JSON
    return response.content
