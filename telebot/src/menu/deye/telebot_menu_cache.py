import telebot

from telebot_menu_item import TelebotMenuItem
from telebot_async_runner import TelebotAsyncRunner
from telebot_deye_helper import TelebotDeyeHelper
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync
from deye_registers_holder_async import DeyeRegistersHolderAsync

class TelebotMenuCache(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
    )

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.cache

  async def process_message(self, message: telebot.types.Message) -> None:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolderAsync(
      loggers = self.loggers.loggers,
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      rates = await holder.get_cache_hit_rates()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    result = ""
    for inverter, rate in rates.items():
      result += f"<b>Inverter: {inverter}</b>"
      result += "<pre>"
      result += f"Got from cache : {rate.got_from_cache_count}\n"
      result += f"Total count    : {rate.total_count}\n"
      result += f"Cache hit rate : {rate.cache_hit_rate_percent}%\n"
      result += "</pre>"

    self.bot.send_message(
      message.chat.id,
      result,
      parse_mode = 'HTML',
    )
