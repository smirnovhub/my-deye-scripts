import telebot

from telebot_menu_item import TelebotMenuItem
from total_stat_registers import TotalStatRegisters
from telebot_menu_all_base import TelebotMenuAllBase

class TelebotMenuAllTotalStat(TelebotMenuAllBase):
  def __init__(self, bot: telebot.TeleBot, is_authorized_func):
    super().__init__(
      bot = bot,
      registers = TotalStatRegisters(),
      all_command = TelebotMenuItem.deye_all_total_stat,
      master_command = TelebotMenuItem.deye_master_total_stat,
      slave_command = TelebotMenuItem.deye_slave_total_stat,
      is_authorized_func = is_authorized_func,
    )
