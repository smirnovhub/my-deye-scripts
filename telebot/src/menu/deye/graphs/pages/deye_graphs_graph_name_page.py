import telebot

from enum import Enum
from typing import List, Union

from button_node import ButtonNode
from deye_graph_data import DeyeGraphData
from break_button_node import BreakButtonNode
from deye_graphs_page import DeyeGraphsPage
from deye_graph_group_data import DeyeGraphGroupData
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from deye_graphs_data_provider import DeyeGraphsDataProvider
from telebot_progress_message import TelebotProgressMessage

class DeyeGraphsGraphNamePage(TelebotNavigationPage):
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
    return DeyeGraphsPage.graph_name

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Select graph:"

  def create_buttons(self) -> None:
    graphs: List[DeyeGraphData] = []
    groups: List[DeyeGraphGroupData] = []

    for inverter in self._provider.inverters:
      if inverter.inverter == self._provider.selected_inverter:
        groups = inverter.groups
        break

    for group in groups:
      if group.group == self._provider.selected_group:
        graphs = group.graphs
        break

    for index, graph in enumerate(graphs):
      if (index % 2) == 0:
        self.register_button(BreakButtonNode())

      title = graph.description.replace("Inverter ", "")

      self.register_button(
        ButtonNode(title),
        self._create_graph_handler(graph = graph),
      )

    self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Back"), self._handle_back)
    self.register_button(ButtonNode("Cancel"), self._handle_cancel)

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._title} cancel"

  async def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(DeyeGraphsPage.group)

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_graph_handler(self, graph: DeyeGraphData):
    async def handler(navigator: TelebotPageNavigator) -> None:
      chat_id = navigator.chat_id
      bot = navigator.bot
      progress = TelebotProgressMessage(bot)

      if not chat_id:
        navigator.stop(f"{self._title} chat id is not set")
        return

      navigator.stop(f"{self._title} {graph.description}")

      progress.show(
        chat_id = chat_id,
        text = "Creating graph",
      )

      try:
        selected_date = self._provider.selected_date
        selected_inverter = self._provider.selected_inverter

        image_file = await self._provider.get_graph_image(
          graph_date = selected_date,
          inverter = selected_inverter,
          graph_name = graph.name,
        )

        progress.hide()

        # Send the file as a document
        bot.send_document(
          chat_id = chat_id,
          document = image_file,
        )
      except Exception as e:
        bot.send_message(
          chat_id = chat_id,
          text = str(e),
        )
      finally:
        progress.hide()

    return handler
