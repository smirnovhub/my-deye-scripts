import telebot

from datetime import timedelta
from telebot.async_telebot import AsyncTeleBot

from telebot_page_navigator import TelebotPageNavigator
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync
from telebot_menu_pv_stat_main_page import TelebotMenuPvStatMainPage

class TelebotMenuPvStat(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_pv_stat

  async def process_message(self, message: telebot.types.Message) -> None:
    navigator = TelebotPageNavigator(
      self.bot,
      auto_update_period = timedelta(seconds = 59),
    )

    main_page = TelebotMenuPvStatMainPage()

    navigator.register_page(main_page)

    await navigator.start(
      page = main_page,
      chat_id = message.chat.id,
    )
