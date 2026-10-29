import copy

import telebot

from dataclasses import asdict
from typing import Any, Sequence, cast

from deye_logger import DeyeLogger
from common_utils import CommonUtils
from deye_register import DeyeRegister
from time_of_use_data import TimeOfUseData
from deye_custom_single_registers import DeyeCustomSingleRegisters
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder_async import DeyeRegistersHolderAsync

class TimeOfUseHelper:
  @staticmethod
  def check_bounds(collection: Sequence[Any], index: int) -> None:
    count = len(collection)
    if not (0 <= index < count):
      raise RuntimeError(f"Index {index} is out of bounds (0 to {count - 1})")

  @staticmethod
  def check_upper_bounds(collection: Sequence[Any], index: int) -> None:
    count = len(collection)
    if index >= count:
      raise RuntimeError(f"Index {index} should be less than {count - 1}")

  @staticmethod
  async def write_time_of_use(
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
    master_logger: DeyeLogger,
  ) -> None:
    if not isinstance(tou_register.value, TimeOfUseData):
      raise RuntimeError(f"Register value type should be {TimeOfUseData.__name__}, but "
                         f"{type(tou_register.value).__name__} received")

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolderAsync(
      loggers = [master_logger],
      register_creator = lambda prefix: DeyeCustomSingleRegisters(tou_register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      await holder.write_register(tou_register, tou_data)
    finally:
      holder.disconnect()

  @staticmethod
  def get_cleared_unchanged_data(
    data_to_clear: TimeOfUseData,
    original_data: TimeOfUseData,
  ) -> TimeOfUseData:
    data = copy.deepcopy(data_to_clear)

    # Convert parts to dicts for simple comparison
    # Use asdict to compare the entire content, not object references
    if asdict(data.charges) == asdict(original_data.charges):
      data.charges.values = []

    if asdict(data.times) == asdict(original_data.times):
      data.times.values = []

    if asdict(data.powers) == asdict(original_data.powers):
      data.powers.values = []

    if asdict(data.socs) == asdict(original_data.socs):
      data.socs.values = []

    if asdict(data.weeks) == asdict(original_data.weeks):
      data.weeks.values = []

    return data

  @staticmethod
  def get_time_of_use_as_rich_message(
    tou_data: TimeOfUseData,
    suffx: str = "",
  ) -> telebot.types.InputRichMessage:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    def create_cell(
      value: str,
      row: int,
      column: int,
    ) -> telebot.types.RichBlockTableCell:
      return telebot.types.RichBlockTableCell(
        text = cast(telebot.types.RichText, value),
        is_header = row == 0,
        align = "center",
        valign = "middle",
      )

    # Header title with enabled status sign
    header_text = f"{sign(tou_data.week.enabled)} Time of Use schedule:"
    if suffx:
      header_text += f" {suffx}"

    # 1. Days of the week table data
    days_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days_values = [
      sign(tou_data.week.monday),
      sign(tou_data.week.tuesday),
      sign(tou_data.week.wednesday),
      sign(tou_data.week.thursday),
      sign(tou_data.week.friday),
      sign(tou_data.week.saturday),
      sign(tou_data.week.sunday),
    ]

    days_rows = [days_headers, days_values]

    days_cells = [[
      create_cell(
        value = value,
        row = row_idx,
        column = col_idx,
      ) for col_idx, value in enumerate(row_data)
    ] for row_idx, row_data in enumerate(days_rows)]

    # 2. Schedule table data
    schedule_headers = ["Grid", "Gen", "Start", "End", "Power", "Batt"]
    schedule_rows = [schedule_headers]

    charges = tou_data.charges.values
    times = tou_data.times.values
    powers = tou_data.powers.values
    socs = tou_data.socs.values

    count = len(times)
    for i in range(count):
      curr_charge = charges[i]
      curr_time = times[i]
      # Next time for the interval end, wrapping around to the first element
      next_time = times[(i + 1) % count]
      curr_power = powers[i]
      curr_soc = socs[i]

      schedule_rows.append([
        sign(curr_charge.grid_charge),
        sign(curr_charge.gen_charge),
        f"{curr_time.hour:02d}:{curr_time.minute:02d}",
        f"{next_time.hour:02d}:{next_time.minute:02d}",
        str(curr_power),
        f"{curr_soc}%",
      ])

    schedule_cells = [[
      create_cell(
        value = value,
        row = row_idx,
        column = col_idx,
      ) for col_idx, value in enumerate(row_data)
    ] for row_idx, row_data in enumerate(schedule_rows)]

    return telebot.types.InputRichMessage(blocks = [
      telebot.types.InputRichBlockParagraph(telebot.types.RichTextBold(cast(
        telebot.types.RichText,
        header_text,
      ))),
      telebot.types.InputRichBlockTable(
        cells = days_cells,
        is_bordered = True,
        is_striped = False,
        is_compact = True,
      ),
      telebot.types.InputRichBlockTable(
        cells = schedule_cells,
        is_bordered = True,
        is_striped = False,
        is_compact = True,
      ),
    ])
