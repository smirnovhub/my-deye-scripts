from typing import List, Optional

from telebot_test_users import TelebotTestUsers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import SolarmanServer
from deye_base_enum import DeyeBaseEnum
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import get_random_by_register_type
from deye_test_helper import get_random_by_register_value_type

class TelebotWritableRegistersUndoTestModule(TelebotBaseTestModule):
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

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    user = TelebotTestUsers().test_user1
    registers = DeyeRegistersFactory.create_registers()
    master_server: Optional[SolarmanServer] = None

    for srv in servers:
      if srv.name == self.loggers.master.name:
        master_server = srv
        break

    if master_server is None:
      self.error('Master server not found')
      return

    for register in registers.all_registers:
      if not register.can_write:
        continue

      old_random_value = get_random_by_register_type(register)
      if old_random_value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      master_server.set_register_values(old_random_value.register.addresses, old_random_value.values)

      new_random_value: Optional[str] = None

      for i in range(15):
        new_random_value = get_random_by_register_value_type(register)
        if str(new_random_value) != str(old_random_value.value):
          break
      else:
        self.error("Cant't generate register random value")

      if new_random_value is None:
        self.error("Cant't generate register random value")
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
      if undo_data != expected:
        self.error(f"Undo data is wrong for register '{register.name}': expected '{expected}', but found '{undo_data}'")
      else:
        self.log.info(f"Undo data is ok for register '{register.name}'")

    self.log.info('Seems all registers processed currectly')
    self.log.info(f'Module {type(self).__name__} done successfully')
