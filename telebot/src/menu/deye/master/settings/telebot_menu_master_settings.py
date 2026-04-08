import telebot

from telebot_menu_item import TelebotMenuItem
from telebot_async_runner import TelebotAsyncRunner
from master_settings_registers import MasterSettingsRegisters
from telebot_menu_base_settings import TelebotMenuBaseSettings

class TelebotMenuMasterSettings(TelebotMenuBaseSettings):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
      registers_class = MasterSettingsRegisters,
      main_command = TelebotMenuItem.deye_master_settings,
      all_command = TelebotMenuItem.deye_all_settings,
      master_command = TelebotMenuItem.deye_master_settings,
    )
