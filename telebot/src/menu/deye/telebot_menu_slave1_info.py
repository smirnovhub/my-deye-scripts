import telebot

from telebot_deye_helper import *
from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from slave1_info_registers import Slave1InfoRegisters
from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotMenuSlave1Info(TelebotMenuItem):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func
    self.loggers = DeyeLoggers()

  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.deye_slave1_info

  def get_commands(self):
    if self.loggers.slave1 is not None:
      return [
        telebot.types.BotCommand(command = 'slave1_info', description = 'Slave1 info'),
      ]
    return []

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]
    if not commands:
      return
  
    @self.bot.message_handler(commands = commands)
    def handle(message):
      if not self.is_authorized(message, self.command):
        return

      def creator(prefix):
        return Slave1InfoRegisters(prefix)

      try:
        holder = DeyeRegistersHolder(loggers = [self.loggers.slave1], register_creator = creator, **holder_kwargs)
        holder.connect_and_read()
      except Exception as e:
        self.bot.send_message(message.chat.id, f'Error while creating DeyeRegistersHolder: {str(e)}')
        return
      finally:
        holder.disconnect()

      info = get_register_values(holder.slave1_registers.all_registers)
      self.bot.send_message(message.chat.id, f'<b>Inverter: slave1</b>\n{info}', parse_mode='HTML')
