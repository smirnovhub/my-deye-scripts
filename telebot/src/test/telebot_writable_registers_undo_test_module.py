from typing import List, Optional

from telebot_test_users import TelebotTestUsers
from deye_registers import DeyeRegisters
from solarman_server import SolarmanServer
from deye_base_enum import DeyeBaseEnum
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import DeyeTestHelper

class TelebotWritableRegistersUndoTestModule(TelebotBaseTestModule):
  """
  Module `TelebotWritableRegistersUndoTestModule` tests the correctness of
  **Undo buttons** for writable Deye registers in the Telegram bot.

  The goal is to ensure that after a register value is changed, the bot
  generates a valid Undo command that restores the previous value.

  **Test flow:**
  - Iterates through all writable registers.  
  - Sets a random initial value on the server.  
  - Changes it to a new random value via the bot.  
  - Waits for confirmation and retrieves the Undo button data.  
  - Checks that the Undo command matches the expected format
    `/<register_name> <old_value>`.

  This module confirms that all writable registers produce correct Undo buttons
  and that the bot supports reliable rollback of recent changes.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'writable registers undo button test'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    user = TelebotTestUsers().test_user1
    registers = DeyeRegisters()
    master_server = self.get_master_server(servers)

    for register in registers.all_registers:
      if not register.can_write:
        continue

      old_random_value = DeyeTestHelper.get_random_by_register_type(register)
      if old_random_value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      master_server.set_register_values(old_random_value.register.addresses, old_random_value.values)

      new_random_value: Optional[str] = None

      for i in range(15):
        new_random_value = DeyeTestHelper.get_random_by_register_value_type(register)
        if str(new_random_value) != str(old_random_value.value):
          break
      else:
        self.error("Can't generate register random value")

      if new_random_value is None:
        self.error("Can't generate register random value")
        break

      command = f'/{register.name}'

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)
      self.wait_for_text_regex(rf'Current.+{register.description}.+value.*Enter new value')

      self.send_text(user, new_random_value)

      if isinstance(register.value, DeyeBaseEnum):
        self.wait_for_text('Do you really want to change')
        self.send_text(user, 'yes')

      self.wait_for_server_changes(master_server, register)
      undo_data = self.wait_for_text_regex_and_get_undo_data(rf'{register.description}.+changed from .+ to ')

      expected = f'/{register.name} {old_random_value.value}'
      self.log.info(f"Checking expected undo data '{expected}' for register '{register.name}'...")

      if undo_data != expected:
        self.error(f"Undo data is wrong for register '{register.name}': expected '{expected}', but found '{undo_data}'")
      else:
        self.log.info(f"Undo data is ok for register '{register.name}'")

    self.log.info('Seems all registers have correct undo buttons')
