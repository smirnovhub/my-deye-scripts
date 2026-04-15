from enum import Enum
from typing import List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from deye_graphs_page import DeyeGraphsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from deye_graphs_data_provider import DeyeGraphsDataProvider
from deye_graph_group_data import DeyeGraphGroupData

class DeyeGraphsGroupPage(TelebotNavigationPage):
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
    return DeyeGraphsPage.group

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode("Select group:"),
      BreakButtonNode(),
    ]

    groups: List[DeyeGraphGroupData] = []

    for inverter in self._provider.inverters:
      if inverter.inverter == self._provider.selected_inverter:
        groups = inverter.groups
        break

    for index, group in enumerate(groups):
      if (index % 2) == 0:
        buttons.append(BreakButtonNode())

      buttons.append(
        self.register_button_handler(
          ButtonNode(group.group),
          self._create_navigation_handler(group = group.group),
        ))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))
    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(DeyeGraphsPage.inverter)

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, group: str):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_group(group)
      navigator.navigate(DeyeGraphsPage.graph_name)

    return handler
