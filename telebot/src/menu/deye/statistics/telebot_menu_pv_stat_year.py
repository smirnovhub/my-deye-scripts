import telebot

from telebot_async_runner import TelebotAsyncRunner
from telebot_menu_item import TelebotMenuItem
from statistics_period import StatisticsPeriod
from telebot_menu_pv_stat_base import TelebotMenuPvStatBase

class TelebotMenuPvStatYear(TelebotMenuPvStatBase):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
      stat_command = TelebotMenuItem.deye_pv_stat_year,
      stat_period = StatisticsPeriod.Year,
    )
