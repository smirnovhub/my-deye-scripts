import telebot

from telebot_menu_item import TelebotMenuItem
from master_settings_registers import MasterSettingsRegisters
from telebot_menu_base_settings import TelebotMenuBaseSettings

class TelebotMenuMasterSettings(TelebotMenuBaseSettings):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(
      bot = bot,
      registers = MasterSettingsRegisters(),
      main_command = TelebotMenuItem.deye_master_settings,
      all_command = TelebotMenuItem.deye_all_settings,
      master_command = TelebotMenuItem.deye_master_settings,
    )
