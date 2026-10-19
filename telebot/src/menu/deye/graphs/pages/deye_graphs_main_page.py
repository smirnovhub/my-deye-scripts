import telebot

from enum import Enum
from typing import Union
from datetime import date, timedelta

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from deye_graphs_page import DeyeGraphsPage
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
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Select graph date:"

  def create_buttons(self) -> None:
    today = date.today()
    yesterday = today - timedelta(days = 1)

    if today in self._provider.dates:
      self.register_button(
        ButtonNode("Today"),
        self._create_navigation_handler(
          target_page = DeyeGraphsPage.inverter,
          graph_date = today,
        ),
      )

    if yesterday in self._provider.dates:
      self.register_button(
        ButtonNode("Yesterday"),
        self._create_navigation_handler(
          target_page = DeyeGraphsPage.inverter,
          graph_date = yesterday,
        ),
      )

    if today in self._provider.dates or yesterday in self._provider.dates:
      self.register_button(BreakButtonNode())

    # for index, graph_date in enumerate(self._provider.dates):
    #   if (index % 2) == 0:
    #     self.register_button(BreakButtonNode())

    #   self.register_button(
    #     self.register_button_handler(
    #       ButtonNode(graph_date.isoformat()),
    #       self._create_navigation_handler(
    #         target_page = DeyeGraphsPage.inverter,
    #         graph_date = graph_date,
    #       ),
    #     ))

    # self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Cancel"), self._handle_cancel)

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._title} cancel"

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, target_page: Enum, graph_date: date):
    async def handler(navigator: TelebotPageNavigator) -> None:
      self._provider.set_selected_date(graph_date)
      await self._provider.load_graph_inverters(graph_date)
      await navigator.navigate(target_page)

    return handler
