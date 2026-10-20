import telebot

from enum import Enum, auto
from datetime import date
from http import HTTPStatus
from urllib.parse import urljoin
from typing import List, Union, cast

from env_utils import EnvUtils
from deye_loggers import DeyeLoggers
from button_style import ButtonStyle
from button_node import ButtonNode
from break_button_node import BreakButtonNode
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from statistics_period import StatisticsPeriod
from inverter_energy_statistics_dto import InverterEnergyStatisticsDto
from http_session_singleton_async import HttpSessionSingletonAsync

class PvStatMainPageType(Enum):
  main = auto()

class TelebotMenuPvStatMainPage(TelebotNavigationPage):
  def __init__(self):
    super().__init__()
    self._deye_loggers = DeyeLoggers()
    self._period = next(iter(StatisticsPeriod))
    self._texts: List[telebot.types.InputRichBlock] = []

  @property
  def page_type(self) -> Enum:
    return PvStatMainPageType.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return telebot.types.InputRichMessage(blocks = self._texts)

  async def on_start(self) -> None:
    self._texts = await self._get_telegram_table(period = self._period)

  async def on_auto_update(self, navigator: TelebotPageNavigator) -> None:
    self._texts = await self._get_telegram_table(period = self._period)
    await navigator.update()

  def create_buttons(self) -> None:
    for period in StatisticsPeriod:
      self._create_pv_stat_button(period)

    self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Cancel"), self._handle_cancel)

  def _create_pv_stat_button(self, period: StatisticsPeriod) -> None:
    async def handler(navigator: TelebotPageNavigator) -> None:
      if self._period == period:
        return

      self._period = period
      self._texts = await self._get_telegram_table(period = period)

      await navigator.update()

    style = ButtonStyle.default
    if self._period == period:
      style = ButtonStyle.success

    self.register_button(
      ButtonNode(
        text = period.description,
        style = style,
      ),
      handler,
    )

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop()

  async def _get_telegram_table(
    self,
    period: StatisticsPeriod,
  ) -> List[telebot.types.InputRichBlock]:
    today = date.today()
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

    if len(self._deye_loggers.slaves) < 1:
      raise ValueError("Slave inverters are empty")

    master_stats = dto.energy_statistics.get(self._deye_loggers.master.name)
    slave_stats = dto.energy_statistics.get(self._deye_loggers.slaves[0].name)

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

    rows = [
      ("Value", "kWh", "Percent"),
      ("Total PV production", f"{total_production:.2f}", f"{total_percent:.0f}%"),
      ("Master PV1", f"{master_pv1:.2f}", f"{master_pv1_percent:.0f}%"),
      ("Slave PV1", f"{slave_pv1:.2f}", f"{slave_pv1_percent:.0f}%"),
      ("Master PV2 (South Wall)", f"{master_pv2:.2f}", f"{master_pv2_percent:.0f}%"),
      ("Master Gen (West Wall)", f"{master_gen:.2f}", f"{master_gen_percent:.0f}%"),
      (
        "Master PV2 + Master Gen",
        f"{master_pv2_and_master_gen:.2f}",
        f"{master_pv2_and_master_gen_percent:.0f}%",
      ),
    ]

    cells = [[self._create_cell(
      value = value,
      row = row,
      column = column,
    ) for column, value in enumerate(row_data)] for row, row_data in enumerate(rows)]

    return [
      telebot.types.InputRichBlockParagraph(
        telebot.types.RichTextBold(
          cast(
            telebot.types.RichText,
            f"Statistics for {period.description.lower()} {period_date}:",
          ))),
      telebot.types.InputRichBlockTable(
        cells = cells,
        is_bordered = True,
        is_striped = False,
        is_compact = True,
      )
    ]

  def _create_cell(
    self,
    value: str,
    row: int,
    column: int,
  ) -> telebot.types.RichBlockTableCell:
    return telebot.types.RichBlockTableCell(
      text = cast(telebot.types.RichText, value),
      align = ("center" if row == 0 else "left" if column == 0 else "right"),
      valign = "middle",
      is_header = row == 0,
    )
