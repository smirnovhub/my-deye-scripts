import telebot

from env_utils import EnvUtils
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_sync_handler import TelebotMenuItemSyncHandler
from telebot_page_navigator import TelebotPageNavigator
from deye_graphs_data_provider import DeyeGraphsDataProvider
from deye_graphs_main_page import DeyeGraphsMainPage
from deye_graphs_graph_name_page import DeyeGraphsGraphNamePage
from deye_graphs_inverter_page import DeyeGraphsInverterPage

class TelebotMenuGraphs(TelebotMenuItemSyncHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self._provider = DeyeGraphsDataProvider()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_graphs

  def process_message(self, message: telebot.types.Message) -> None:
    server_url = EnvUtils.get_remote_graph_server_url()
    if not server_url:
      self.bot.send_message(
        message.chat.id,
        f"Environment variable '{EnvUtils.REMOTE_GRAPH_SERVER_URL}' is empty",
      )
      return

    try:
      is_available = self._provider.is_graph_server_available()
    except Exception:
      is_available = False

    if not is_available:
      self.bot.send_message(message.chat.id, f"Graph server {server_url} seems to be down")
      return

    try:
      graph_dates = self._provider.load_graph_dates()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    if not graph_dates:
      self.bot.send_message(message.chat.id, "Graph list is empty")
      return

    navigator = TelebotPageNavigator(self.bot)
    title = "Deye graphs:"
    main_page = DeyeGraphsMainPage(
      provider = self._provider,
      title = title,
    )

    navigator.register_pages([
      main_page,
      DeyeGraphsInverterPage(
        provider = self._provider,
        title = title,
      ),
      DeyeGraphsGraphNamePage(
        provider = self._provider,
        title = title,
      ),
    ])

    navigator.start(
      page = main_page,
      text = title,
      chat_id = message.chat.id,
    )
