import telebot

from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices_helper import row_break_str
from telebot_advanced_choice import ask_advanced_choice

from telebot_constants import (
  sync_inverter_time_button_name,
  inverter_system_time_need_sync_difference_sec,
)

from telebot_deye_helper import (
  holder_kwargs,
  get_register_values,
  get_choices_of_invertors,
)

class TelebotMenuAllBase(TelebotMenuItemHandler):
  def __init__(
    self,
    bot: telebot.TeleBot,
    registers: DeyeRegisters,
    all_command: TelebotMenuItem,
    master_command: TelebotMenuItem,
    slave_command: TelebotMenuItem,
  ):
    super().__init__(bot)
    self.registers = registers
    self.all_command: TelebotMenuItem = all_command
    self.master_command: TelebotMenuItem = master_command
    self.slave_command: TelebotMenuItem = slave_command

  @property
  def command(self) -> TelebotMenuItem:
    return self.all_command

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message.from_user.id, message.chat.id):
      return

    def creator(prefix):
      return self.registers

    loggers = DeyeLoggers()
    holder = DeyeRegistersHolder(loggers = loggers.loggers, register_creator = creator, **holder_kwargs)

    try:
      holder.connect_and_read()
    except Exception as e:
      self.bot.send_message(message.chat.id, f'Error while reading registers: {str(e)}')
      return
    finally:
      holder.disconnect()

    choices = get_choices_of_invertors(
      user_id = message.from_user.id,
      all_command = self.all_command,
      master_command = self.master_command,
      slave_command = self.slave_command,
    )

    # add button for time sync if needed
    if abs(self.registers.inverter_system_time_diff_register.value) > inverter_system_time_need_sync_difference_sec:
      # add line break for keyboard
      choices[row_break_str] = row_break_str
      # add time sync command
      choices[sync_inverter_time_button_name] = f'/{TelebotMenuItem.deye_sync_time.command}'

    info = get_register_values(holder.accumulated_registers.all_registers)

    ask_advanced_choice(
      self.bot,
      message.chat.id,
      f'<b>Inverter: all</b>\n{info}',
      choices,
      max_per_row = 2,
    )
