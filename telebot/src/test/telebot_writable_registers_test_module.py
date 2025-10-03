import time
import logging

from typing import List, Optional

from deye_loggers import DeyeLoggers
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
    loggers = DeyeLoggers()
    registers = DeyeRegistersFactory.create_registers()
    log = logging.getLogger()

    if not loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    server: Optional[AioSolarmanServer] = None

    for srv in servers:
      if srv.name == loggers.master.name:
        server = srv
        break

    if server is None:
      self.error(f'Unable to find server with name {loggers.master.name}')
      return

    server.clear_registers()
    server.clear_registers_status()

    for register in registers.all_registers:
      if not register.can_write:
        continue

      value = get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        log.info(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      log.info(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")
      log.info(f"Sending command '/{register.name} {value}'")

      fake_message = TelebotFakeTestMessage.make(
        text = f'/{register.name} {value}',
        user_id = users.allowed_users[0].id,
      )

      self.bot.process_new_messages([fake_message])

    time.sleep(15)

    for register in registers.all_registers:
      if not register.can_write:
        continue

      log.info(f'Checking {register.name}...')

      if not server.is_registers_written(register.address, register.quantity):
        self.error(f"No changes on the server side after writing '{register.name}'")
