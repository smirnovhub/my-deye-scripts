import telebot

from telebot_constants import TelebotConstants
from telebot_menu_item import TelebotMenuItem
from total_stat_registers import TotalStatRegisters
from telebot_menu_all_base import TelebotMenuAllBase

class TelebotMenuAllTotalStat(TelebotMenuAllBase):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(
      bot = bot,
      registers = TotalStatRegisters(),
      all_command = TelebotMenuItem.deye_all_total_stat,
      master_command = TelebotMenuItem.deye_master_total_stat,
      slave_command = TelebotMenuItem.deye_slave_total_stat,
      title = TelebotConstants.total_stat_title,
    )
