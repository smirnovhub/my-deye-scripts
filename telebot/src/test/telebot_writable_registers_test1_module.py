from typing import List, Optional

from deye_register import DeyeRegister
from telebot_test_users import TelebotTestUsers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import SolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import get_random_by_register_value_type

class TelebotWritableRegistersTest1Module(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    user = TelebotTestUsers().test_user1
    registers = DeyeRegistersFactory.create_registers()

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

      value = get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      self.bot.clear_messages()

      command = f'/{register.name}'

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '{command}'")

      change_message = TelebotFakeTestMessage.make(
        text = command,
        user_id = user.id,
        first_name = user.name,
      )

      self.bot.process_new_messages([change_message])
      self.call_with_retry(self._check_for_ask, register)

      value_message = TelebotFakeTestMessage.make(
        text = f'{value}',
        user_id = user.id,
        first_name = user.name,
      )

      self.bot.process_new_messages([value_message])
      self.call_with_retry(self._check_for_server_changes, master_server, register)
      self.call_with_retry(self._check_for_reply_message, register)

    self.log.info('Seems all registers processed currectly')

  def _check_for_ask(self, register: DeyeRegister):
    pattern = rf'Current.+{register.description}.+value.*Enter new value'
    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"No messages to match pattern '{pattern}'")
    else:
      self.log.info(f'Checking {register.name}... OK')

  def _check_for_server_changes(self, server: SolarmanServer, register: DeyeRegister):
    if not server.is_registers_written(register.address, register.quantity):
      self.log.info(f'Checking {register.name}... FAILED')
      self.error(f"No changes on the server side after writing '{register.name}'")
    else:
      self.log.info(f'Checking {register.name}... OK')

  def _check_for_reply_message(self, register: DeyeRegister):
    pattern = (rf'{register.description}.+changed from .+ to ')
    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"No messages to match pattern '{pattern}'")
    else:
      self.log.info(f'Checking {register.name}... OK')
