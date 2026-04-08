import telebot

from telebot_async_runner import TelebotAsyncRunner
from slave_info_registers import SlaveInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_slave_base import TelebotMenuSlaveTotalBase

class TelebotMenuSlaveInfo(TelebotMenuSlaveTotalBase):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
      registers_class = SlaveInfoRegisters,
      all_command = TelebotMenuItem.deye_all_info,
      master_command = TelebotMenuItem.deye_master_info,
      slave_command = TelebotMenuItem.deye_slave_info,
    )
