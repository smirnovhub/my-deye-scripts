import telebot

from telebot_menu_item import TelebotMenuItem
from telebot_menu_master_base import TelebotMenuMasterBase
from today_stat_registers import TodayStatRegisters

class TelebotMenuMasterTodayStat(TelebotMenuMasterBase):
  def __init__(self, bot: telebot.TeleBot, is_authorized_func):
    super().__init__(
      bot = bot,
      registers = TodayStatRegisters(),
      all_command = TelebotMenuItem.deye_all_today_stat,
      master_command = TelebotMenuItem.deye_master_today_stat,
      slave_command = TelebotMenuItem.deye_slave_today_stat,
      is_authorized_func = is_authorized_func,
    )
