import telebot

from telebot_menu_item import TelebotMenuItem
from all_settings_registers import AllSettingsRegisters
from telebot_menu_base_settings import TelebotMenuBaseSettings

class TelebotMenuAllSettings(TelebotMenuBaseSettings):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(
      bot = bot,
      registers = AllSettingsRegisters(),
      main_command = TelebotMenuItem.deye_all_settings,
      all_command = TelebotMenuItem.deye_all_settings,
      master_command = TelebotMenuItem.deye_master_settings,
    )
