import telebot

from master_info_registers import MasterInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_master_base import TelebotMenuMasterBase

class TelebotMenuMasterInfo(TelebotMenuMasterBase):
  def __init__(self, bot: telebot.TeleBot, is_authorized_func):
    super().__init__(
      bot = bot,
      registers = MasterInfoRegisters(),
      all_command = TelebotMenuItem.deye_all_info,
      master_command = TelebotMenuItem.deye_master_info,
      slave_command = TelebotMenuItem.deye_slave_info,
      is_authorized_func = is_authorized_func,
    )
