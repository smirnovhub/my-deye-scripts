import random
import string

from typing import List

from telebot_test_users import TelebotTestUsers
from deye_registers import DeyeRegisters
from deye_base_enum import DeyeBaseEnum
from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import DeyeTestHelper
from deye_exceptions import DeyeKnownException

class TelebotWritableRegistersTest4Module(TelebotBaseTestModule):
  """
  Module `TelebotWritableRegistersTest4Module` is a test suite designed to verify
  that the Telegram bot correctly handles **invalid enum values** for writable Deye registers.

  The purpose of this module is to confirm that when a user provides an incorrect
  enum value—either interactively or directly through a command—the bot properly
  detects the error and responds with a message indicating that the value is unknown.

  **Test flow:**

  1. **Testing invalid enum values:**  
     - Iterates through all writable registers and selects only those that use enum types.
     - For each such register:
       - Sets a valid random enum value on the server to prepare the test environment.
       - Generates a random invalid string to simulate an incorrect enum input.

     **Interactive command check:**  
       - Sends a command to view the current value of the register.
       - Waits for the bot to display the current enum value and prompt for a new one.
       - Sends the invalid string as input.
       - Verifies that the bot responds with an error about an unknown enum value.

     **Direct command check:**  
       - Sends a command that directly includes the invalid value.
       - Confirms that the bot produces the same error response.

  2. **Validation:**  
     - Ensures that all writable enum registers reject unrecognized values.
     - Logs progress and completion once all checks have passed.

  This module validates that the bot consistently rejects invalid enum inputs
  in both interactive and direct command modes, ensuring reliable user input handling.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'writable registers test 4'

  def run_tests(self, servers: List[SolarmanServer]):
    user = TelebotTestUsers().test_user1

    registers = DeyeRegisters()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    master_server = self.get_master_server(servers)
    master_server.clear_registers()
    master_server.clear_registers_status()

    for register in registers.all_registers:
      if not register.can_write:
        continue

      if not isinstance(register.value, DeyeBaseEnum):
        continue

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")

      random_value = DeyeTestHelper.get_random_by_register_type(register)
      if random_value is None or not isinstance(random_value.value, DeyeBaseEnum):
        raise DeyeKnownException(f"Can't get random value for register '{register.name}' with "
                                 f"value type {type(register.value).__name__}...")

      master_server.set_register_values(random_value.register.addresses, random_value.values)

      # Check wrong enum values
      value = ''.join(random.choices(string.ascii_letters, k = 8))

      command = f'/{register.name}'

      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)
      self.wait_for_text_regex(rf'Current.+{register.description}.+value: {random_value.value.pretty}.*Enter new value')

      self.send_text(user, value)

      self.wait_for_text_regex(rf'Enum value for .*{register.description}.* is unknown')

      value = ''.join(random.choices(string.ascii_letters, k = 8))
      command = f'/{register.name} {value}'

      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)
      self.wait_for_text_regex(rf'Enum value for .*{register.description}.* is unknown')

      if master_server.is_something_written():
        self.error(f"Register '{register.name}' should not be written with wrong enum value")

    self.log.info('Seems all enum writable registers processed correctly')
