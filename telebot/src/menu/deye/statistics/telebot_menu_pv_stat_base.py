import telebot

from http import HTTPStatus
from urllib.parse import urljoin
from telebot import types
from typing import List, cast
from datetime import date

from env_utils import EnvUtils
from telebot_async_runner import TelebotAsyncRunner
from telebot_command_choice import CommandChoice
from telebot_menu_item import TelebotMenuItem
from statistics_period import StatisticsPeriod
from inverter_energy_statistics_dto import InverterEnergyStatisticsDto
from http_session_singleton_async import HttpSessionSingletonAsync
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuPvStatBase(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
    stat_command: TelebotMenuItem,
    stat_period: StatisticsPeriod,
  ):
    super().__init__(bot = bot, runner = runner)
    self._stat_command = stat_command
    self._stat_period = stat_period

  @property
  def command(self) -> TelebotMenuItem:
    return self._stat_command

  async def process_message(self, message: telebot.types.Message) -> None:
    choices = {
      TelebotMenuItem.deye_pv_stat_day.description: f"/{TelebotMenuItem.deye_pv_stat_day.command}",
      TelebotMenuItem.deye_pv_stat_month.description: f"/{TelebotMenuItem.deye_pv_stat_month.command}",
      TelebotMenuItem.deye_pv_stat_year.description: f"/{TelebotMenuItem.deye_pv_stat_year.command}",
    }

    try:
      table = await self._get_telegram_table(date.today(), self._stat_period)
    except Exception as e:
      CommandChoice.ask_command_choice(
        bot = self.bot,
        chat_id = message.chat.id,
        text = str(e),
        options = choices,
        max_per_row = 2,
      )
      return

    CommandChoice.ask_rich_command_choice(
      bot = self.bot,
      chat_id = message.chat.id,
      rich_message = types.InputRichMessage(blocks = table),
      options = choices,
      max_per_row = 2,
    )

  async def _get_telegram_table(
    self,
    today: date,
    period: StatisticsPeriod,
  ) -> List[types.InputRichBlock]:
    period_date = period.get_date_suffix(today)
    server_url = EnvUtils.get_remote_cache_server_url()
    session = await HttpSessionSingletonAsync.get_session()
    url = urljoin(server_url, f"/storage/pv-production-{period_date}")

    async with session.get(url) as response:
      if response.status != HTTPStatus.OK:
        err_str = (f"Failed to fetch production data for {period_date} "
                   f"from {url}, status code: {response.status}")
        self.logger.error(err_str)
        raise ValueError(err_str)

      payload = await response.text()
      dto = InverterEnergyStatisticsDto.from_json(payload)

    master_pv2 = 0.0
    master_gen = 0.0

    for name, stats in dto.energy_statistics.items():
      if name == self.loggers.master.name:
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

    total_percent = "100%" if total_production >= 0.005 else "0%"

    rows = [
      ("Value", "kWh", "%"),
      ("Total PV production", f"{total_production:.2f}", total_percent),
      ("Master PV2 (South Wall)", f"{master_pv2:.2f}", f"{pv2_pct:.0f}%"),
      ("Master Gen (West Wall)", f"{master_gen:.2f}", f"{gen_pct:.0f}%"),
      (
        "Master PV2 + Master Gen",
        f"{master_pv2 + master_gen:.2f}",
        f"{pv2_gen_pct:.0f}%",
      ),
    ]

    cells = [[
      types.RichBlockTableCell(
        text = cast(types.RichText, value),
        align = "center" if row_index == 0 else ("left" if column == 0 else "right"),
        valign = "middle",
        is_header = (row_index == 0),
      ) for column, value in enumerate(row)
    ] for row_index, row in enumerate(rows)]

    return [
      types.InputRichBlockParagraph(
        types.RichTextBold(cast(
          types.RichText,
          f"Statistics for {period.description.lower()} {period_date}:",
        ))),
      types.InputRichBlockTable(
        cells = cells,
        is_bordered = True,
        is_striped = False,
        is_compact = True,
      )
    ]
