import telebot

from telebot_deye_helper import *
from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from master_info_registers import MasterInfoRegisters
from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotMenuMasterInfo(TelebotMenuItem):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func

  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.deye_master_info

  def get_commands(self):
    return [
      telebot.types.BotCommand(command = 'master_info', description = 'Master info')
    ]

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]
    @self.bot.message_handler(commands = commands)
    def handle(message):
      if not self.is_authorized(message, self.command):
        return

      def creator(prefix):
        return MasterInfoRegisters(prefix)

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
      self.bot.send_message(message.chat.id, f'<b>Inverter: master</b>\n{info}', parse_mode='HTML')
