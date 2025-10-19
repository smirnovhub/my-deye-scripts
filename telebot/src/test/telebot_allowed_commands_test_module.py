import random

from typing import List

from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from deye_registers import DeyeRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_test_users import TelebotTestUsers
from testable_telebot import TestableTelebot

class TelebotAllowedCommandsTestModule(TelebotBaseTestModule):
  """
  Module `TelebotAllowedCommandsTestModule` verifies that the Telegram bot
  enforces **command access rights** correctly for a specific allowed user.

  The goal is to ensure that the user can only execute permitted commands
  and register modifications, while all other commands are blocked.

  **Test flow:**
  - Defines allowed commands and registers for the user.  
  - Identifies writable registers that are not allowed for modification.  
  - Sends all registered commands without arguments:
    - Allowed registers → bot prompts for current value input.  
    - Allowed commands → bot responds with relevant info.  
    - Disabled registers → bot informs the user they cannot change it.  
    - Any other command → bot responds that it is not allowed.  
  - Sends commands with arguments for disallowed registers and commands:
    - Confirms that the bot rejects unauthorized changes.  

  This module ensures that command permissions and access controls are
  enforced correctly for the user.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'allowed commands test'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

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

    self.log.info('Checking commands without arguments...')

    for command in self.get_all_registered_commands():
      cmd = f'/{command}'
      self.log.info(f"Sending command '{cmd}' from user {user.id} {user.name}")
      self.send_text(user, cmd)

      if command in disabled_registers:
        register = registers.get_register_by_name(command)
        self.wait_for_text_regex(f"You can't change.+{register.description}")
      elif command in allowed_registers:
        register = registers.get_register_by_name(command)
        self.wait_for_text_regex(f"Current.+{register.description}.+value:.*Enter new value")
      elif command in allowed_commands:
        self.wait_for_text("Inverter:")
      else:
        self.wait_for_text('Command is not allowed')

    self.log.info('Checking commands with arguments...')

    for command in self.get_all_registered_commands():
      if command in allowed_registers or command in allowed_commands:
        continue

      cmd = f'/{command} {random.randint(1000, 9999)}'
      self.log.info(f"Sending command '{cmd}' from user {user.id} {user.name}")
      self.send_text(user, cmd)

      if command in disabled_registers:
        register = registers.get_register_by_name(command)
        self.wait_for_text_regex(f"You can't change.+{register.description}")
      else:
        self.wait_for_text('Command is not allowed')

    self.log.info('Seems commands access rights processed correctly')
