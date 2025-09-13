import telebot

from telebot_deye_helper import *
from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from accumulated_info_registers import AccumulatedInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuAllInfo(TelebotMenuItemHandler):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func
    self.loggers = DeyeLoggers()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_all_info

  def get_commands(self) -> List[telebot.types.BotCommand]:
    if self.loggers.count > 1:
      return [
        telebot.types.BotCommand(command = self.command.command, description = self.command.description),
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
        return AccumulatedInfoRegisters(prefix)

      try:
        holder = DeyeRegistersHolder(loggers = self.loggers.loggers, register_creator = creator, **holder_kwargs)
        holder.connect_and_read()
      except Exception as e:
        self.bot.send_message(message.chat.id, f'Error while creating DeyeRegistersHolder: {str(e)}')
        return
      finally:
        holder.disconnect()

      info = get_register_values(holder.accumulated_registers.all_registers)
      self.bot.send_message(message.chat.id, f'<b>Inverter: all</b>\n{info}', parse_mode='HTML')
