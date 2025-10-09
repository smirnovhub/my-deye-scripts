from typing import List, Optional

from deye_register import DeyeRegister
from telebot_test_users import TelebotTestUsers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import SolarmanServer
from deye_base_enum import DeyeBaseEnum
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import get_random_by_register_value_type

class TelebotWritableRegistersTest2Module(TelebotBaseTestModule):
  """
  Module `TelebotWritableRegistersTest2Module` is a test suite for validating
  writable Deye registers via a testable Telegram bot using direct value commands.

  For each writable register, the following steps are performed:

  1. **Generate test value**:  
    A random valid value is generated according to the register's type,
    skipping zero if required.

  2. **Send command with value via Telegram bot**:  
    - Sends a command in the form `/register_name value`.
    - The bot processes the message without asking for the current value.

  3. **Verify server changes**:  
    - Checks that the server registers are updated according to the sent values.
    - Raises an error if any writable register did not change as expected.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'writable registers test 2'

  def run_tests(self, servers: List[SolarmanServer]):
    user = TelebotTestUsers().test_user1

    registers = DeyeRegistersFactory.create_registers()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    self.bot.clear_messages()

    master_server: Optional[SolarmanServer] = None

    for srv in servers:
      if srv.name == self.loggers.master.name:
        master_server = srv
        break

    if master_server is None:
      self.error('Master server not found')
      return

    master_server.clear_registers()
    master_server.clear_registers_status()

    processed_registers: List[DeyeRegister] = []

    # Process all registers except enum
    for register in registers.all_registers:
      if not register.can_write:
        continue

      if isinstance(register.value, DeyeBaseEnum):
        continue

      processed_registers.append(register)

      value = get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      command = f'/{register.name} {value}'

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)

    self.call_with_retry(self._check_results, master_server, processed_registers)

    # Process enum registers
    for register in registers.all_registers:
      if not register.can_write:
        continue

      if not isinstance(register.value, DeyeBaseEnum):
        continue

      value = get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      command = f'/{register.name} {value}'

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)

      self.wait_for_text('Do you really want to change')
      self.send_text(user, 'yes')

      self.wait_for_server_changes(master_server, register)
      self.wait_for_text_regex(rf'{register.description}.+changed from .+ to ')

    self.log.info('Seems all registers processed currectly')
    self.log.info(f'Module {type(self).__name__} done successfully')

  def _check_results(self, server: SolarmanServer, registers: List[DeyeRegister]):
    for register in registers:
      if not server.is_registers_written(
          register.address,
          register.quantity,
      ) or not self.bot.is_messages_contains_regex(rf'.*{register.description}.+changed from.+to.+'):
        self.log.info(f'Checking {register.name}... FAILED')
        self.error(f"No changes after writing '{register.name}'")
      else:
        self.log.info(f'Checking {register.name}... OK')
