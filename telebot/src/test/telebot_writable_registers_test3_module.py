from typing import List, Optional

from telebot_test_users import TelebotTestUsers
from deye_registers_factory import DeyeRegistersFactory
from deye_base_enum import DeyeBaseEnum
from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import get_random_by_register_type

class TelebotWritableRegistersTest3Module(TelebotBaseTestModule):
  """
  Module `TelebotWritableRegistersTest3Module` is a test suite for validating
  writable Deye registers via a testable Telegram bot, specifically testing
  the case when the new value matches the current server value.

  For each writable register, the following steps are performed:

  1. **Generate and set random value on server**:  
    - Generates a random value for the register using `get_random_by_register_type`.
    - Pre-sets this value on the master server so that the register already has it.

  2. **Send command with same value via Telegram bot**:  
    - Sends a command in the form `/register_name value` where `value` equals
      the current server value.
    - The bot processes the message.

  3. **Verify bot response**:  
    - Checks that the bot responds with a message indicating that the new value
      is the same as the old value and nothing changed.
    - Raises an error if no such confirmation message is found.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[SolarmanServer]):
    user = TelebotTestUsers().test_user1

    registers = DeyeRegistersFactory.create_registers()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

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

    for register in registers.all_registers:
      if not register.can_write:
        continue

      random_value = get_random_by_register_type(register)
      if random_value is None:
        continue

      master_server.set_register_values(random_value.register.addresses, random_value.values)

      self.bot.clear_messages()

      value = str(random_value.value)

      command = f'/{register.name} {value}'

      if isinstance(random_value.value, DeyeBaseEnum):
        value = random_value.value.pretty

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)

      suffix = f' {register.suffix}'.rstrip()
      self.wait_for_text_regex(rf'.*New value \({value}{suffix}\) is '
                               'the same as old value. Nothing changed.*')

    self.log.info('Seems all registers processed currectly')
    self.log.info(f'Module {type(self).__name__} done successfully')
