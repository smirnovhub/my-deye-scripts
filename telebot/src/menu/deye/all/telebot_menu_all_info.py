import telebot

from telebot_async_runner import TelebotAsyncRunner
from telebot_menu_item import TelebotMenuItem
from telebot_menu_all_base import TelebotMenuAllBase
from accumulated_info_registers import AccumulatedInfoRegisters

class TelebotMenuAllInfo(TelebotMenuAllBase):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
      registers_class = AccumulatedInfoRegisters,
      all_command = TelebotMenuItem.deye_all_info,
      master_command = TelebotMenuItem.deye_master_info,
      slave_command = TelebotMenuItem.deye_slave_info,
    )
