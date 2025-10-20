from typing import List

from telebot_test_users import TelebotTestUsers
from deye_registers import DeyeRegisters
from solarman_server import SolarmanServer
from deye_base_enum import DeyeBaseEnum
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import DeyeTestHelper

class TelebotWritableRegistersTest1Module(TelebotBaseTestModule):
  """
  Module `TelebotWritableRegistersTest1Module` is a test suite for validating
  writable Deye registers via a testable Telegram bot.

  For each writable register, the following steps are performed:

  1. **Generate test value**:  
    A random valid value is generated according to the register's type,
    skipping zero if required.

  2. **Simulate command via Telegram bot**:  
    - Sends a command in the form `/register_name`.
    - Checks if the bot asks for the current value (prompt verification).

  3. **Send new value**:  
    - Sends the generated value as a Telegram message.
    - Verifies that the server registers are updated.
    - Checks that the bot replies with a confirmation message reflecting the change.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'writable registers test 1'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    user = TelebotTestUsers().test_user1
    registers = DeyeRegisters()
    master_server = self.get_master_server(servers)

    for register in registers.all_registers:
      if not register.can_write:
        continue

      value = DeyeTestHelper.get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      command = f'/{register.name}'

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)
      self.wait_for_text_regex(rf'Current.+{register.description}.+value.*Enter new value')

      self.send_text(user, value)

      if isinstance(register.value, DeyeBaseEnum):
        self.wait_for_text('Do you really want to change')
        self.send_text(user, 'yes')

      self.wait_for_server_changes(master_server, register)
      self.wait_for_text_regex(rf'{register.description}.+changed from .+ to ')

    self.log.info('Seems all writable registers processed correctly')
