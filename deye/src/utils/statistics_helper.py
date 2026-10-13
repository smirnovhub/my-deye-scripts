import re

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

  def get_clean_statistics(self, stat: str) -> str:
    # Removes <b>, </b>, <pre>, </pre> case-insensitively
    return re.sub(r"</?(b|pre)>", "", stat, flags = re.IGNORECASE)

  async def get_statistics_for_telegram(self, today: date, period: StatisticsPeriod) -> str:
    period_date = period.get_date_suffix(today)
    server_url = EnvUtils.get_remote_cache_server_url()
    session = await HttpSessionSingletonAsync.get_session()
    url = urljoin(server_url, f"/storage/pv-production-{period_date}")

    async with session.get(url) as response:
      if response.status != HTTPStatus.OK:
        err_str = f"Failed to fetch production data for {period_date} from {url}, status code: {response.status}"
        self._logger.error(err_str)

        # Read the entire response body to allow aiohttp to reuse the connection (Keep-Alive)
        await response.read()

        raise ValueError(err_str)

      payload = await response.text()
      dto = InverterEnergyStatisticsDto.from_json(payload)

    master_pv2 = 0.0
    master_gen = 0.0

    for name, stats in dto.energy_statistics.items():
      if name == self._loggers.master.name:
        master_pv2 = stats.production_pv2
        master_gen = stats.gen_energy
        break

    total_production = sum(stats.production_pv1 + stats.production_pv2 + stats.gen_energy
                           for stats in dto.energy_statistics.values())

    if total_production > 0:
      pv2_pct = (master_pv2 / total_production) * 100
      gen_pct = (master_gen / total_production) * 100
      pv2_gen_pct = ((master_pv2 + master_gen) / total_production) * 100
    else:
      pv2_pct = gen_pct = pv2_gen_pct = 0.0

    return (f"<b>Statistics for {period.description.lower()} {period_date}:</b>\n<pre>"
            f"• Total PV production     : {total_production:.2f} kWh (100%)\n"
            f"• Master PV2 (South Wall) : {master_pv2:.2f} kWh ({pv2_pct:.0f}%)\n"
            f"• Master Gen (West Wall)  : {master_gen:.2f} kWh ({gen_pct:.0f}%)\n"
            f"• Master PV2 + Master Gen : {master_pv2 + master_gen:.2f} kWh ({pv2_gen_pct:.0f}%)</pre>")
