from enum import Enum
from io import BytesIO
from typing import List

from button_node import ButtonNode
from deye_graph_data import DeyeGraphData
from break_button_node import BreakButtonNode
from pages.deye_graphs_page import DeyeGraphsPage
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
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode("Select graph:"),
      BreakButtonNode(),
    ]

    graphs: List[DeyeGraphData] = []

    for inverter in self._provider.inverters:
      if inverter.inverter == self._provider.selected_inverter:
        graphs = inverter.graphs
        break

    for index, graph in enumerate(graphs):
      if (index % 2) == 0:
        buttons.append(BreakButtonNode())

      title = graph.description.replace("Inverter ", "")

      buttons.append(self.register_button_handler(
        ButtonNode(title),
        self._create_graph_handler(graph = graph),
      ))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))
    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def get_goodbye_message(self) -> str:
    return f"{self._title} cancel"

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(DeyeGraphsPage.inverter)

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_graph_handler(self, graph: DeyeGraphData):
    def handler(navigator: TelebotPageNavigator) -> None:
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

        png = self._provider.get_graph_png(
          graph_date = selected_date,
          graph_type = selected_inverter,
          graph_name = graph.name,
        )

        # Use BytesIO to create a file-like object in memory
        file_data = BytesIO(png)
        file_data.name = f"{selected_date}-{selected_inverter}-{graph.name}.png"

        # Send the file as a document
        bot.send_document(chat_id, file_data)
      finally:
        progress.hide()

    return handler
