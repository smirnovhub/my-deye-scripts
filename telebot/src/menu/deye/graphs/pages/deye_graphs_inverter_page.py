import os
import re
import telebot

from enum import Enum
from typing import Optional, Union

from telebot_utils import TelebotUtils
from button_node import ButtonNode
from break_button_node import BreakButtonNode
from deye_graphs_page import DeyeGraphsPage
from deye_file_lock import DeyeFileLock
from deye_file_locker import DeyeFileLocker
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from deye_graphs_data_provider import DeyeGraphsDataProvider
from telebot_progress_message import TelebotProgressMessage

class DeyeGraphsInverterPage(TelebotNavigationPage):
  def __init__(
    self,
    provider: DeyeGraphsDataProvider,
    title: str,
  ):
    super().__init__()
    self._provider = provider
    self._title = title
    lockfile = os.path.join(DeyeFileLock.lock_path, 'full_report.lock')
    self._locker = DeyeFileLocker('graphs', lockfile, verbose = True)
    self._progress: Optional[TelebotProgressMessage] = None

    self._allowed_inverters = [
      'master',
      r'slave\d+',
      'all',
      'combined',
    ]

  @property
  def page_type(self) -> Enum:
    return DeyeGraphsPage.inverter

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Select inverter:"

  def create_buttons(self) -> None:
    allowed_inverters = [inv for inv in self._provider.inverters if self._is_inverter_allowed(inv.inverter)]

    for index, inverter in enumerate(allowed_inverters):
      if index > 0 and (index % 2) == 0:
        self.register_button(BreakButtonNode())

      self.register_button(
        ButtonNode(inverter.inverter.title()),
        self._create_navigation_handler(inverter = inverter.inverter),
      )

    self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Full report"), self._handle_full_report)
    self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Raw data"), self._handle_raw_data)
    self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Back"), self._handle_back)
    self.register_button(ButtonNode("Cancel"), self._handle_cancel)

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._title} cancel"

  async def _handle_full_report(self, navigator: TelebotPageNavigator) -> None:
    bot = navigator.bot
    chat_id = navigator.chat_id

    if not chat_id:
      await navigator.stop(f"{self._title} chat id is not set")
      return

    if not self._acquire_lock():
      await navigator.stop(f"{self._title} already working")
      return

    try:
      progress = TelebotProgressMessage(bot)
      await progress.show(chat_id, "Generating full report")

      await navigator.stop(f"{self._title} full report")

      selected_date = self._provider.selected_date
      data_file = await self._provider.get_graph_data(
        graph_date = selected_date,
        format = "pdf",
      )

      # Send the file as a document
      await bot.send_document(
        chat_id = chat_id,
        document = data_file,
      )
    except Exception as e:
      self._logger.error(f"Error: {e}", exc_info = e)
      await bot.send_message(
        chat_id = chat_id,
        text = f"Error: {e}",
      )
    finally:
      self._release_lock()
      await progress.hide()

  async def _handle_raw_data(self, navigator: TelebotPageNavigator) -> None:
    chat_id = navigator.chat_id
    bot = navigator.bot

    if not chat_id:
      await navigator.stop(f"{self._title} chat id is not set")
      return

    await navigator.stop(f"{self._title} raw data")

    try:
      selected_date = self._provider.selected_date
      data_file = await self._provider.get_graph_data(
        graph_date = selected_date,
        format = "csv",
      )

      # Send the file as a document
      await bot.send_document(
        chat_id = chat_id,
        document = data_file,
      )
    except Exception as e:
      await bot.send_message(
        chat_id = chat_id,
        text = TelebotUtils.escape_html(str(e)),
      )

  async def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(DeyeGraphsPage.main)

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, inverter: str):
    async def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_inverter(inverter)
      await navigator.navigate(DeyeGraphsPage.group)

    return handler

  def _acquire_lock(self) -> bool:
    try:
      self._locker.acquire(timeout = 0.1)
      return True
    except Exception:
      return False

  def _release_lock(self) -> None:
    try:
      self._locker.release()
    except Exception:
      pass

  def _is_inverter_allowed(self, name: str) -> bool:
    for pattern in self._allowed_inverters:
      if re.fullmatch(pattern, name):
        return True
    return False
