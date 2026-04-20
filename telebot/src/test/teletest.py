import sys
import asyncio
import logging

from typing import List

from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from debug_timer import DebugTimerWithLog
from all_settings_registers import AllSettingsRegisters
from master_settings_registers import MasterSettingsRegisters
from common_utils import CommonUtils
from telebot_constants import TelebotConstants
from telebot_menu_item import TelebotMenuItem
from accumulated_info_registers import AccumulatedInfoRegisters
from slave_info_registers import SlaveInfoRegisters
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from deye_test_helper import DeyeTestHelper
from solarman_test_server import SolarmanTestServer
from forecast_registers import ForecastRegisters
from master_info_registers import MasterInfoRegisters
from telebot_registers_test_module import TelebotRegistersTestModule
from today_stat_registers import TodayStatRegisters
from total_stat_registers import TotalStatRegisters
from telebot_blocked_user_test_module import TelebotBlockedUserTestModule
from telebot_unauthorized_user_test_module import TelebotUnauthorizedUserTestModule
from telebot_unknown_command_test_module import TelebotUnknownCommandTestModule
from telebot_inverter_time_sync_test_module import TelebotInverterTimeSyncTestModule
from telebot_allowed_commands_test_module import TelebotAllowedCommandsTestModule
from telebot_writable_registers_test1_module import TelebotWritableRegistersTest1Module
from telebot_writable_registers_test2_module import TelebotWritableRegistersTest2Module
from telebot_writable_registers_test3_module import TelebotWritableRegistersTest3Module
from telebot_writable_registers_test4_module import TelebotWritableRegistersTest4Module
from telebot_writable_registers_test5_module import TelebotWritableRegistersTest5Module
from telebot_writable_registers_undo_test_module import TelebotWritableRegistersUndoTestModule
from telebot_writable_registers_buttons_test_module import TelebotWritableRegistersButtonsTestModule
from telegram_send_message import Telegram

class TeleTest:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot
    self.loggers = DeyeLoggers()

  async def run_tests(self):
    if not self.loggers.is_test_loggers:
      raise ValueError('Your loggers are not test loggers')

    servers: List[SolarmanTestServer] = []

    for logger in self.loggers.loggers:
      servers.append(
        SolarmanTestServer(
          name = logger.name,
          address = logger.address,
          serial = logger.serial,
          port = logger.port,
        ))

    await self._wait_for_solarman_servers_ready(self.loggers.loggers)

    log = logging.getLogger()
    modules = self._get_test_modules(self.bot)

    try:
      for module in modules:
        self._clear_data(servers, log)
        log.info(f'Running module {type(module).__name__}...')
        with DebugTimerWithLog(type(module).__name__):
          await module.run_tests(servers)
        log.info(f'Module {type(module).__name__} done successfully')
      log.info(DeyeTestHelper.test_success_str)
    except Exception as e:
      info = ''
      if isinstance(module, TelebotRegistersTestModule):
        info = (f'(name = {module.name}, command = {module.command}, '
                f'register_creator = {type(module.register_creator(module.name)).__name__})')
      msg = f'An exception occurred while running {type(module).__name__}{info}: {str(e)}'
      log.info(msg)
      await asyncio.sleep(1)
      Telegram.send_private_telegram_message(f'{CommonUtils.large_red_circle_emoji} '
                                             f'<b>Telebot test failed</b> while running '
                                             f'{type(module).__name__}{info}: {str(e)}')
      sys.exit(1)

  def _clear_data(self, servers: List[SolarmanTestServer], log: logging.Logger):
    self.bot.clear_messages()
    for server in servers:
      server.clear_registers()
      server.clear_registers_status()

  def _get_test_modules(self, bot: TestableTelebot) -> List[TelebotBaseTestModule]:
    modules: List[TelebotBaseTestModule] = [
      TelebotBlockedUserTestModule(bot),
      TelebotUnauthorizedUserTestModule(bot),
      TelebotUnknownCommandTestModule(bot),
      TelebotAllowedCommandsTestModule(bot),
      TelebotWritableRegistersTest1Module(bot),
      TelebotWritableRegistersTest2Module(bot),
      TelebotWritableRegistersTest3Module(bot),
      TelebotWritableRegistersTest4Module(bot),
      TelebotWritableRegistersTest5Module(bot),
      TelebotWritableRegistersUndoTestModule(bot),
      TelebotWritableRegistersButtonsTestModule(bot),
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
        title = TelebotConstants.today_stat_title,
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.master.name,
        command = TelebotMenuItem.deye_master_today_stat,
        register_creator = lambda prefix: TodayStatRegisters(prefix),
        title = TelebotConstants.today_stat_title,
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_all_total_stat,
        register_creator = lambda prefix: TotalStatRegisters(prefix),
        title = TelebotConstants.total_stat_title,
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.master.name,
        command = TelebotMenuItem.deye_master_total_stat,
        register_creator = lambda prefix: TotalStatRegisters(prefix),
        title = TelebotConstants.total_stat_title,
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
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_battery_forecast_by_percent,
        register_creator = lambda prefix: ForecastRegisters(prefix),
      ),
      TelebotRegistersTestModule(
        bot,
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_battery_forecast_by_time,
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
          title = TelebotConstants.today_stat_title,
        ),
        TelebotRegistersTestModule(
          bot,
          name = logger.name,
          command = TelebotMenuItem.deye_slave_total_stat,
          register_creator = lambda prefix: TotalStatRegisters(prefix),
          title = TelebotConstants.total_stat_title,
        ),
      ])

    return modules

  async def _wait_for_solarman_servers_ready(
    self,
    loggers: List[DeyeLogger],
    timeout: float = 5,
  ) -> bool:
    """
    Wait until all solarman server ports for all loggers are open.
    """
    logger_tools = logging.getLogger()
    logger_tools.info(f"Waiting for {len(loggers)} solarman server(s) to be ready...")

    async def check_single_logger(deye_logger: DeyeLogger) -> bool:
      """
      Internal helper to check one specific logger with a timeout.
      """
      start_time = asyncio.get_running_loop().time()
      while asyncio.get_running_loop().time() - start_time < timeout:
        try:
          # Try to open a connection to the specific logger's address and port
          reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
              deye_logger.address,
              deye_logger.port,
            ),
            timeout = 0.5,
          )
          writer.close()
          await writer.wait_closed()
          return True
        except (ConnectionRefusedError, OSError, asyncio.TimeoutError):
          await asyncio.sleep(0.2)

      logger_tools.error(
        f"Logger '{deye_logger.name}' ({deye_logger.address}:{deye_logger.port}) did not become ready.")
      return False

    # Run all checks concurrently
    results = await asyncio.gather(*(check_single_logger(l) for l in loggers))

    # Return True only if ALL loggers are ready
    if all(results):
      logger_tools.info("All solarman servers are ready!")
      return True

    return False
