import time
import telebot

from typing import List, Optional

from telebot_menu_item import TelebotMenuItem
from telebot_users import TelebotUsers
from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from telebot_fake_test_message import TelebotFakeTestMessage
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory
from deye_test_helper import get_random_by_register_type

from deye_utils import (
  get_current_time,
  time_format_str,
)

class TelebotInverterTimeSyncTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)
    self.registers = DeyeRegistersFactory.create_registers()

  def run_tests(self, servers: List[SolarmanServer]):
    users = TelebotUsers()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

    master_server: Optional[SolarmanServer] = None

    for srv in servers:
      if srv.name == self.loggers.master.name:
        master_server = srv
        break

    if master_server is None:
      self.error(f'Master server not found')
      return

    register = self.registers.inverter_system_time_register

    rnd = get_random_by_register_type(register)
    self.log.info(f'Setting time to server: {rnd.value}')
    master_server.set_register_values(register.address, rnd.values)

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

    self.log.info(f"Replying 'yes' for time sync confirmation...")
    self.bot.process_new_messages([yes_message])

    self.call_with_retry(self._check_results, register, master_server, rnd.value)

    self.log.info(f'Run command from button: {command}')

    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

    rnd = get_random_by_register_type(register)
    self.log.info(f'Setting time to server: {rnd.value}')
    master_server.set_register_values(register.address, rnd.values)

    fake_query = telebot.types.CallbackQuery(
      id = 321,
      chat_instance = 'fake',
      json_string = '',
      from_user = fake_message.from_user,
      data = command,
      message = fake_message,
    )

    self.bot.clear_messages()
    self.bot.process_new_callback_query([fake_query])
    time.sleep(1)

    self.log.info(f"Replying 'yes' for time sync confirmation...")
    self.bot.process_new_messages([yes_message])

    self.call_with_retry(self._check_results, register, master_server, rnd.value)

  def _check_results(self, register: DeyeRegister, master_server: SolarmanServer, changed_from: str):
    changed_to = get_current_time().strftime(time_format_str)
    pattern = (rf'{register.description}.+changed '
               f'from {changed_from} '
               f'to {changed_to}')

    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"No messages to match pattern '{pattern}'")

    if not master_server.is_registers_written(register.address, register.quantity):
      self.error(f"No changes on the server side after writing '{register.name}'")

    self.log.info('Time change found. Everything looks good')
