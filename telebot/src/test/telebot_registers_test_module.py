from typing import Callable, List

from telebot_menu_item import TelebotMenuItem
from telebot_test_users import TelebotTestUsers
from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_registers import DeyeRegisters
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder import DeyeRegistersHolder
from deye_test_helper import DeyeTestHelper
from deye_exceptions import DeyeKnownException

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

  @property
  def description(self) -> str:
    return f"{self.command.command.format(self.name).replace('_', ' ')} test"

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    user = TelebotTestUsers().test_user1

    self.log.info(f'Running module {type(self).__name__}: '
                  f"name = '{self.name}' "
                  f"command = '{self.command}' "
                  f"register_creator = {type(self.register_creator(self.name)).__name__}'")

    command = f'/{self.command.command.format(self.name)}'

    self.log.info(f'Run regular command: {command}')

    holder = self._init_registers(servers)
    self.send_text(user, command)
    self.call_with_retry(self._check_results, holder)

    self.log.info(f'Run command from button: {command}')

    self.bot.clear_messages()

    holder = self._init_registers(servers)
    self.send_button_click(user, command)
    self.call_with_retry(self._check_results, holder)

  def _init_registers(self, servers: List[SolarmanServer]) -> DeyeRegistersHolder:
    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

    registers = self.register_creator(self.name)

    for register in registers.all_registers:
      random_value = DeyeTestHelper.get_random_by_register_type(register)
      if random_value is None:
        continue

      for server in servers:
        random_value = DeyeTestHelper.get_random_by_register_type(register)
        if random_value is None:
          self.error(f"Unable to get random value for register '{register.name}' with type {type(register).__name__}")
          break
        server.set_register_values(random_value.register.addresses, random_value.values)

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      register_creator = self.register_creator,
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.read_registers()
    finally:
      holder.disconnect()

    return holder

  def _check_results(self, holder: DeyeRegistersHolder):
    pattern = f'inverter: {self.name}|{self.name} settings:'
    if not self.bot.is_messages_contains_regex(pattern):
      raise DeyeKnownException(f"Messages don't contain expected inverter name '{pattern}'")

    found = True
    for register in holder.all_registers[self.name].all_registers:
      desc = register.description.replace('Inverter ', '')
      suffix = f' {register.suffix}'.rstrip()
      info = f'{desc}: {register.pretty_value}{suffix}'

      if self.bot.is_messages_contains(info):
        self.log.info(f'{info} - OK')
      else:
        self.log.info(f'{info} - FAILED')
        found = False

    if not found:
      self.error('Some registers or values not found')
    else:
      self.log.info('All registers and values found')
