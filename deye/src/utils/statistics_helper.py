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

  async def get_energy_statistics_dto(self, period_date: str) -> InverterEnergyStatisticsDto:
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

  def get_printable_statistics_dto(
    self,
    dto: InverterEnergyStatisticsDto,
    holder: Optional[DeyeRegistersHolderAsync] = None,
  ) -> PrintableEnergyStatisticsDto:
    if len(self._loggers.slaves) < 1:
      raise ValueError("Slave inverters not found")

    master_stats = dto.energy_statistics.get(self._loggers.master.name)
    slave1 = self._loggers.slaves[0]
    slave1_stats = dto.energy_statistics.get(slave1.name)

    if master_stats is None:
      raise ValueError("Master statistics not found")

    if slave1_stats is None:
      raise ValueError("Slave statistics not found")

    total_kwh = master_stats.production_pv1 + \
      slave1_stats.production_pv1 + \
      master_stats.production_pv2 + \
      master_stats.gen_energy

    rounding_digits = 2
    total_kwh_rounded = round(total_kwh, rounding_digits)

    def calc_percent(val: float) -> float:
      if total_kwh_rounded > 0 and round(val, rounding_digits) > 0:
        return (val / total_kwh) * 100
      else:
        return 0.0

    master_pv1 = PrintableEnergyStatisticsRowDto(
      label = "Master PV1",
      kw = 0.0,
      kwh = master_stats.production_pv1,
      percent = calc_percent(master_stats.production_pv1),
    )

    slave1_pv1 = PrintableEnergyStatisticsRowDto(
      label = "Slave PV1",
      kw = 0.0,
      kwh = slave1_stats.production_pv1,
      percent = calc_percent(slave1_stats.production_pv1),
    )

    master_pv2 = PrintableEnergyStatisticsRowDto(
      label = "Master PV2 (South Wall)",
      kw = 0.0,
      kwh = master_stats.production_pv2,
      percent = calc_percent(master_stats.production_pv2),
    )

    master_gen = PrintableEnergyStatisticsRowDto(
      label = "Master Gen (West Wall)",
      kw = 0.0,
      kwh = master_stats.gen_energy,
      percent = calc_percent(master_stats.gen_energy),
    )

    if holder is not None:
      master_pv1.kw = holder.master_registers.pv1_power_register.value / 1000
      slave1_pv1.kw = holder.all_registers[slave1.name].pv1_power_register.value / 1000
      master_pv2.kw = holder.master_registers.pv2_power_register.value / 1000
      master_gen.kw = holder.master_registers.gen_power_register.value / 1000

    total_production = master_pv1 + slave1_pv1 + master_pv2 + master_gen
    total_production.label = "Total PV production"
    total_production.percent = 100.0 if total_kwh_rounded > 0 else 0.0

    master_pv1_and_slave1_pv1 = master_pv1 + slave1_pv1
    master_pv1_and_slave1_pv1.label = "Master PV1 + Slave PV1"

    master_pv2_and_master_gen = master_pv2 + master_gen
    master_pv2_and_master_gen.label = "Master PV2 + Master Gen"

    return PrintableEnergyStatisticsDto(printable_statistics = [
      total_production,
      master_pv1,
      slave1_pv1,
      master_pv1_and_slave1_pv1,
      master_pv2,
      master_gen,
      master_pv2_and_master_gen,
    ])

  async def get_printable_statistics(self, today: date, period: StatisticsPeriod) -> str:
    period_date = period.get_date_suffix(today)
    dto = await self.get_energy_statistics_dto(period_date)
    stats_dto = self.get_printable_statistics_dto(dto)

    # Calculate dynamic widths based on actual field values
    label_width = max(len(row.label) for row in stats_dto.printable_statistics)
    max_kwh = max((row.kwh for row in stats_dto.printable_statistics), default = 0.0)
    kwh_width = max(4, len(str(int(max_kwh))) + 3)

    lines = [f"Statistics for {period.description.lower()} {period_date}:"]
    for row in stats_dto.printable_statistics:
      lines.append(f"• {row.label:<{label_width}} : {row.kwh:{kwh_width}.2f} kWh ({row.percent:.0f}%)")

    return "\n".join(lines)
