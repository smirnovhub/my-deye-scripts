import telebot

from telebot_constants import *
from telebot_user_choices import *
from telebot_deye_helper import *

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from accumulated_info_registers import AccumulatedInfoRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuAllInfo(TelebotMenuItemHandler):
  def __init__(self, bot, is_authorized_func):
    self.bot: telebot.TeleBot = bot
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
    def handle(message: telebot.types.Message):
      if not self.is_authorized(message, self.command):
        return

      registers = AccumulatedInfoRegisters()

      def creator(prefix):
        return registers

      try:
        holder = DeyeRegistersHolder(loggers = self.loggers.loggers, register_creator = creator, **holder_kwargs)
        holder.connect_and_read()
      except Exception as e:
        self.bot.send_message(message.chat.id, f'Error while creating DeyeRegistersHolder: {str(e)}')
        return
      finally:
        holder.disconnect()

      keyboard = None
      if abs(registers.inverter_system_time_diff_register.value) > inverter_system_time_need_sync_difference_sec:
        keyboard = get_keyboard_for_register(registers, registers.inverter_system_time_register)
      #else:
        #keyboard = get_keyboard_for_choices({'Master info': '/master_info', 'Slave1 info': '/slave1_info'}, 3)

      info = get_register_values(holder.accumulated_registers.all_registers)
      sent = self.bot.send_message(message.chat.id,
                                   f'<b>Inverter: all</b>\n{info}',
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
