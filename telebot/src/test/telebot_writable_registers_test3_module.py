from typing import List, Optional

from deye_register import DeyeRegister
from telebot_test_users import TelebotTestUsers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import SolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import get_random_by_register_type

class TelebotWritableRegistersTest3Module(TelebotBaseTestModule):
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

      command = f'/{register.name} {random_value.value}'

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      change_message = TelebotFakeTestMessage.make(
        text = command,
        user_id = user.id,
        first_name = user.name,
      )

      self.bot.process_new_messages([change_message])
      self.call_with_retry(self._check_result, register)

    self.log.info('Seems all registers processed currectly')

  def _check_result(self, register: DeyeRegister):
    pattern = rf'.*New value \(.+\) is the same as old value. Nothing changed.*'
    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"No messages to match pattern '{pattern}'")
    else:
      self.log.info(f'Checking {register.name}... OK')
