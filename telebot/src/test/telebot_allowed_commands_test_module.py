from typing import List

from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from deye_registers import DeyeRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_test_users import TelebotTestUsers
from testable_telebot import TestableTelebot

class TelebotAllowedCommandsTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'allowed commands test'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    user = TelebotTestUsers().test_user3
    registers = DeyeRegisters()

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
      self.log.info(f"Sending command '/{command}' from user {user.id} {user.name}")

      self.send_text(user, f'/{command}')

      if command in disabled_registers:
        self.wait_for_text_regex(".*You can't change.*")
      elif command in allowed_registers:
        self.wait_for_text_regex(".*Current.*value:.*Enter new value.*")
      elif command in allowed_commands:
        self.wait_for_text_regex(".*Inverter:.*")
      else:
        self.wait_for_text_regex('.*Command is not allowed.*')

    self.log.info('Seems commands access rights processed currectly')
    self.log.info(f'Module {type(self).__name__} done successfully')
