import telebot

from datetime import datetime

from telebot_constants import *
from telebot_deye_helper import *
from telebot_user_choices import *

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from custom_registers import CustomRegisters
from telebot_menu_item import TelebotMenuItem
from deye_registers_factory import DeyeRegistersFactory
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuSyncTime(TelebotMenuItemHandler):
  def __init__(self, bot, is_authorized_func, is_writable_register_allowed_func):
    self.bot: telebot.TeleBot = bot
    self.is_authorized = is_authorized_func
    self.is_writable_register_allowed = is_writable_register_allowed_func
    self.registers = DeyeRegistersFactory.create_registers()
    self.time_does_not_need_sync_threshold_sec = 15

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_sync_time

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return [
      telebot.types.BotCommand(command = self.command.command, description = self.command.description),
    ]

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]
    if not commands:
      return

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      if not self.is_authorized(message, self.command):
        return

      register = self.registers.inverter_system_time_register

      if not self.is_writable_register_allowed(message.from_user.id, self.command, register.name):
        available_registers = self.get_available_registers(message.from_user.id)
        self.bot.send_message(
          message.chat.id,
          f'You can\'t change <b>{register.description}</b>. Available registers to change:\n{available_registers}',
          parse_mode = 'HTML')
        return

      def creator(prefix):
        return CustomRegisters([register], prefix)

      try:
        loggers = DeyeLoggers()
        holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
        holder.connect_and_read()
      except Exception as e:
        self.bot.send_message(message.chat.id, f'Error while creating DeyeRegistersHolder: {str(e)}')
        return
      finally:
        holder.disconnect()

      now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      time_diff = register.value - datetime.now()
      diff_seconds = int(abs(time_diff.total_seconds()))
      if diff_seconds > inverter_system_time_too_big_difference_sec:
        sent = ask_confirmation(
          self.bot, message.chat.id, f'Difference between inverter time and current time is too big:\n'
          f'Current time: <b>{now}</b>\n'
          f'Inverter time: <b>{register.value.strftime("%Y-%m-%d %H:%M:%S")}</b>\n'
          f'The difference is about {diff_seconds} seconds.\n'
          'Are you sure to sync inverter time?', self.on_user_confirmation)
        self.bot.clear_step_handler_by_chat_id(message.chat.id)
        self.bot.register_next_step_handler(message, self.user_confirmation_next_step_handler, sent.message_id)
      elif diff_seconds > self.time_does_not_need_sync_threshold_sec:
        self.on_user_confirmation(message.chat.id, True)
      else:
        self.bot.send_message(message.chat.id, 'The inverter time does not need to be synced', parse_mode = 'HTML')

  def get_available_registers(self, user_id: int) -> str:
    str = ''
    num = 1
    for register in self.registers.read_write_registers:
      if self.is_writable_register_allowed(user_id, self.command, register.name):
        str += f'<b>{num}. {register.description}:</b>\n'
        str += f'/{register.name}\n'
        num += 1
    return str

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      try:
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        register = self.registers.inverter_system_time_register
        text = self.process_read_write_register_step2(register, value)
        self.bot.send_message(chat_id, text, parse_mode = 'HTML')
      except Exception as e:
        self.bot.send_message(chat_id, str(e))
    else:
      self.bot.send_message(chat_id, 'Time sync cancelled')

  def process_read_write_register_step2(self, register: DeyeRegister, text: str) -> str:
    try:
      if type(register.value) is int and register.value == int(text):
        return f'New value ({int(text)}) is the same as old value ({register.value}). Do nothing'

      if type(register.value) is float and register.value == float(text):
        return f'New value ({float(text)}) is the same as old value ({register.value}). Do nothing'

      value = write_register(register, text)
      return f'<b>{register.description}</b> changed to {value} {register.suffix}'
    except Exception as e:
      raise Exception('Error while writing registers: ' + str(e))

  def user_confirmation_next_step_handler(self, message: telebot.types.Message, message_id: int):
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

    if message.text == 'yes':
      try:
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        register = self.registers.inverter_system_time_register
        text = self.process_read_write_register_step2(register, value)
        self.bot.send_message(message.chat.id, text, parse_mode = 'HTML')
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
    else:
      self.bot.send_message(message.chat.id, 'Time sync cancelled')
