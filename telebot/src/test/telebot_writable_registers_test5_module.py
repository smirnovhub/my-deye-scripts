import random

from typing import List

from telebot_test_users import TelebotTestUsers
from deye_registers import DeyeRegisters
from solarman_test_server import SolarmanTestServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot

class TelebotWritableRegistersTest5Module(TelebotBaseTestModule):
  """
  Module `TelebotWritableRegistersTest5Module` is a test suite that verifies
  how the Telegram bot handles **out-of-range values** for writable numeric
  Deye registers (integers and floats).

  The purpose of this module is to ensure that the bot correctly rejects values
  that exceed the allowed minimum or maximum for each register, preventing
  invalid writes to the server.

  **Test flow:**

  1. **Preparation:**  
     - Clears all registers and their statuses on the master server to start fresh.

  2. **Out-of-range value tests:**  
     - Iterates through all writable numeric registers.
     - For each register, generates test values that are:
       - Slightly above the maximum allowed value.
       - Slightly below the minimum allowed value.
       - Large positive numbers outside the valid range.
       - Large negative numbers outside the valid range.
     - Sends these values to the bot both interactively and directly via command.

  3. **Validation:**  
     - Confirms that the bot responds with messages indicating the value is out
       of the allowed range.
     - Ensures that no out-of-range value is actually written to the server.
     - Logs progress and final success messages for traceability.

  This module ensures robust validation for numeric writable registers,
  guaranteeing that the bot prevents any out-of-range assignments.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)
    self.registers = DeyeRegisters()
    self.user = TelebotTestUsers().test_user1

  @property
  def description(self) -> str:
    return 'writable registers test 5'

  def run_tests(self, servers: List[SolarmanTestServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    master_server = self.get_master_server(servers)
    master_server.clear_registers()
    master_server.clear_registers_status()

    self.test_registers(master_server, 0.01)
    self.test_registers(master_server, -0.01)
    self.test_registers(master_server, 1)
    self.test_registers(master_server, -1)
    self.test_registers(master_server, random.randint(100, 99999))
    self.test_registers(master_server, random.randint(-99999, -100))

    self.log.info('Seems all writable registers with out-of-range values processed correctly')

  def test_registers(self, server: SolarmanTestServer, shift: float):
    for register in self.registers.all_registers:
      if not register.can_write:
        continue

      if not isinstance(register.value, int) and not isinstance(register.value, float):
        continue

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")

      if shift > 0:
        val = register.max_value + shift
        self.log.info(f"Testing shift {shift} above register's max value {register.max_value}")
      else:
        val = register.min_value + shift
        self.log.info(f"Testing shift {shift} below register's min value {register.min_value}")

      command = f'/{register.name}'

      self.log.info(f"Sending command '{command}'")

      self.send_text(self.user, command)
      self.wait_for_text_regex(rf'Current.+{register.description}.+value.*Enter new value')

      self.send_text(self.user, str(val))

      self.wait_for_text_regex(f'value should be (int|float)?\s?from {register.min_value} to {register.max_value}')

      command = f'/{register.name} {val}'

      self.log.info(f"Sending command '{command}'")
      self.send_text(self.user, command)

      self.wait_for_text_regex(f'value should be (int|float)?\s?from {register.min_value} to {register.max_value}')

      if server.is_something_written():
        self.error(f"Register '{register.name}' should not be written with out of range value")
