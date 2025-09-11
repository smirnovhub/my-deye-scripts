import textwrap
import telebot

from telebot_deye_helper import *
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from single_register import SingleRegister
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotMenuWritebleRegisters(TelebotMenuItem):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func
    self.registers = DeyeRegisters()

  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.deye_writeble_registers

  def get_commands(self):
    commands = []
    for register in self.registers.read_write_registers:
      commands.append(telebot.types.BotCommand(command = register.name, description = register.description))
    return commands

  def register_handlers(self):
    for register in self.registers.read_write_registers:
      code = self.get_writable_register_handler(register.name)
      exec(code, locals())

  def get_writable_register_handler(self, register_name):
    return textwrap.dedent('''\
    @self.bot.message_handler(commands = ['{register_name}'])
    def set_{register_name}(message):
      if not self.is_authorized(message, self.command):
        return

      register = self.registers.{register_name}_register

      try:
        text = self.process_read_write_register_step1(register)
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
        self.bot.register_next_step_handler(message, set_{register_name}_step2)
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
  
    def set_{register_name}_step2(message):
      if not self.is_authorized(message, self.command):
        return

      register = self.registers.{register_name}_register

      try:
        text = self.process_read_write_register_step2(register, message.text)
        self.bot.send_message(message.chat.id, text)
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
  ''').format(register_name = register_name)

  def process_read_write_register_step1(self, register):
    loggers = DeyeLoggers()

    def creator(prefix):
      return SingleRegister(register, prefix)

    try:
      holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
      holder.connect_and_read()
    except Exception as e:
      raise Exception(str(e))
    finally:
      holder.disconnect()

    result = f'Current <b>{register.description}</b> value: {register.value} {register.suffix}\n'

    if register.min_value != register.max_value:
      result += f'Enter new value (from {register.min_value} to {register.max_value}):'
    else:
      result += f'Enter new value:'

    return result

  def process_read_write_register_step2(self, register, text):
    try:
      if type(register.value) is int and register.value == int(text):
        return f'New value ({int(text)}) the same as old value ({register.value}). Do nothing'

      if type(register.value) is float and register.value == float(text):
        return f'New value ({float(text)}) the same as old value ({register.value}). Do nothing'

      value = write_register(register, text)
      return f'New value written successfully: {value} {register.suffix}'
    except Exception as e:
      raise Exception('Error while writing registers: ' + str(e))
