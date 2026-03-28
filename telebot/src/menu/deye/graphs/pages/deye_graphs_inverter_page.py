from enum import Enum
from typing import List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from pages.deye_graphs_page import DeyeGraphsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from deye_graphs_data_provider import DeyeGraphsDataProvider

class DeyeGraphsInverterPage(TelebotNavigationPage):
  def __init__(
    self,
    provider: DeyeGraphsDataProvider,
    title: str,
  ):
    super().__init__()
    self._provider = provider
    self._title = title

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
          self._create_navigation_handler(
            target_page = DeyeGraphsPage.graph_name,
            inverter = inverter.inverter,
          ),
        ))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Raw data"), self._handle_raw_data))
    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))
    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def get_goodbye_message(self) -> str:
    return f"{self._title} cancel"

  def _handle_raw_data(self, navigator: TelebotPageNavigator) -> None:
    chat_id = navigator.chat_id
    bot = navigator.bot

    if not chat_id:
      navigator.stop(f"{self._title} chat id is not set")
      return

    navigator.stop(f"{self._title} raw data")

    try:
      selected_date = self._provider.selected_date
      raw_file = self._provider.get_graph_raw_data(graph_date = selected_date)

      # Send the file as a document
      bot.send_document(chat_id = chat_id, document = raw_file)
    except Exception as e:
      bot.send_message(chat_id = chat_id, text = str(e))

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(DeyeGraphsPage.main)

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, target_page: Enum, inverter: str):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_inverter(inverter)
      navigator.navigate(target_page)

    return handler
