from typing import List, Optional

from deye_register import DeyeRegister
from telebot_users import TelebotUsers
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import get_random_by_register_value_type

class TelebotWritableRegistersTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[AioSolarmanServer]):
    users = TelebotUsers()

    registers = DeyeRegistersFactory.create_registers()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    server: Optional[AioSolarmanServer] = None

    for srv in servers:
      if srv.name == self.loggers.master.name:
        server = srv
        break

    if server is None:
      self.error(f'Unable to find server with name {self.loggers.master.name}')
      return

    server.clear_registers()
    server.clear_registers_status()

    for register in registers.all_registers:
      if not register.can_write:
        continue

      value = get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        self.log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      self.log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      self.log.info(f"Sending command '/{register.name} {value}'")

      fake_message = TelebotFakeTestMessage.make(
        text = f'/{register.name} {value}',
        user_id = users.allowed_users[0].id,
      )

      self.bot.process_new_messages([fake_message])

    writable_registers = [r for r in registers.all_registers if r.can_write]
    self.call_with_retry(self._check_results, server, writable_registers)

  def _check_results(self, server: AioSolarmanServer, registers: List[DeyeRegister]):
    to_remove = []
    for register in registers:
      if not server.is_registers_written(register.address, register.quantity):
        self.log.info(f'Checking {register.name}... FAILED')

        for r in to_remove:
          registers.remove(r)

        self.error(f"No changes on the server side after writing '{register.name}'")
      else:
        self.log.info(f'Checking {register.name}... OK')
        to_remove.append(register)

    for register in to_remove:
      registers.remove(register)

    if registers:
      self.error(f"No changes on the server side after writing some registers")
