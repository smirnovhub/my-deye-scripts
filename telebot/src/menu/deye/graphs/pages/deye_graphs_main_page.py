from datetime import date
from enum import Enum
from typing import List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from pages.deye_graphs_page import DeyeGraphsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from deye_graphs_data_provider import DeyeGraphsDataProvider

class DeyeGraphsMainPage(TelebotNavigationPage):
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
    return DeyeGraphsPage.main

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode("Select graph date:"),
      BreakButtonNode(),
    ]

    for index, graph_date in enumerate(self._provider.dates):
      if (index % 2) == 0:
        buttons.append(BreakButtonNode())

      btn = ButtonNode(graph_date.isoformat())
      buttons.append(
        self.register_button_handler(
          btn, self._create_navigation_handler(
            target_page = DeyeGraphsPage.inverter,
            graph_date = graph_date,
          )))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))
    self._buttons = buttons

  def get_goodbye_message(self) -> str:
    return f"{self._title} cancel"

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, target_page: Enum, graph_date: date):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_date(graph_date)
      self._provider.load_graph_inverters(graph_date)
      navigator.navigate(target_page)

    return handler
