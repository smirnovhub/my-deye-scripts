from dataclasses import asdict
from typing import Any, Sequence

from time_of_use_data import TimeOfUseData
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from telebot_navigation_page import TelebotNavigationPage
from custom_single_registers import CustomSingleRegisters
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder import DeyeRegistersHolder

class TimeOfUseBasePage(TelebotNavigationPage):
  def __init__(self):
    super().__init__()
    self._loggers = DeyeLoggers()
    registers = DeyeRegisters()
    self._register = registers.time_of_use_register

  def check_bounds(self, collection: Sequence[Any], index: int) -> None:
    count = len(collection)
    if not (0 <= index < count):
      class_name = self.__class__.__name__
      raise RuntimeError(f"{class_name}: index {index} is out of bounds (0 to {count - 1})")

  def check_upper_bounds(self, collection: Sequence[Any], index: int) -> None:
    count = len(collection)
    if index >= count:
      class_name = self.__class__.__name__
      raise RuntimeError(f"{class_name}: index {index} should be less than {count - 1}")

  def write_time_of_use(self, tou_data: TimeOfUseData) -> None:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self._loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self._register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.write_register(self._register, tou_data)
    finally:
      holder.disconnect()

  def clear_unchanged_data(
    self,
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
