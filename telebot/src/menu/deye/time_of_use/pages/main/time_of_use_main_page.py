import copy

from enum import Enum
from typing import List

from dataclasses import asdict

from button_node import ButtonNode
from common_utils import CommonUtils
from time_of_use_base_page import TimeOfUseBasePage
from time_of_use_page import TimeOfUsePage
from time_of_use_data import TimeOfUseData
from deye_loggers import DeyeLoggers
from break_button_node import BreakButtonNode
from deye_registers import DeyeRegisters
from telebot_page_navigator import TelebotPageNavigator
from buttons.time_of_use_week_buttons import TimeOfUseWeekButtons
from time_of_use_schedule_buttons import TimeOfUseScheduleButtons
from custom_single_registers import CustomSingleRegisters
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder import DeyeRegistersHolder

class TimeOfUseMainPage(TimeOfUseBasePage):
  def __init__(self, tou_data: TimeOfUseData):
    super().__init__()
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._loggers = DeyeLoggers()
    registers = DeyeRegisters()
    self._register = registers.time_of_use_register
    self._ask_for_reset = False

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    week_buttons = TimeOfUseWeekButtons(
      root_page = self,
      tou_data = self._tou_data,
    )

    schedule_buttons = TimeOfUseScheduleButtons(
      root_page = self,
      tou_data = self._tou_data,
    )

    if self._ask_for_reset:
      bottom_buttons: List[ButtonNode] = [
        ButtonNode("Reset time intervals?"),
        BreakButtonNode(),
        self.register_button_handler(ButtonNode("Yes"), self._handle_reset_yes),
        self.register_button_handler(ButtonNode("No"), self._handle_reset_no),
      ]
    else:
      bottom_buttons: List[ButtonNode] = [
        self.register_button_handler(ButtonNode("Save"), self._handle_save),
      ]

      if self._need_reset():
        bottom_buttons.append(self.register_button_handler(ButtonNode("Reset"), self._handle_reset_ask))

      bottom_buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = week_buttons.buttons + schedule_buttons.buttons + bottom_buttons

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    super().on_button_clicked(
      navigator = navigator,
      button = button,
    )

    if self._ask_for_reset:
      self._ask_for_reset = False

  def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    try:
      self._write_time_of_use(self._tou_data, self._tou_original_data)
    except Exception as e:
      navigator.stop(str(e))
    else:
      navigator.stop(self._get_time_of_use_as_text(self._tou_data))

  def _handle_reset_yes(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_reset = False
    self._reset_time_intervals()
    navigator.update()

  def _handle_reset_no(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_reset = False
    navigator.update()

  def _handle_reset_ask(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_reset = True
    navigator.update()

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(self._get_time_of_use_as_text(self._tou_original_data))

  def _write_time_of_use(
    self,
    tou_data: TimeOfUseData,
    tou_original_data: TimeOfUseData,
  ) -> None:
    if asdict(tou_data) == asdict(tou_original_data):
      return

    data = copy.deepcopy(tou_data)

    self._clear_unchanged_data(
      data_to_clear = data,
      original_data = tou_original_data,
    )

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self._loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self._register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.write_register(self._register, data)
    finally:
      holder.disconnect()

  def _need_reset(self) -> bool:
    """
    Checks if the time intervals need to be reset to their default hourly steps.
    """
    values = self._tou_data.times.values
    total_intervals = len(values)

    # If there's nothing to check, no reset is needed
    if total_intervals == 0:
      return False

    hours_per_step = 24 // total_intervals

    for i in range(total_intervals):
      curr_time = values[i]

      expected_hour = i * hours_per_step
      expected_minute = 0

      # If any interval differs from the expected default, return True
      if curr_time.hour != expected_hour or curr_time.minute != expected_minute:
        return True

    return False

  def _reset_time_intervals(self) -> None:
    """
    Directly updates the hour and minute attributes of existing TimeOfUseTime objects.
    """
    values = self._tou_data.times.values

    total_intervals = len(values)
    if total_intervals == 0:
      return

    hours_per_step = 24 // total_intervals

    # Update only existing objects in the list
    for i in range(min(total_intervals, len(values))):
      curr_time = values[i]

      # Modify attributes in-place
      curr_time.hour = i * hours_per_step
      curr_time.minute = 0

  def _clear_unchanged_data(
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

  def _get_time_of_use_as_text(self, data: TimeOfUseData) -> str:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    weekly = data.weeks.values[0]

    header = f'{sign(weekly.enabled)} Time of Use schedule:'
    schedule = 'Gr Gen    Time     Pwr SOC\n'

    charges = data.charges.values
    times = data.times.values
    powers = data.powers.values
    socs = data.socs.values

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
                   f'{curr_power:>4} {curr_soc:>3}\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(weekly.monday)}  '
                     f'{sign(weekly.tuesday)}  '
                     f'{sign(weekly.wednesday)}  '
                     f'{sign(weekly.thursday)}  '
                     f'{sign(weekly.friday)}  '
                     f'{sign(weekly.saturday)}  '
                     f'{sign(weekly.sunday)}')

    return f'{header}\n<pre>{days_of_week}</pre>\n<pre>{schedule}</pre>'
