import time
import logging
import telebot

from typing import Callable, List

from deye_loggers import DeyeLoggers
from telebot_menu_item import TelebotMenuItem
from telebot_users import TelebotUsers
from solarman_server import AioSolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_registers import DeyeRegisters
from telebot_fake_test_message import TelebotFakeTestMessage
from deye_registers_holder import DeyeRegistersHolder
from system_time_diff_deye_register import SystemTimeDiffDeyeRegister
from deye_test_helper import get_random_by_register_type

class TelebotRegistersTestModule(TelebotBaseTestModule):
  def __init__(
    self,
    bot: TestableTelebot,
    name: str,
    command: TelebotMenuItem,
    register_creator: Callable[[str], DeyeRegisters],
  ):
    super().__init__(bot)
    self.name = name
    self.command = command
    self.register_creator = register_creator
    self.loggers = DeyeLoggers()
    self.log = logging.getLogger()

  def run_tests(self, servers: List[AioSolarmanServer]):
    users = TelebotUsers()

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

      self.log.info(f'Running module {type(self).__name__}: '
                    f"name = '{self.name}' "
                    f"command = '{self.command}' "
                    f"register_creator = {type(self.register_creator(self.name)).__name__}'")

    holder = self._init_registers(servers)

    time.sleep(1)
    command = f'/{self.command.command.format(self.name)}'

    fake_message = TelebotFakeTestMessage.make(
      text = command,
      user_id = users.allowed_users[0].id,
    )

    self.log.info(f'Run regular command: {command}')
    self.bot.clear_messages()
    self.bot.process_new_messages([fake_message])

    time.sleep(1)
    self._check_results(holder)

    self.log.info(f'Run command from button: {command}')

    fake_query = telebot.types.CallbackQuery(
      id = "fake",
      chat_instance = 'fake',
      json_string = '',
      from_user = fake_message.from_user,
      data = command,
      message = fake_message,
    )

    holder = self._init_registers(servers)
    time.sleep(1)

    self.bot.clear_messages()
    self.bot.process_new_callback_query([fake_query])

    time.sleep(1)
    self._check_results(holder)

  def _init_registers(self, servers: List[AioSolarmanServer]) -> DeyeRegistersHolder:
    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

    registers = self.register_creator(self.name)

    for register in registers.all_registers:
      random_value = get_random_by_register_type(register)
      if random_value is None:
        continue

      for server in servers:
        random_value = get_random_by_register_type(register)
        server.set_register_values(random_value.register.address, random_value.values)

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      register_creator = self.register_creator,
      caching_time = 0,
      socket_timeout = 10,
      name = 'teletest',
    )

    def log_retry(attempt, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying...')

    try:
      holder.read_registers_with_retry(retry_cout = 10, on_retry = log_retry)
    finally:
      holder.disconnect()

    return holder

  def _check_results(self, holder: DeyeRegistersHolder):
    found = True
    for register in holder.all_registers[self.name].all_registers:
      if isinstance(register, SystemTimeDiffDeyeRegister):
        continue

      if not self.bot.is_messages_contains(self.name):
        self.error(f"Messages don't contain expected inverter name '{self.name}'")

      desc = register.description.replace('Inverter ', '')

      suffix = f' {register.suffix}'.rstrip()
      info = f'{desc}: {register.pretty_value}{suffix}'

      if self.bot.is_messages_contains(info):
        self.log.info(f'{info} - OK')
      else:
        self.log.info(f'{info} - FAILED')
        found = False

    if not found:
      self.error('Some registers info not found')
