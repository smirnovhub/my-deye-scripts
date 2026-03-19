from dataclasses import asdict
from typing import Any, Sequence

from time_of_use_data import TimeOfUseData
from deye_logger import DeyeLogger
from deye_register import DeyeRegister
from time_of_use_time import TimeOfUseTime
from custom_single_registers import CustomSingleRegisters
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder import DeyeRegistersHolder

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
  def write_time_of_use(
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
    master_logger: DeyeLogger,
  ) -> None:
    if not isinstance(tou_register.value, TimeOfUseData):
      raise RuntimeError(f"Register value type should be {TimeOfUseData.__name__}, but "
                         f"{type(tou_register.value).__name__} received")

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [master_logger],
      register_creator = lambda prefix: CustomSingleRegisters(tou_register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.write_register(tou_register, tou_data)
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
  def is_interval_correct(
    start: TimeOfUseTime,
    end: TimeOfUseTime,
  ) -> bool:
    if start == end:
      return False

    # Check if next_time is 00:00 (end of the 24h cycle)
    is_midnight = end.hour == 0 and end.minute == 0
    return is_midnight or end >= start
