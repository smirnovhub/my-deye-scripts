import logging

from typing import List

from deye_loggers import DeyeLoggers
from telebot_menu_item import TelebotMenuItem
from accumulated_info_registers import AccumulatedInfoRegisters
from slave_info_registers import SlaveInfoRegisters
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot
from solarman_server import AioSolarmanServer
from forecast_registers import ForecastRegisters
from master_info_registers import MasterInfoRegisters
from telebot_registers_test_module import TelebotRegistersTestModule
from today_stat_registers import TodayStatRegisters
from total_stat_registers import TotalStatRegisters
from telebot_inverter_time_sync_test_module import TelebotInverterTimeSyncTestModule
from telebot_writable_registers_test_module import TelebotWritableRegistersTestModule

class TeleTest:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot
    self.loggers = DeyeLoggers()

  def run_tests(self):
    if not self.loggers.is_test_loggers:
      print('Your loggers are not test loggers')
      return

    logging.basicConfig(
      filename = 'telebot.log',
      filemode = 'w',
      level = logging.INFO,
      format = "[%(asctime)s] [%(levelname)s] %(message)s",
      datefmt = "%Y-%m-%d %H:%M:%S",
    )

    servers: List[AioSolarmanServer] = []

    for logger in self.loggers.loggers:
      server = AioSolarmanServer(
        name = logger.name,
        address = logger.address,
        serial = logger.serial,
        port = logger.port,
      )

      servers.append(server)

    log = logging.getLogger()

    try:
      for module in self._get_test_modules(self.bot):
        module.run_tests(servers)
      print('All tests passed')
      log.info('All tests passed')
    except Exception as e:
      info = ''
      if isinstance(module, TelebotRegistersTestModule):
        info = (f'(name = {module.name}, command = {module.command}, '
                f'register_creator = {type(module.register_creator(module.name)).__name__})')
      msg = f'An exception occurred while running {type(module).__name__}{info}: {str(e)}'
      print(msg)
      log.info(msg)

  def _get_test_modules(self, bot: TestableTelebot) -> List[TelebotBaseTestModule]:
    modules: List[TelebotBaseTestModule] = [
      TelebotWritableRegistersTestModule(bot),
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
        name = self.loggers.accumulated_registers_prefix,
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
        name = self.loggers.accumulated_registers_prefix,
        command = TelebotMenuItem.deye_master_total_stat,
        register_creator = lambda prefix: TotalStatRegisters(prefix),
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
