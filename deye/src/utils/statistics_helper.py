from datetime import date
from http import HTTPStatus
from logging import Logger
from urllib.parse import urljoin

from deye_loggers import DeyeLoggers
from env_utils import EnvUtils
from http_session_singleton_async import HttpSessionSingletonAsync
from inverter_energy_statistics_dto import InverterEnergyStatisticsDto
from statistics_period import StatisticsPeriod

class StatisticsHelper:
  def __init__(self, logger: Logger):
    self._logger = logger
    self._loggers = DeyeLoggers()

  async def get_statistics(self, today: date, period: StatisticsPeriod) -> str:
    period_date = period.get_date_suffix(today)
    server_url = EnvUtils.get_remote_cache_server_url()
    session = await HttpSessionSingletonAsync.get_session()
    url = urljoin(server_url, f"/storage/pv-production-{period_date}")

    async with session.get(url) as response:
      # Read response body first to ensure it is always consumed
      payload = await response.text()

      if response.status != HTTPStatus.OK:
        err_str = (f"Failed to fetch production data for {period_date} "
                   f"from {url}, status code: {response.status}")
        self._logger.error(err_str)
        raise ValueError(err_str)

      dto = InverterEnergyStatisticsDto.from_json(payload)

    master_pv1 = 0.0
    master_pv2 = 0.0
    master_gen = 0.0
    slave_pv1 = 0.0
    master_pv2_and_master_gen = 0.0

    total_percent = 0
    master_pv1_percent = 0
    master_pv2_percent = 0
    slave_pv1_percent = 0
    master_gen_percent = 0
    master_pv2_and_master_gen_percent = 0

    if len(self._loggers.slaves) < 1:
      raise ValueError("Slave inverters are empty")

    master_stats = dto.energy_statistics.get(self._loggers.master.name)
    slave_stats = dto.energy_statistics.get(self._loggers.slaves[0].name)

    if master_stats is None:
      raise ValueError("Master statistics not found")

    if slave_stats is None:
      raise ValueError("Slave statistics not found")

    master_pv1 = round(master_stats.production_pv1, 2)
    master_pv2 = round(master_stats.production_pv2, 2)
    master_gen = round(master_stats.gen_energy, 2)
    slave_pv1 = round(slave_stats.production_pv1, 2)
    master_pv2_and_master_gen = round(master_stats.production_pv2 + master_stats.gen_energy, 2)

    total_production = round(
        master_stats.production_pv1 + \
        master_stats.production_pv2 + \
        master_stats.gen_energy + \
        slave_stats.production_pv1, 2)

    if total_production > 0:
      total_percent = 100

      if master_pv1 > 0:
        master_pv1_percent = (master_stats.production_pv1 / total_production) * 100

      if master_pv2 > 0:
        master_pv2_percent = (master_stats.production_pv2 / total_production) * 100

      if slave_pv1 > 0:
        slave_pv1_percent = (slave_stats.production_pv1 / total_production) * 100

      if master_gen > 0:
        master_gen_percent = (master_stats.gen_energy / total_production) * 100

      if master_pv2_and_master_gen > 0:
        master_pv2_and_master_gen_percent = (
          (master_stats.production_pv2 + master_stats.gen_energy) / total_production) * 100

    return (
      f"Statistics for {period.description.lower()} {period_date}:\n"
      f"• Total PV production     : {total_production:.2f} kWh ({total_percent:.0f}%)\n"
      f"• Master PV1              : {master_pv1:.2f} kWh ({master_pv1_percent:.0f}%)\n"
      f"• Slave PV1               : {slave_pv1:.2f} kWh ({slave_pv1_percent:.0f}%)\n"
      f"• Master PV2 (South Wall) : {master_pv2:.2f} kWh ({master_pv2_percent:.0f}%)\n"
      f"• Master Gen (West Wall)  : {master_gen:.2f} kWh ({master_gen_percent:.0f}%)\n"
      f"• Master PV2 + Master Gen : {master_pv2_and_master_gen:.2f} kWh ({master_pv2_and_master_gen_percent:.0f}%)")
