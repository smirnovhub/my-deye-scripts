import telebot

from telebot_constants import *
from telebot_deye_helper import *

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from slave_info_registers import SlaveInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuSlaveInfo(TelebotMenuItemHandler):
  def __init__(self, bot, is_authorized_func):
    self.bot: telebot.TeleBot = bot
    self.is_authorized = is_authorized_func
    self.loggers = DeyeLoggers()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_slave_info

  def get_commands(self) -> List[telebot.types.BotCommand]:
    commands = []
    for logger in self.loggers.loggers:
      if logger.name != self.loggers.master.name:
        commands.append(
          telebot.types.BotCommand(command = self.command.command.format(logger.name),
                                   description = self.command.description.format(logger.name.title())))
    return commands

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]
    if not commands:
      return

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      if not self.is_authorized(message, self.command):
        return

      registers = SlaveInfoRegisters()

      def creator(prefix):
        return registers

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

      keyboard = None
      if abs(registers.inverter_system_time_diff_register.value) > inverter_system_time_need_sync_difference_sec:
        keyboard = get_keyboard_for_register(registers, registers.inverter_system_time_register)

      info = get_register_values(holder.all_registers[slave_name].all_registers)
      sent = self.bot.send_message(message.chat.id,
                                   f'<b>Inverter: {slave_name}</b>\n{info}',
                                   reply_markup = keyboard,
                                   parse_mode = 'HTML')
      self.bot.clear_step_handler_by_chat_id(message.chat.id)
      self.bot.register_next_step_handler(message, self.next_step_handler, sent.message_id)

  def next_step_handler(self, message: telebot.types.Message, message_id: int):
    try:
      # remove yes/no buttons from previous message
      self.bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = message_id, reply_markup = None)
    except Exception:
      # Ignore exceptions (e.g., "message is not modified")
      pass

    # if we received new command, process it
    if message.text.startswith('/'):
      self.bot.process_new_messages([message])
      return
