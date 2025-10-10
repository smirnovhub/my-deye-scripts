import datetime
import logging

import sys
import time

from typing import List

from deye_loggers import DeyeLoggers
from all_settings_registers import AllSettingsRegisters
from master_settings_registers import MasterSettingsRegisters
from telebot_menu_item import TelebotMenuItem
from accumulated_info_registers import AccumulatedInfoRegisters
from slave_info_registers import SlaveInfoRegisters
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from solarman_server import SolarmanServer
from forecast_registers import ForecastRegisters
from master_info_registers import MasterInfoRegisters
from telebot_registers_test_module import TelebotRegistersTestModule
from today_stat_registers import TodayStatRegisters
from total_stat_registers import TotalStatRegisters
from telebot_unauthorized_user_test_module import TelebotUnauthorizedUserTestModule
from telebot_unknown_command_test_module import TelebotUnknownCommandTestModule
from telebot_inverter_time_sync_test_module import TelebotInverterTimeSyncTestModule
from telebot_allowed_commands_test_module import TelebotAllowedCommandsTestModule
from telebot_writable_registers_test1_module import TelebotWritableRegistersTest1Module
from telebot_writable_registers_test2_module import TelebotWritableRegistersTest2Module
from telebot_writable_registers_test3_module import TelebotWritableRegistersTest3Module
from telebot_writable_registers_undo_test_module import TelebotWritableRegistersUndoTestModule
from telebot_send_message import send_private_telegram_message
from deye_utils import format_timedelta
from deye_test_helper import test_success_str

from common_utils import (
  large_green_circle_emoji,
  large_red_circle_emoji,
)

class TeleTest:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot
    self.loggers = DeyeLoggers()

  def run_tests(self):
    if not self.loggers.is_test_loggers:
      print('Your loggers are not test loggers')
      return

    servers: List[SolarmanServer] = []

    for logger in self.loggers.loggers:
      servers.append(
        SolarmanServer(
          name = logger.name,
          address = logger.address,
          serial = logger.serial,
          port = logger.port,
        ))

    log = logging.getLogger()
    modules = self._get_test_modules(self.bot)

    try:
      for i, module in enumerate(modules):
        time.sleep(1)
        start_time = datetime.datetime.now()
        self._clear_data(servers, log)
        module.run_tests(servers)
        delta = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
        send_private_telegram_message(f'{large_green_circle_emoji} [{i + 1}/{len(modules)}] '
                                      f'<b>Success</b> after {delta}: {module.description}')
      print(test_success_str)
      log.info(test_success_str)
    except Exception as e:
      info = ''
      if isinstance(module, TelebotRegistersTestModule):
        info = (f'(name = {module.name}, command = {module.command}, '
                f'register_creator = {type(module.register_creator(module.name)).__name__})')
      msg = f'An exception occurred while running {type(module).__name__}{info}: {str(e)}'
      print(msg)
      log.info(msg)

      delta = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
      send_private_telegram_message(f'{large_red_circle_emoji} [{i + 1}/{len(modules)}] '
                                    f'<b>Failed</b> after {delta}: {module.description}: {msg}')
      sys.exit(1)

  def _clear_data(self, servers: List[SolarmanServer], log: logging.Logger):
    self.bot.clear_messages()
    time.sleep(3)

    if not self.bot.is_messages_empty():
      print('Error: still receiving messages from previous module. Exiting...')
      log.info('Error: still receiving messages from previous module. Exiting...')
      sys.exit(1)

    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

  def _get_test_modules(self, bot: TestableTelebot) -> List[TelebotBaseTestModule]:
    modules: List[TelebotBaseTestModule] = [
      TelebotUnauthorizedUserTestModule(bot),
      TelebotUnknownCommandTestModule(bot),
      TelebotAllowedCommandsTestModule(bot),
      TelebotWritableRegistersTest1Module(bot),
      TelebotWritableRegistersTest2Module(bot),
      TelebotWritableRegistersTest3Module(bot),
      TelebotWritableRegistersUndoTestModule(bot),
      TelebotInverterTimeSyncTestModule(bot),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_all_info,
        register_creator = lambda prefix: AccumulatedInfoRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.master.name,
        command = TelebotMenuItem.deye_master_info,
        register_creator = lambda prefix: MasterInfoRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_all_today_stat,
        register_creator = lambda prefix: TodayStatRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.master.name,
        command = TelebotMenuItem.deye_master_today_stat,
        register_creator = lambda prefix: TodayStatRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_all_total_stat,
        register_creator = lambda prefix: TotalStatRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.master.name,
        command = TelebotMenuItem.deye_master_total_stat,
        register_creator = lambda prefix: TotalStatRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_all_settings,
        register_creator = lambda prefix: AllSettingsRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.master.name,
        command = TelebotMenuItem.deye_master_settings,
        register_creator = lambda prefix: MasterSettingsRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_battery_forecast,
        register_creator = lambda prefix: ForecastRegisters(prefix),
      ),
    ]

    for logger in self.loggers.slaves:
      modules.extend([
        TelebotRegistersTestModule(
          bot,
          name = logger.name,
          command = TelebotMenuItem.deye_slave_info,
          register_creator = lambda prefix: SlaveInfoRegisters(prefix),
        ),
        TelebotRegistersTestModule(
          bot,
          name = logger.name,
          command = TelebotMenuItem.deye_slave_today_stat,
          register_creator = lambda prefix: TodayStatRegisters(prefix),
        ),
        TelebotRegistersTestModule(
          bot,
          name = logger.name,
          command = TelebotMenuItem.deye_slave_total_stat,
          register_creator = lambda prefix: TotalStatRegisters(prefix),
        ),
      ])

    return modules
