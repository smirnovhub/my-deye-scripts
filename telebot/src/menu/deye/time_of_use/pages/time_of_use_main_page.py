import copy

from enum import Enum
from typing import List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from time_of_use_base_page import TimeOfUseBasePage
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from time_of_use_data import TimeOfUseData
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseMainPage(TimeOfUseBasePage):
  def __init__(self, tou_data: TimeOfUseData):
    super().__init__()
    self._tou_data = tou_data
    self._tou_week = tou_data.weeks.values[0]
    self._tou_original_data = copy.deepcopy(tou_data)

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    self.clear_button_handlers()

    header_buttons: List[ButtonNode] = [
      ButtonNode("Grid"),
      ButtonNode("Gen"),
      ButtonNode("Start"),
      ButtonNode("End"),
      ButtonNode("Pwr"),
      ButtonNode("Batt"),
      BreakButtonNode(),
    ]

    week_header_buttons: List[ButtonNode] = [
      ButtonNode("Mon"),
      ButtonNode("Tue"),
      ButtonNode("Wed"),
      ButtonNode("Thu"),
      ButtonNode("Fri"),
      ButtonNode("Sat"),
      ButtonNode("Sun"),
      BreakButtonNode(),
    ]

    bottom_buttons: List[ButtonNode] = [
      self.register_button_handler(ButtonNode("Save"), self._handle_save),
      self.register_button_handler(ButtonNode("Reset"), self._handle_reset),
      self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel),
    ]

    charges = self._tou_data.charges.values
    times = self._tou_data.times.values
    powers = self._tou_data.powers.values
    socs = self._tou_data.socs.values

    count = len(times)
    rows_buttons = []

    for i in range(count):
      charge = charges[i]
      time = times[i]
      next_time = times[(i + 1) % count]

      grid = TimeOfUseSwitchButtonNode(
        enabled = charge.grid_charge,
        index = i,
      )

      gen = TimeOfUseSwitchButtonNode(
        enabled = charge.gen_charge,
        index = i,
      )

      start = TimeOfUseButtonNode(
        text = f"{time.hour:02d}:{time.minute:02d}",
        index = i,
      )

      end = TimeOfUseButtonNode(
        text = f"{next_time.hour:02d}:{next_time.minute:02d}",
        index = i,
      )

      power = TimeOfUseButtonNode(
        text = str(powers[i]),
        data = str(powers[i]),
        index = i,
      )

      soc = TimeOfUseButtonNode(
        text = f"{socs[i]}%",
        data = str(socs[i]),
        index = i,
      )

      self.register_button_handler(grid, lambda n, b = grid: self._toggle_grid(n, b))
      self.register_button_handler(gen, lambda n, b = gen: self._toggle_gen(n, b))
      self.register_button_handler(start,
                                   lambda n, i = i: n.navigate(TimeOfUsePage.start_hours, time_of_use_line_index = i))
      self.register_button_handler(
        end, lambda n, i = i: n.navigate(TimeOfUsePage.end_hours, time_of_use_line_index = (i + 1) % count))
      self.register_button_handler(power, lambda n, i = i: n.navigate(TimeOfUsePage.powers, time_of_use_line_index = i))
      self.register_button_handler(soc, lambda n, i = i: n.navigate(TimeOfUsePage.socs, time_of_use_line_index = i))

      rows_buttons.extend([grid, gen, start, end, power, soc, BreakButtonNode()])

    # Days of the week
    mon = TimeOfUseSwitchButtonNode(enabled = self._tou_week.monday)
    mon_btn = self.register_button_handler(mon, lambda n, b = mon: self._toggle_monday(n, b))
    tue = TimeOfUseSwitchButtonNode(enabled = self._tou_week.tuesday)
    tue_btn = self.register_button_handler(tue, lambda n, b = tue: self._toggle_tuesday(n, b))
    wed = TimeOfUseSwitchButtonNode(enabled = self._tou_week.wednesday)
    wed_btn = self.register_button_handler(wed, lambda n, b = wed: self._toggle_wednesday(n, b))
    thu = TimeOfUseSwitchButtonNode(enabled = self._tou_week.thursday)
    thu_btn = self.register_button_handler(thu, lambda n, b = thu: self._toggle_thursday(n, b))
    fri = TimeOfUseSwitchButtonNode(enabled = self._tou_week.friday)
    fri_btn = self.register_button_handler(fri, lambda n, b = fri: self._toggle_friday(n, b))
    sat = TimeOfUseSwitchButtonNode(enabled = self._tou_week.saturday)
    sat_btn = self.register_button_handler(sat, lambda n, b = sat: self._toggle_saturday(n, b))
    sun = TimeOfUseSwitchButtonNode(enabled = self._tou_week.sunday)
    sun_btn = self.register_button_handler(sun, lambda n, b = sun: self._toggle_sunday(n, b))

    week_buttons = [
      mon_btn,
      tue_btn,
      wed_btn,
      thu_btn,
      fri_btn,
      sat_btn,
      sun_btn,
      BreakButtonNode(),
    ]

    self._buttons = week_header_buttons + week_buttons + header_buttons + rows_buttons + bottom_buttons

  def _toggle_grid(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode):
    button.switch()
    self._tou_data.charges.values[button.index].grid_charge = button.enabled
    navigator.update()

  def _toggle_gen(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode):
    button.switch()
    self._tou_data.charges.values[button.index].gen_charge = button.enabled
    navigator.update()

  def _toggle_monday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.monday = not self._tou_week.monday
    navigator.update()

  def _toggle_tuesday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.tuesday = not self._tou_week.tuesday
    navigator.update()

  def _toggle_wednesday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.wednesday = not self._tou_week.wednesday
    navigator.update()

  def _toggle_thursday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.thursday = not self._tou_week.thursday
    navigator.update()

  def _toggle_friday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.friday = not self._tou_week.friday
    navigator.update()

  def _toggle_saturday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.saturday = not self._tou_week.saturday
    navigator.update()

  def _toggle_sunday(self, navigator: TelebotPageNavigator, button: TimeOfUseSwitchButtonNode) -> None:
    button.switch()
    self._tou_week.sunday = not self._tou_week.sunday
    navigator.update()

  def _handle_save(self, navigator: TelebotPageNavigator):
    try:
      self.write_time_of_use(self._tou_data, self._tou_original_data)
    except Exception as e:
      navigator.stop(str(e))
    else:
      navigator.stop(self.get_time_of_use_as_text(self._tou_data))

  def _handle_reset(self, navigator: TelebotPageNavigator):
    self._reset_time_intervals()
    self.update()
    navigator.update()

  def _handle_cancel(self, navigator: TelebotPageNavigator):
    navigator.stop(self.get_time_of_use_as_text(self._tou_original_data))

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
