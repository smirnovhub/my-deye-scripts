import copy

from dataclasses import asdict
from enum import Enum
from typing import List

from button_node import ButtonNode
from button_style import ButtonStyle
from deye_register import DeyeRegister
from common_utils import CommonUtils
from deye_loggers import DeyeLoggers
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from time_of_use_data import TimeOfUseData
from time_of_use_times import TimeOfUseTimes
from break_button_node import BreakButtonNode
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_week_buttons import TimeOfUseWeekButtons
from telebot_navigation_page import TelebotNavigationPage
from time_of_use_schedule_buttons import TimeOfUseScheduleButtons

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._loggers = DeyeLoggers()
    self._ask_for_fix = False
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

    bottom_buttons: List[ButtonNode] = []

    if self._ask_for_fix:
      bottom_buttons.extend([
        ButtonNode("Fix time intervals?"),
        BreakButtonNode(),
        self.register_button_handler(ButtonNode("Yes"), self._handle_fix_yes),
        self.register_button_handler(ButtonNode("No"), self._handle_fix_no),
      ])
    elif self._ask_for_reset:
      bottom_buttons.extend([
        ButtonNode("Reset time intervals?"),
        BreakButtonNode(),
        self.register_button_handler(ButtonNode("Yes"), self._handle_reset_yes),
        self.register_button_handler(ButtonNode("No"), self._handle_reset_no),
      ])
    else:
      if self._need_save():
        callback = self._handle_save if schedule_buttons.is_data_correct else self._handle_fix_ask
        bottom_buttons.append(self.register_button_handler(ButtonNode("Save"), callback))

      if self._need_fix_intervals():
        bottom_buttons.append(
          self.register_button_handler(ButtonNode(
            "Fix times",
            style = ButtonStyle.danger,
          ), self._handle_fix_ask))
      elif self._need_reset_intervals():
        bottom_buttons.append(self.register_button_handler(ButtonNode("Reset times"), self._handle_reset_ask))

      bottom_buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = week_buttons.buttons + schedule_buttons.buttons + bottom_buttons

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    super().on_button_clicked(
      navigator = navigator,
      button = button,
    )

    if self._ask_for_reset:
      self._ask_for_reset = False

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    text = self._get_time_of_use_as_text(self._tou_original_data)
    navigator.stop(text)

  def get_goodbye_message(self) -> str:
    return self._get_time_of_use_as_text(self._tou_original_data)

  def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    text = self._get_time_of_use_as_text(tou_data = self._tou_data, suffx = "saved")

    if not self._need_save():
      navigator.stop(text)
      return

    data = copy.deepcopy(self._tou_data)

    TimeOfUseHelper.clear_unchanged_data(
      data_to_clear = data,
      original_data = self._tou_original_data,
    )

    try:
      TimeOfUseHelper.write_time_of_use(
        tou_register = self._tou_register,
        master_logger = self._loggers.master,
        tou_data = data,
      )
    except Exception as e:
      navigator.stop(str(e))
    else:
      navigator.stop(text)

  def _handle_fix_yes(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_fix = False
    self._fix_time_intervals()
    navigator.update()

  def _handle_fix_no(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_fix = False
    navigator.update()

  def _handle_reset_yes(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_reset = False
    self._reset_time_intervals()
    navigator.update()

  def _handle_reset_no(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_reset = False
    navigator.update()

  def _handle_fix_ask(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_fix = True
    navigator.update()

  def _handle_reset_ask(self, navigator: TelebotPageNavigator) -> None:
    self._ask_for_reset = True
    navigator.update()

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(self._get_time_of_use_as_text(tou_data = self._tou_original_data))

  def _need_save(self) -> bool:
    return asdict(self._tou_data) != asdict(self._tou_original_data)

  def _need_fix_intervals(self) -> bool:
    times = self._tou_data.times.values
    count = len(times)

    for i in range(count):
      time = times[i]
      next_time = times[(i + 1) % count]

      if not TimeOfUseTimes.is_interval_correct(start = time, end = next_time):
        return True

    return False

  def _need_reset_intervals(self) -> bool:
    """
    Checks if the time intervals need to be reset to their default hourly steps.
    """
    times = self._tou_data.times.values
    count = len(times)

    # If there's nothing to check, no reset is needed
    if count == 0:
      return False

    hours_per_step = 24 // count

    for i in range(count):
      curr_time = times[i]

      expected_hour = i * hours_per_step
      expected_minute = 0

      # If any interval differs from the expected default, return True
      if curr_time.hour != expected_hour or curr_time.minute != expected_minute:
        return True

    return False

  def _fix_time_intervals(self) -> None:
    times = self._tou_data.times.values
    if not times:
      return

    step_min = 5
    count = len(times)

    times[0].hour = 0
    times[0].minute = 0

    # The absolute anchor is the very first time in the list
    start_minutes = times[0].hour * 60 + times[0].minute
    # The end anchor is the same time but 24 hours later
    end_minutes = start_minutes + 1440

    # Prepare a list of minutes, treating each as being within the 24h window
    minutes = []
    for i in range(count):
      m = times[i].hour * 60 + times[i].minute
      # If time is less than start, it's definitely the next day (e.g., 00:00 after 20:00)
      if m < start_minutes:
        m += 1440
      minutes.append(m)

    # Add the target end point (start of next day) for the last interval calculation
    minutes.append(end_minutes)

    i = 0
    while i < len(minutes) - 1:
      t1 = minutes[i]

      # Look for the next valid anchor (a point that is > t1 and > previous points)
      j = i + 1
      while j < len(minutes) and minutes[j] <= t1:
        j += 1

      # If we have a gap, interpolate
      if j > i + 1:
        steps = j - i
        total_diff = minutes[j] - t1

        for k in range(1, steps):
          raw_val = t1 + (total_diff * k / steps)
          # Round to nearest 5 min
          rounded_val = int(round(raw_val / step_min) * step_min)

          # Safety constraints
          if rounded_val >= minutes[j]:
            rounded_val = minutes[j] - step_min
          if rounded_val <= minutes[i + k - 1]:
            rounded_val = minutes[i + k - 1] + step_min

          minutes[i + k] = rounded_val
      i = j

    # Write back (excluding the extra end_minutes we added)
    for i in range(count):
      total = minutes[i] % 1440
      times[i].hour = total // 60
      times[i].minute = total % 60

  def _reset_time_intervals(self) -> None:
    """
    Directly updates the hour and minute attributes of existing TimeOfUseTime objects.
    """
    times = self._tou_data.times.values
    if not times:
      return

    count = len(times)
    hours_per_step = 24 // count

    # Update only existing objects in the list
    for i in range(min(count, len(times))):
      curr_time = times[i]

      # Modify attributes in-place
      curr_time.hour = i * hours_per_step
      curr_time.minute = 0

  def _get_time_of_use_as_text(
    self,
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
