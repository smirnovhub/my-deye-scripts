import asyncio
from typing import List
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

    # Fetch all statistics concurrently, safely capturing exceptions
    results = await asyncio.gather(
      *(self._statistics_helper.get_statistics_for_telegram(today, period) for period in StatisticsPeriod),
      return_exceptions = True,
    )

    stats: List[str] = []
    exceptions: List[str] = []

    for res in results:
      if isinstance(res, Exception):
        exceptions.append(str(res))
      else:
        stats.append(str(res))

    # Combine stats and exceptions into a single message text
    all_stat = "".join(stats)
    if exceptions:
      all_stat += "\n" + "\n".join(exceptions)

    cleaned_stat = all_stat.strip()
    if cleaned_stat:
      self.bot.send_message(
        message.chat.id,
        cleaned_stat,
        parse_mode = 'HTML',
      )
