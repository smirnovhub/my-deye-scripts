from io import BytesIO

import telebot
import requests

from typing import List
from datetime import date
from urllib.parse import urljoin

from env_utils import EnvUtils
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from http_session_singleton import HttpSessionSingleton
from telebot_progress_message import TelebotProgressMessage

class TelebotMenuGraphs(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self._progress = TelebotProgressMessage(bot)
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
      self.bot.send_message(message.chat.id, str(e))
      return

    self._progress.show(message.chat.id, "Retrieving data")

    try:
      graph_png = self._get_graph_png(server_url)
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      self._progress.hide()

    # Use BytesIO to create a file-like object in memory
    file_data = BytesIO(graph_png)
    file_data.name = 'image.png'

    # Send the file as a document
    self.bot.send_document(message.chat.id, file_data)

    #self.bot.send_message(message.chat.id, f"dates = {graph_dates}")

  def _is_graph_server_available(self, server_url: str) -> bool:
    ping_endpoint = urljoin(server_url, "/ping")
    response = self._session.get(ping_endpoint, timeout = 3)
    response.raise_for_status()
    return response.status_code == requests.codes.ok

  def _get_graph_dates(self, server_url: str) -> List[date]:
    url = urljoin(server_url, '/graphs')
    response = self._session.get(url)

    if response.status_code != requests.codes.ok:
      raise RuntimeError(f"Graphs server {server_url} returned error {response.status_code}: {response.text}")

    # Check if the response body is valid JSON
    data = response.json()

    if not isinstance(data, dict):
      raise RuntimeError(f"Graphs server {server_url} returned wrong type for skip regulation date")

    if 'dates' not in data:
      raise RuntimeError("No field 'dates' in graphs server response")

    return [date.fromisoformat(d) for d in data['dates']]

  def _get_graph_png(self, server_url: str) -> bytes:
    url = urljoin(server_url, '/graphs/png/2026-03-27/combined/battery_power')
    response = self._session.get(url)

    if response.status_code != requests.codes.ok:
      raise RuntimeError(f"Graphs server {server_url} returned error {response.status_code}: {response.text}")

    # Check if the response body is valid JSON
    return response.content
