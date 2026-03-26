import telebot
import requests

from typing import List
from datetime import date
from urllib.parse import urljoin

from env_utils import EnvUtils
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from http_session_singleton import HttpSessionSingleton

class TelebotMenuGraphs(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self._session = HttpSessionSingleton().session

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_graphs

  def process_message(self, message: telebot.types.Message) -> None:
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    server_url = EnvUtils.get_remote_graph_server_url()
    if not server_url:
      self.bot.send_message(
        message.chat.id,
        f"Environment variable '{EnvUtils.REMOTE_GRAPH_SERVER_URL}' is empty",
      )
      return

    try:
      is_available = self._is_graph_server_available(server_url)
    except Exception:
      is_available = False

    if not is_available:
      self.bot.send_message(message.chat.id, f"Graph server {server_url} seems to be down")
      return

    try:
      graph_dates = self._get_graph_dates(server_url)
    except Exception as e:
      self.bot.send_message(str(e))
      return

    self.bot.send_message(f"dates = {graph_dates}")

  def _is_graph_server_available(self, server_url: str) -> bool:
    ping_endpoint = urljoin(server_url, "/ping")
    response = self._session.get(ping_endpoint, timeout = 3)
    response.raise_for_status()
    return response.status_code == requests.codes.ok

  def _get_graph_dates(self, server_url: str) -> List[date]:
    url = urljoin(server_url, '/graphs')
    response = self._session.get(url)

    if response.status_code != requests.codes.ok:
      raise RuntimeError(f"Graphs server returned error {response.status_code}: {response.text}")

    # Check if the response body is valid JSON
    data = response.json()

    if not isinstance(data, dict):
      raise RuntimeError("Graphs server returned wrong type for skip regulation date")

    if 'dates' not in data:
      raise RuntimeError("No field 'dates' in graphs server response")

    return [date.fromisoformat(d) for d in data['dates']]
