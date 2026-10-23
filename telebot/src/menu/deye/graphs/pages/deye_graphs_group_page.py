import telebot

from enum import Enum
from typing import List, Union

from telebot_buttons import *
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
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Select group:"

  def create_buttons(self) -> None:
    groups: List[DeyeGraphGroupData] = []

    for inverter in self._provider.inverters:
      if inverter.inverter == self._provider.selected_inverter:
        groups = inverter.groups
        break

    for index, group in enumerate(groups):
      if (index % 2) == 0:
        self.register_button(BreakButtonNode())

      self.register_button(
        ButtonNode(group.group),
        self._create_navigation_handler(group = group.group),
      )

    self.register_button(BreakButtonNode())
    self.register_button(BackButtonNode(), self._handle_back)
    self.register_button(CancelButtonNode(), self._handle_cancel)

  async def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(DeyeGraphsPage.inverter)

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, group: str):
    async def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_group(group)
      await navigator.navigate(DeyeGraphsPage.graph_name)

    return handler
