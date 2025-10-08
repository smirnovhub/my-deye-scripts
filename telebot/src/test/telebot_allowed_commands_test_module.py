from typing import List

from solarman_server import SolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from deye_registers_factory import DeyeRegistersFactory
from telebot_menu_item import TelebotMenuItem
from telebot_test_users import TelebotTestUsers
from testable_telebot import TestableTelebot

class TelebotAllowedCommandsTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    user = TelebotTestUsers().test_user3
    registers = DeyeRegistersFactory.create_registers()

    allowed_commands: List[str] = [
      TelebotMenuItem.deye_all_info.command.format(self.loggers.accumulated_registers_prefix),
      TelebotMenuItem.deye_master_total_stat.command.format(self.loggers.master.name),
    ]

    for logger in self.loggers.slaves:
      allowed_commands.append(TelebotMenuItem.deye_slave_today_stat.command.format(logger.name))

    allowed_registers: List[str] = [
      registers.time_of_use_power_register.name,
      registers.grid_peak_shaving_power_register.name,
      registers.zero_export_power_register.name,
    ]

    disabled_registers: List[str] = []

    for register in registers.all_registers:
      if register.can_write:
        if register.name not in allowed_registers:
          disabled_registers.append(register.name)

    for command in self.get_all_registered_commands():
      self.bot.clear_messages()

      self.log.info(f"Sending command '/{command}' from user {user.id} {user.name}")

      change_message = TelebotFakeTestMessage.make(
        text = f'/{command}',
        user_id = user.id,
        first_name = user.name,
      )

      self.bot.process_new_messages([change_message])

      self.call_with_retry(
        self._check_result,
        command = command,
        allowed_commands = allowed_commands,
        allowed_registers = allowed_registers,
        disabled_registers = disabled_registers,
      )

    self.log.info('Seems commands access rights processed currectly')

  def _check_result(
    self,
    command: str,
    allowed_commands: List[str],
    allowed_registers: List[str],
    disabled_registers: List[str],
  ):
    if command in disabled_registers:
      self._check_pattern(".*You can't change.*")
    elif command in allowed_registers:
      self._check_pattern(".*Current.*value:.*Enter new value.*")
    elif command in allowed_commands:
      self._check_pattern(".*Inverter:.*")
    else:
      self._check_pattern('.*Command is not allowed.*')

  def _check_pattern(self, pattern: str):
    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"Waiting for message '{pattern}'")
    else:
      self.log.info(f"Message '{pattern}' received")
