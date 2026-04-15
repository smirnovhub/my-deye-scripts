import os

from enum import Enum
from typing import List, Optional

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

  @property
  def page_type(self) -> Enum:
    return DeyeGraphsPage.inverter

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode("Select inverter:"),
      BreakButtonNode(),
    ]

    for index, inverter in enumerate(self._provider.inverters):
      if (index % 2) == 0:
        buttons.append(BreakButtonNode())

      buttons.append(
        self.register_button_handler(
          ButtonNode(inverter.inverter.title()),
          self._create_navigation_handler(inverter = inverter.inverter),
        ))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Full report"), self._handle_full_report))
    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Raw data"), self._handle_raw_data))
    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))
    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def get_goodbye_message(self) -> str:
    return f"{self._title} cancel"

  def _handle_full_report(self, navigator: TelebotPageNavigator) -> None:
    bot = navigator.bot
    chat_id = navigator.chat_id

    if not chat_id:
      navigator.stop(f"{self._title} chat id is not set")
      return

    if not self._acquire_lock():
      navigator.stop(f"{self._title} already working")
      return

    try:
      progress = TelebotProgressMessage(bot)
      progress.show(chat_id, "Generating full report")

      navigator.stop(f"{self._title} full report")

      selected_date = self._provider.selected_date
      data_file = self._provider.get_graph_data(
        graph_date = selected_date,
        format = "pdf",
      )

      # Send the file as a document
      bot.send_document(chat_id = chat_id, document = data_file)
    except Exception as e:
      bot.send_message(chat_id = chat_id, text = str(e))
    finally:
      self._release_lock()
      progress.hide()

  def _handle_raw_data(self, navigator: TelebotPageNavigator) -> None:
    chat_id = navigator.chat_id
    bot = navigator.bot

    if not chat_id:
      navigator.stop(f"{self._title} chat id is not set")
      return

    if not self._acquire_lock():
      navigator.stop(f"{self._title} already working")
      return

    navigator.stop(f"{self._title} raw data")

    try:
      selected_date = self._provider.selected_date
      data_file = self._provider.get_graph_data(
        graph_date = selected_date,
        format = "csv",
      )

      # Send the file as a document
      bot.send_document(chat_id = chat_id, document = data_file)
    except Exception as e:
      bot.send_message(chat_id = chat_id, text = str(e))

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(DeyeGraphsPage.main)

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, inverter: str):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_inverter(inverter)
      navigator.navigate(DeyeGraphsPage.group)

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
