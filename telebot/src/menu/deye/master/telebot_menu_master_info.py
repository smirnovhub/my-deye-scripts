import telebot

from master_info_registers import MasterInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_master_base import TelebotMenuMasterBase
from telebot_async_runner import TelebotAsyncRunner

class TelebotMenuMasterInfo(TelebotMenuMasterBase):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
      registers_class = MasterInfoRegisters,
      all_command = TelebotMenuItem.deye_all_info,
      master_command = TelebotMenuItem.deye_master_info,
      slave_command = TelebotMenuItem.deye_slave_info,
    )
