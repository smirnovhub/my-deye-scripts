import telebot

from telebot_deye_helper import *
from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from slave_info_registers import SlaveInfoRegisters
from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotMenuSlaveInfo(TelebotMenuItem):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func
    self.loggers = DeyeLoggers()

  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.deye_slave_info

  def get_commands(self):
    commands = []
    for logger in self.loggers.loggers:
      if logger.name != self.loggers.master.name:
        commands.append(telebot.types.BotCommand(command = f'{logger.name}_info', description = f'{logger.name.title()} info'))
    return commands

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]
    if not commands:
      return
  
    @self.bot.message_handler(commands = commands)
    def handle(message):
      if not self.is_authorized(message, self.command):
        return

      def creator(prefix):
        return SlaveInfoRegisters(prefix)

      slave_name = message.text.lstrip('/').replace('_info', '')

      logger = self.loggers.get_logger_by_name(slave_name)
      if logger is None:
        self.bot.send_message(message.chat.id, f'Logger with name {slave_name} not found')
        return

      try:
        holder = DeyeRegistersHolder(loggers = [logger], register_creator = creator, **holder_kwargs)
        holder.connect_and_read()
      except Exception as e:
        self.bot.send_message(message.chat.id, f'Error while creating DeyeRegistersHolder: {str(e)}')
        return
      finally:
        holder.disconnect()

      info = get_register_values(holder.all_registers[slave_name].all_registers)
      self.bot.send_message(message.chat.id, f'<b>Inverter: {slave_name}</b>\n{info}', parse_mode='HTML')
