import telebot

from datetime import date

from telebot_async_runner import TelebotAsyncRunner
from telebot_menu_item import TelebotMenuItem
from statistics_helper import StatisticsHelper
from statistics_period import StatisticsPeriod
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuPvStat(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(bot = bot, runner = runner)
    self._statistics_helper = StatisticsHelper(self.logger)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_pv_stat

  async def process_message(self, message: telebot.types.Message) -> None:
    today = date.today()

    try:
      day_stat = await self._statistics_helper.get_statistics_for_telegram(today, StatisticsPeriod.Day)
      month_stat = await self._statistics_helper.get_statistics_for_telegram(today, StatisticsPeriod.Month)
      year_stat = await self._statistics_helper.get_statistics_for_telegram(today, StatisticsPeriod.Year)
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    self.bot.send_message(
      message.chat.id,
      f"{day_stat}{month_stat}{year_stat}",
      parse_mode = 'HTML',
    )
