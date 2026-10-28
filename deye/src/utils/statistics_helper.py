from datetime import date
from http import HTTPStatus
from logging import Logger
from typing import Optional
from urllib.parse import urljoin

from env_utils import EnvUtils
from deye_loggers import DeyeLoggers
from statistics_period import StatisticsPeriod
from deye_registers_holder_async import DeyeRegistersHolderAsync
from printable_energy_statistics_dto import PrintableEnergyStatisticsDto
from printable_energy_statistics_row_dto import PrintableEnergyStatisticsRowDto
from http_session_singleton_async import HttpSessionSingletonAsync
from inverter_energy_statistics_dto import InverterEnergyStatisticsDto

class StatisticsHelper:
  def __init__(self, logger: Logger):
    self._logger = logger
    self._loggers = DeyeLoggers()

  async def get_production_dto(self, period_date: str) -> InverterEnergyStatisticsDto:
    session = await HttpSessionSingletonAsync.get_session()
    server_url = EnvUtils.get_remote_cache_server_url()
    url = urljoin(server_url, f"/storage/pv-production-{period_date}")

    async with session.get(url) as response:
      # Read response body first to ensure it is always consumed
      payload = await response.text()

      if response.status != HTTPStatus.OK:
        err_str = (f"Failed to fetch production data for {period_date} "
                   f"from {url}, status code: {response.status}")

        self._logger.error(err_str)
        raise ValueError(err_str)

      return InverterEnergyStatisticsDto.from_json(payload)

  def get_energy_stats_dto(
    self,
    dto: InverterEnergyStatisticsDto,
    holder: Optional[DeyeRegistersHolderAsync] = None,
  ) -> PrintableEnergyStatisticsDto:
    if len(self._loggers.slaves) < 1:
      raise ValueError("Slave inverters not found")

    master_stats = dto.energy_statistics.get(self._loggers.master.name)
    slave1 = self._loggers.slaves[0]
    slave_stats = dto.energy_statistics.get(slave1.name)

    if master_stats is None:
      raise ValueError("Master statistics not found")

    if slave_stats is None:
      raise ValueError("Slave statistics not found")

    master_pv1_kw = 0.0
    master_pv2_kw = 0.0
    master_gen_kw = 0.0
    slave_pv1_kw = 0.0
    master_pv2_and_master_gen_kw = 0.0
    total_kw = 0.0

    master_pv1_kwh = round(master_stats.production_pv1, 2)
    master_pv2_kwh = round(master_stats.production_pv2, 2)
    master_gen_kwh = round(master_stats.gen_energy, 2)
    slave_pv1_kwh = round(slave_stats.production_pv1, 2)
    master_pv2_and_master_gen_kwh = round(master_stats.production_pv2 + master_stats.gen_energy, 2)

    total_kwh = round(
        master_stats.production_pv1 + \
        master_stats.production_pv2 + \
        master_stats.gen_energy + \
        slave_stats.production_pv1, 2)

    total_kwh_percent = 0.0
    master_pv1_kwh_percent = 0.0
    master_pv2_kwh_percent = 0.0
    slave_pv1_kwh_percent = 0.0
    master_gen_kwh_percent = 0.0
    master_pv2_and_master_gen_kwh_percent = 0.0

    if total_kwh > 0:
      total_kwh_percent = 100

      if master_pv1_kwh > 0:
        master_pv1_kwh_percent = (master_stats.production_pv1 / total_kwh) * 100

      if master_pv2_kwh > 0:
        master_pv2_kwh_percent = (master_stats.production_pv2 / total_kwh) * 100

      if slave_pv1_kwh > 0:
        slave_pv1_kwh_percent = (slave_stats.production_pv1 / total_kwh) * 100

      if master_gen_kwh > 0:
        master_gen_kwh_percent = (master_stats.gen_energy / total_kwh) * 100

      if master_pv2_and_master_gen_kwh > 0:
        master_pv2_and_master_gen_kwh_percent = (
          (master_stats.production_pv2 + master_stats.gen_energy) / total_kwh) * 100

    if holder is not None:
      master_pv1_kw = holder.master_registers.pv1_power_register.value / 1000
      master_pv2_kw = holder.master_registers.pv2_power_register.value / 1000
      master_gen_kw = holder.master_registers.gen_power_register.value / 1000
      slave_pv1_kw = holder.all_registers[slave1.name].pv1_power_register.value / 1000
      master_pv2_and_master_gen_kw = master_pv2_kw + master_gen_kw
      total_kw = master_pv1_kw + master_pv2_kw + master_gen_kw + slave_pv1_kw

    printable_statistics = [
      PrintableEnergyStatisticsRowDto(
        label = "Total PV production",
        kw = total_kw,
        kwh = total_kwh,
        percent = total_kwh_percent,
      ),
      PrintableEnergyStatisticsRowDto(
        label = "Master PV1",
        kw = master_pv1_kw,
        kwh = master_pv1_kwh,
        percent = master_pv1_kwh_percent,
      ),
      PrintableEnergyStatisticsRowDto(
        label = "Slave PV1",
        kw = slave_pv1_kw,
        kwh = slave_pv1_kwh,
        percent = slave_pv1_kwh_percent,
      ),
      PrintableEnergyStatisticsRowDto(
        label = "Master PV2 (South Wall)",
        kw = master_pv2_kw,
        kwh = master_pv2_kwh,
        percent = master_pv2_kwh_percent,
      ),
      PrintableEnergyStatisticsRowDto(
        label = "Master Gen (West Wall)",
        kw = master_gen_kw,
        kwh = master_gen_kwh,
        percent = master_gen_kwh_percent,
      ),
      PrintableEnergyStatisticsRowDto(
        label = "Master PV2 + Master Gen",
        kw = master_pv2_and_master_gen_kw,
        kwh = master_pv2_and_master_gen_kwh,
        percent = master_pv2_and_master_gen_kwh_percent,
      ),
    ]

    return PrintableEnergyStatisticsDto(printable_statistics = printable_statistics)

  async def get_statistics(self, today: date, period: StatisticsPeriod) -> str:
    period_date = period.get_date_suffix(today)
    dto = await self.get_production_dto(period_date)
    stats_dto = self.get_energy_stats_dto(dto)

    # Calculate dynamic widths based on actual field values
    label_width = max(len(row.label) for row in stats_dto.printable_statistics)
    max_kwh = max((row.kwh for row in stats_dto.printable_statistics), default = 0.0)
    kwh_width = max(4, len(str(int(max_kwh))) + 3)

    lines = [f"Statistics for {period.description.lower()} {period_date}:"]
    for row in stats_dto.printable_statistics:
      lines.append(f"• {row.label:<{label_width}} : {row.kwh:{kwh_width}.2f} kWh ({row.percent:.0f}%)")

    return "\n".join(lines)
