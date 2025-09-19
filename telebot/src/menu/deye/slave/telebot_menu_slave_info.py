import telebot

from slave_info_registers import SlaveInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_slave_base import TelebotMenuSlaveTotalBase

class TelebotMenuSlaveInfo(TelebotMenuSlaveTotalBase):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(
      bot = bot,
      registers = SlaveInfoRegisters(),
      all_command = TelebotMenuItem.deye_all_info,
      master_command = TelebotMenuItem.deye_master_info,
      slave_command = TelebotMenuItem.deye_slave_info,
    )
