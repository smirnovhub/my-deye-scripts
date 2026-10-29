from dataclasses import asdict

from telebot_buttons import *
from button_style import ButtonStyle
from deye_register import DeyeRegister
from deye_loggers import DeyeLoggers
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_ask_data import TimeOfUseAskData
from time_of_use_helper import TimeOfUseHelper
from time_of_use_data import TimeOfUseData
from time_of_use_page_type import TimeOfUsePageType
from time_of_use_times import TimeOfUseTimes

class TimeOfUseBottomButtons:
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
    tou_original_data: TimeOfUseData,
    ask_data: TimeOfUseAskData,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data = tou_data
    self._tou_original_data = tou_original_data
    self._ask_data = ask_data
    self._loggers = DeyeLoggers()

  def create_buttons(
    self,
    page: TelebotNavigationPage,
    can_save: bool,
  ) -> None:
    if self._ask_data.ask_for_fix_times:
      page.register_button(ButtonNode("Fix time intervals?"))
      page.register_button(BreakButtonNode())
      page.register_button(ButtonNode("Yes"), self._handle_fix_yes)
      page.register_button(ButtonNode("No"), self._handle_fix_no)
    elif self._ask_data.ask_for_reset_times:
      page.register_button(ButtonNode("Reset time intervals?"))
      page.register_button(BreakButtonNode())
      page.register_button(ButtonNode("Yes"), self._handle_reset_yes)
      page.register_button(ButtonNode("No"), self._handle_reset_no)
    else:
      if self._need_save():
        callback = self._handle_save if can_save else self._handle_fix_ask
        page.register_button(ButtonNode("Save"), callback)

      if self._need_fix_intervals():
        page.register_button(ButtonNode(
          "Fix times",
          style = ButtonStyle.danger,
        ), self._handle_fix_ask)
      elif self._need_reset_intervals():
        page.register_button(ButtonNode("Reset times"), self._handle_reset_ask)

      page.register_button(CancelButtonNode(), self._handle_cancel)

    self._ask_data.ask_for_fix_times = False
    self._ask_data.ask_for_reset_times = False

  async def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    if not self._need_save():
      text = TimeOfUseHelper.get_time_of_use_as_rich_message(tou_data = self._tou_data)
      await navigator.stop(text)
      return

    data = TimeOfUseHelper.get_cleared_unchanged_data(
      data_to_clear = self._tou_data,
      original_data = self._tou_original_data,
    )

    await TimeOfUseHelper.write_time_of_use(
      tou_register = self._tou_register,
      master_logger = self._loggers.master,
      tou_data = data,
    )

    await navigator.navigate(TimeOfUsePageType.undo)

  async def _handle_fix_yes(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_fix_times = False
    self._fix_time_intervals()
    await navigator.update()

  async def _handle_fix_no(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_fix_times = False
    await navigator.update()

  async def _handle_reset_yes(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_reset_times = False
    self._reset_time_intervals()
    await navigator.update()

  async def _handle_reset_no(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_reset_times = False
    await navigator.update()

  async def _handle_fix_ask(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_fix_times = True
    await navigator.update()

  async def _handle_reset_ask(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_reset_times = True
    await navigator.update()

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(
      TimeOfUseHelper.get_time_of_use_as_rich_message(
        tou_data = self._tou_original_data,
        suffx = "cancel",
      ))

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
      time = times[i]

      expected_hour = i * hours_per_step
      expected_minute = 0

      # If any interval differs from the expected default, return True
      if time.hour != expected_hour or time.minute != expected_minute:
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
