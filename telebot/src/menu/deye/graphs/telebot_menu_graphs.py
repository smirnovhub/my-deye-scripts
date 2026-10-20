import telebot

from telebot.async_telebot import AsyncTeleBot

from env_utils import EnvUtils
from telebot_menu_item import TelebotMenuItem
from telebot_page_navigator import TelebotPageNavigator
from deye_graphs_data_provider import DeyeGraphsDataProvider
from deye_graphs_main_page import DeyeGraphsMainPage
from deye_graphs_graph_name_page import DeyeGraphsGraphNamePage
from deye_graphs_inverter_page import DeyeGraphsInverterPage
from deye_graphs_group_page import DeyeGraphsGroupPage
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuGraphs(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(bot = bot, )
    self._provider = DeyeGraphsDataProvider()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_graphs

  async def process_message(self, message: telebot.types.Message) -> None:
    server_url = EnvUtils.get_remote_graph_server_url()
    if not server_url:
      await self.bot.send_message(
        message.chat.id,
        f"Environment variable '{EnvUtils.REMOTE_GRAPH_SERVER_URL}' is empty",
      )
      return

    try:
      await self._provider.check_graph_server_available()
    except Exception as e:
      await self.bot.send_message(
        message.chat.id,
        f"Graph server {server_url} seems to be down: {e}",
      )
      return

    try:
      graph_dates = await self._provider.load_graph_dates()
    except Exception as e:
      await self.bot.send_message(
        message.chat.id,
        str(e),
      )
      return

    if not graph_dates:
      await self.bot.send_message(
        message.chat.id,
        "Graph list is empty",
      )
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
      DeyeGraphsGroupPage(
        provider = self._provider,
        title = title,
      ),
      DeyeGraphsGraphNamePage(
        provider = self._provider,
        title = title,
      ),
    ])

    await navigator.start(
      page = main_page,
      chat_id = message.chat.id,
    )
