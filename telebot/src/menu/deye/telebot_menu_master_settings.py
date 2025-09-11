import telebot

from telebot_deye_helper import *
from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from master_settings_registers import MasterSettingsRegisters
from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotMenuMasterSettings(TelebotMenuItem):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func

  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.deye_master_settings

  def get_commands(self):
    return [
      telebot.types.BotCommand(command = 'master_settings', description = 'Master settings'),
    ]

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]
    @self.bot.message_handler(commands = commands)
    def handle(message):
      if not self.is_authorized(message, self.command):
        return

      def creator(prefix):
        return MasterSettingsRegisters(prefix)

      try:
        loggers = DeyeLoggers()
        holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
        holder.connect_and_read()
      except Exception as e:
        self.bot.send_message(message.chat.id, f'Error while creating DeyeRegistersHolder: {str(e)}')
        return
      finally:
        holder.disconnect()

      info = get_register_values(holder.master_registers.all_registers)
      self.bot.send_message(message.chat.id, f'<b>Master inverter settings:</b>\n{info}', parse_mode='HTML')
