import telebot

from typing import List, Type

from telebot_utils import TelebotUtils
from deye_registers import DeyeRegisters
from telebot_command_choice import CommandChoice
from telebot_menu_item import TelebotMenuItem
from telebot_async_runner import TelebotAsyncRunner
from telebot_constants import TelebotConstants
from telebot_deye_helper import TelebotDeyeHelper
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync
from deye_registers_holder_async import DeyeRegistersHolderAsync

class TelebotMenuAllBase(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
    registers_class: Type[DeyeRegisters],
    all_command: TelebotMenuItem,
    master_command: TelebotMenuItem,
    slave_command: TelebotMenuItem,
    title: str = TelebotConstants.default_title,
  ):
    super().__init__(bot = bot, runner = runner)
    self.registers_class = registers_class
    self.all_command = all_command
    self.master_command = master_command
    self.slave_command = slave_command
    self.title = title

  @property
  def command(self) -> TelebotMenuItem:
    return self.all_command

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return [
      telebot.types.BotCommand(
        command = self.command.command.format(self.loggers.accumulated_registers_prefix),
        description = self.command.description.format(self.loggers.accumulated_registers_prefix.title()),
      )
    ]

  async def process_message(self, message: telebot.types.Message) -> None:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolderAsync(
      loggers = self.loggers.loggers,
      register_creator = lambda prefix: self.registers_class(prefix = prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      await holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    choices = TelebotDeyeHelper.get_choices_of_inverters(
      user_id = message.from_user.id,
      all_command = self.all_command,
      master_command = self.master_command,
      slave_command = self.slave_command,
    )

    registers = holder.accumulated_registers

    # add button for time sync if needed
    if abs(registers.inverter_system_time_diff_register.value
           ) > TelebotConstants.inverter_system_time_need_sync_difference_sec:
      # add line break for keyboard
      choices[TelebotUtils.row_break_str] = TelebotUtils.row_break_str
      # add time sync command
      choices[TelebotConstants.sync_inverter_time_button_name] = f'/{TelebotMenuItem.deye_sync_time.command}'

    info = TelebotDeyeHelper.get_register_values(registers.all_registers)

    CommandChoice.ask_command_choice(
      self.bot,
      message.chat.id,
      f'<b>{self.title}: {self.loggers.accumulated_registers_prefix}</b>\n{info}',
      choices,
      max_per_row = 2,
    )
