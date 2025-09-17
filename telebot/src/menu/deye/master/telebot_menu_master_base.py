import telebot

from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import ask_advanced_choice

from telebot_deye_helper import (
  holder_kwargs,
  get_register_values,
  get_choices_of_invertors,
)

from telebot_constants import (
  sync_inverter_time_str,
  inverter_system_time_need_sync_difference_sec,
)

class TelebotMenuMasterBase(TelebotMenuItemHandler):
  def __init__(
    self,
    bot: telebot.TeleBot,
    registers: DeyeRegisters,
    all_command: TelebotMenuItem,
    master_command: TelebotMenuItem,
    slave_command: TelebotMenuItem,
    is_authorized_func,
  ):
    super().__init__(bot)
    self.is_authorized = is_authorized_func
    self.loggers = DeyeLoggers()
    self.registers = registers
    self.all_command: TelebotMenuItem = all_command
    self.master_command: TelebotMenuItem = master_command
    self.slave_command: TelebotMenuItem = slave_command

  @property
  def command(self) -> TelebotMenuItem:
    return self.master_command

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message, self.command):
      return

    def creator(prefix):
      return self.registers

    loggers = DeyeLoggers()
    holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)

    try:
      holder.connect_and_read()
    except Exception as e:
      self.bot.send_message(message.chat.id, f'Error while reading registers: {str(e)}')
      return
    finally:
      holder.disconnect()

    choices = get_choices_of_invertors(
      all_command = self.all_command,
      master_command = self.master_command,
      slave_command = self.slave_command,
    )

    if abs(self.registers.inverter_system_time_diff_register.value) > inverter_system_time_need_sync_difference_sec:
      # add line break for keyboard
      choices[''] = ''
      # add time sync command
      choices[sync_inverter_time_str] = f'/{TelebotMenuItem.deye_sync_time.command}'

    info = get_register_values(holder.master_registers.all_registers)

    ask_advanced_choice(
      self.bot,
      message.chat.id,
      f'<b>Inverter: master</b>\n{info}',
      choices,
      max_per_row = 2,
    )
