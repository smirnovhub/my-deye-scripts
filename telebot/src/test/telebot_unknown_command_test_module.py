import random
import string

from typing import List

from telebot_test_users import TelebotTestUsers
from solarman_test_server import SolarmanTestServer
from deye_registers import DeyeRegisters
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot

class TelebotUnknownCommandTestModule(TelebotBaseTestModule):
  """
  Module `TelebotUnknownCommandTestModule` is a test suite that verifies how
  the Telegram bot responds to **unknown or unsupported commands**.

  The goal of this module is to confirm that the bot consistently detects
  and reports unrecognized commands, whether they are random strings or names
  of non-writable registers.

  **Test flow:**

  1. **Random unknown commands:**  
     - Repeatedly generates random strings composed of letters, digits, and underscores.
     - Sends each as a command (e.g., `/randomcommand`).
     - Confirms that the bot responds with a message indicating the command is unknown.
     - Repeats the test with an additional random parameter (e.g., `/randomcommand param`)
       to ensure the same behavior when extra text is included.

  2. **Non-writable register commands:**  
     - Iterates through all available registers.
     - Selects those that are not writable.
     - Sends commands using their names both with and without additional parameters.
     - Checks that the bot treats such cases as unknown commands and responds accordingly.

  3. **Validation:**  
     - Verifies that all responses correctly identify unsupported commands.
     - Logs detailed progress and completion messages for traceability.

  This module ensures that the bot reliably rejects all unrecognized inputs,
  maintaining predictable and user-friendly command handling behavior.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'unknown commands test'

  def run_tests(self, servers: List[SolarmanTestServer]):
    user = TelebotTestUsers().test_user1

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    choices = string.ascii_letters + string.digits + '_'

    for i in range(5):
      command = ''.join(random.choices(choices, k = 16))

      self.log.info(f"Sending command '/{command}'")

      self.send_text(user, f'/{command}')
      self.wait_for_text_regex(rf'Unknown command: /.*{command}')

    for i in range(5):
      command = ''.join(random.choices(choices, k = 16))
      param = ''.join(random.choices(choices, k = 8))

      self.log.info(f"Sending command '/{command} {param}'")

      self.send_text(user, f'/{command} {param}')
      self.wait_for_text_regex(rf'Unknown command: /.*{command}')

    self.log.info('Testing non-writable registers as a command...')

    registers = DeyeRegisters()

    for register in registers.all_registers:
      if register.can_write:
        continue

      if register.name == registers.time_of_use_register.name:
        continue

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")

      command = f'/{register.name}'

      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)
      self.wait_for_text_regex(rf'Unknown command: /.*{register.name}')

      value = ''.join(random.choices(string.ascii_letters, k = 8))
      command = f'/{register.name} {value}'

      self.log.info(f"Sending command '{command}'")

      self.send_text(user, command)
      self.wait_for_text_regex(rf'Unknown command: /.*{register.name}')

    self.log.info('Seems unknown commands processed correctly')
