import copy

from dataclasses import asdict
from enum import Enum
from typing import List

from button_node import ButtonNode
from common_utils import CommonUtils
from time_of_use_base_page import TimeOfUseBasePage
from time_of_use_page import TimeOfUsePage
from time_of_use_data import TimeOfUseData
from break_button_node import BreakButtonNode
from telebot_page_navigator import TelebotPageNavigator
from buttons.time_of_use_week_buttons import TimeOfUseWeekButtons
from time_of_use_schedule_buttons import TimeOfUseScheduleButtons

class TimeOfUseMainPage(TimeOfUseBasePage):
  def __init__(self, tou_data: TimeOfUseData):
    super().__init__()
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._ask_for_reset = False

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    week_buttons = TimeOfUseWeekButtons(
      page = self,
      tou_week = self._tou_data.week,
    )

    schedule_buttons = TimeOfUseScheduleButtons(
      page = self,
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

  def get_goodbye_message(self) -> str:
    return self._get_time_of_use_as_text(self._tou_original_data)

  def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    text = self._get_time_of_use_as_text(self._tou_data)

    if asdict(self._tou_data) == asdict(self._tou_original_data):
      navigator.stop(text)
      return

    data = copy.deepcopy(self._tou_data)

    self.clear_unchanged_data(
      data_to_clear = data,
      original_data = self._tou_original_data,
    )

    try:
      self.write_time_of_use(data)
    except Exception as e:
      navigator.stop(str(e))
    else:
      navigator.stop(text)

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

  def _get_time_of_use_as_text(self, data: TimeOfUseData) -> str:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    header = f'{sign(data.week.enabled)} Time of Use schedule:'
    schedule = 'Gr Gen    Time     Pwr Batt\n'

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
                   f'{curr_power:>4} {curr_soc:>3}%\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(data.week.monday)}  '
                     f'{sign(data.week.tuesday)}  '
                     f'{sign(data.week.wednesday)}  '
                     f'{sign(data.week.thursday)}  '
                     f'{sign(data.week.friday)}  '
                     f'{sign(data.week.saturday)}  '
                     f'{sign(data.week.sunday)}')

    return f'{header}\n<pre>{days_of_week}</pre>\n<pre>{schedule}</pre>'
