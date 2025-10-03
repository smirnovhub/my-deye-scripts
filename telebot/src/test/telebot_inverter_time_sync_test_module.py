import re
import time
import logging
import telebot

from typing import List, Optional

from deye_loggers import DeyeLoggers
from telebot_menu_item import TelebotMenuItem
from telebot_users import TelebotUsers
from solarman_server import AioSolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from telebot_fake_test_message import TelebotFakeTestMessage
from deye_registers_factory import DeyeRegistersFactory

class TelebotInverterTimeSyncTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)
    self.loggers = DeyeLoggers()
    self.log = logging.getLogger()
    self.registers = DeyeRegistersFactory.create_registers()

  def run_tests(self, servers: List[AioSolarmanServer]):
    users = TelebotUsers()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

    time.sleep(1)
    command = f'/{TelebotMenuItem.deye_sync_time.command}'

    fake_message = TelebotFakeTestMessage.make(
      text = command,
      user_id = users.allowed_users[0].id,
    )

    yes_message = TelebotFakeTestMessage.make(
      text = 'yes',
      user_id = users.allowed_users[0].id,
    )

    self.log.info(f'Run regular command: {command}')
    self.bot.clear_messages()
    self.bot.process_new_messages([fake_message])
    time.sleep(1)
    self.bot.process_new_messages([yes_message])

    time.sleep(3)
    self._check_results(servers)

    self.log.info(f'Run command from button: {command}')

    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

    fake_query = telebot.types.CallbackQuery(
      id = "fake",
      chat_instance = 'fake',
      json_string = '',
      from_user = fake_message.from_user,
      data = command,
      message = fake_message,
    )

    time.sleep(1)

    self.bot.clear_messages()
    self.bot.process_new_callback_query([fake_query])
    time.sleep(1)
    self.bot.process_new_messages([yes_message])

    time.sleep(3)
    self._check_results(servers)

  def _check_results(self, servers: List[AioSolarmanServer]):
    register = self.registers.inverter_system_time_register
    pattern = rf"{re.escape(register.description)}.+changed from\s+.+?\s+to\s+.+"

    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"No string to match pattern '{pattern}'")

    master_server: Optional[AioSolarmanServer] = None
    for server in servers:
      if server.name == self.loggers.master.name:
        master_server = server
        break

    if master_server is None:
      self.error('Master server not found')
      return

    if not master_server.is_registers_written(register.address, register.quantity):
      self.error(f"No changes on the server side after writing '{register.name}'")
