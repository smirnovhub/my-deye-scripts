from dataclasses import asdict
from typing import Any, Sequence

from deye_logger import DeyeLogger
from common_utils import CommonUtils
from deye_register import DeyeRegister
from time_of_use_data import TimeOfUseData
from custom_single_registers import CustomSingleRegisters
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
      register_creator = lambda prefix: CustomSingleRegisters(tou_register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      await holder.write_register(tou_register, tou_data)
    finally:
      holder.disconnect()

  @staticmethod
  def clear_unchanged_data(
    data_to_clear: TimeOfUseData,
    original_data: TimeOfUseData,
  ) -> None:
    # Convert parts to dicts for simple comparison
    # Use asdict to compare the entire content, not object references
    if asdict(data_to_clear.charges) == asdict(original_data.charges):
      data_to_clear.charges.values = []

    if asdict(data_to_clear.times) == asdict(original_data.times):
      data_to_clear.times.values = []

    if asdict(data_to_clear.powers) == asdict(original_data.powers):
      data_to_clear.powers.values = []

    if asdict(data_to_clear.socs) == asdict(original_data.socs):
      data_to_clear.socs.values = []

    if asdict(data_to_clear.weeks) == asdict(original_data.weeks):
      data_to_clear.weeks.values = []

  @staticmethod
  def get_time_of_use_as_text(
    tou_data: TimeOfUseData,
    suffx: str = "",
  ) -> str:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    header = f'{sign(tou_data.week.enabled)} Time of Use schedule: {suffx}'
    schedule = 'Gr Gen    Time     Pwr Batt\n'

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

      schedule += (f'{sign(curr_charge.grid_charge)} {sign(curr_charge.gen_charge)} '
                   f'{curr_time.hour:02d}:{curr_time.minute:02d} '
                   f'{next_time.hour:02d}:{next_time.minute:02d} '
                   f'{curr_power:>4} {curr_soc:>3}%\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(tou_data.week.monday)}  '
                     f'{sign(tou_data.week.tuesday)}  '
                     f'{sign(tou_data.week.wednesday)}  '
                     f'{sign(tou_data.week.thursday)}  '
                     f'{sign(tou_data.week.friday)}  '
                     f'{sign(tou_data.week.saturday)}  '
                     f'{sign(tou_data.week.sunday)}')

    return f'{header}\n<pre>{days_of_week}</pre>\n<pre>{schedule}</pre>'
