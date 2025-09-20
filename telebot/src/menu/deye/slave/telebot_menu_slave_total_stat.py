import telebot

from telebot_menu_item import TelebotMenuItem
from telebot_menu_slave_base import TelebotMenuSlaveTotalBase
from total_stat_registers import TotalStatRegisters

class TelebotMenuSlaveTotalStat(TelebotMenuSlaveTotalBase):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(
      bot = bot,
      registers = TotalStatRegisters(),
      all_command = TelebotMenuItem.deye_all_total_stat,
      master_command = TelebotMenuItem.deye_master_total_stat,
      slave_command = TelebotMenuItem.deye_slave_total_stat,
    )
