from datetime import datetime
from typing import List, Optional

from telebot_menu_item import TelebotMenuItem
from telebot_test_users import TelebotTestUsers
from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_registers_factory import DeyeRegistersFactory
from deye_test_helper import get_random_by_register_type
from telebot_constants import inverter_system_time_too_big_difference_sec

from deye_utils import (
  get_current_time,
  time_format_str,
)

class TelebotInverterTimeSyncTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)
    self.registers = DeyeRegistersFactory.create_registers()

  def run_tests(self, servers: List[SolarmanServer]):
    user = TelebotTestUsers().test_user1

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

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
    master_server.set_register_values(register.addresses, rnd.values)

    date_time = datetime.strptime(rnd.value, time_format_str)
    time_diff = date_time - get_current_time()
    diff_seconds = int(abs(time_diff.total_seconds()))

    command = f'/{TelebotMenuItem.deye_sync_time.command}'

    self.log.info(f'Run regular command: {command}')

    self.send_text(user, command)

    if diff_seconds > inverter_system_time_too_big_difference_sec:
      self.wait_for_text_regex(f'.*The difference is about {diff_seconds} seconds'
                               '.+Are you sure to sync inverter time.*')

      self.log.info(f"Replying 'yes' for time sync confirmation...")
      self.send_text(user, 'yes')

    changed_to = get_current_time().strftime(time_format_str)
    changed_pattern = (rf'{register.description}.+changed '
                       f'from {rnd.value} '
                       f'to {changed_to}')

    self.wait_for_text_regex(changed_pattern)
    self.wait_for_server_changes(master_server, register)

    self.log.info(f'Run command from button: {command}')

    self.bot.clear_messages()

    master_server.clear_registers()
    master_server.clear_registers_status()

    rnd = get_random_by_register_type(register)
    self.log.info(f'Setting time to server: {rnd.value}')
    master_server.set_register_values(register.addresses, rnd.values)

    date_time = datetime.strptime(rnd.value, time_format_str)
    time_diff = date_time - get_current_time()
    diff_seconds = int(abs(time_diff.total_seconds()))

    self.send_button_click(user, command)

    if diff_seconds > inverter_system_time_too_big_difference_sec:
      self.wait_for_text_regex(f'.*The difference is about {diff_seconds} seconds'
                               '.+Are you sure to sync inverter time.*')

      self.log.info(f"Replying 'yes' for time sync confirmation...")
      self.send_text(user, 'yes')

    changed_pattern = (rf'{register.description}.+changed '
                       f'from {rnd.value} '
                       f'to {changed_to}')

    self.wait_for_text_regex(changed_pattern)
    self.wait_for_server_changes(master_server, register)

    self.log.info('Time change found. Everything looks good')
    self.log.info(f'Module {type(self).__name__} done successfully')
