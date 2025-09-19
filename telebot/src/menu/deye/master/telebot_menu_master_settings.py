import telebot

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from master_settings_registers import MasterSettingsRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

from telebot_deye_helper import (
  holder_kwargs,
  get_register_values,
)

class TelebotMenuMasterSettings(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_master_settings

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message.from_user.id, message.chat.id):
      return

    def creator(prefix):
      return MasterSettingsRegisters(prefix)

    try:
      loggers = DeyeLoggers()
      holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
      holder.connect_and_read()
    except Exception as e:
      self.bot.send_message(message.chat.id, f'Error while reading registers: {str(e)}')
      return
    finally:
      holder.disconnect()

    info = get_register_values(holder.master_registers.all_registers)
    self.bot.send_message(message.chat.id, f'<b>Master inverter settings:</b>\n{info}', parse_mode = 'HTML')
