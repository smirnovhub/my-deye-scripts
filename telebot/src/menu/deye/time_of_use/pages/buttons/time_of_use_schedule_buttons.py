from enum import Enum
from typing import List

from button_node import ButtonNode
from button_style import ButtonStyle
from time_of_use_data import TimeOfUseData
from time_of_use_page import TimeOfUsePage
from break_button_node import BreakButtonNode
from time_of_use_times import TimeOfUseTimes
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseScheduleButtons:
  def __init__(
    self,
    page: TelebotNavigationPage,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_data = tou_data
    self._is_data_correct = True

    header_buttons: List[ButtonNode] = [
      page.register_button_handler(
        ButtonNode("Grid"),
        self._toggle_all_grid,
      ),
      page.register_button_handler(
        ButtonNode("Gen"),
        self._toggle_all_gen,
      ),
      ButtonNode("Start"),
      ButtonNode("End"),
      page.register_button_handler(
        ButtonNode("Pwr"),
        self._create_navigation_handler(TimeOfUsePage.powers),
      ),
      page.register_button_handler(
        ButtonNode("Batt"),
        self._create_navigation_handler(TimeOfUsePage.socs),
      ),
      BreakButtonNode(),
    ]

    charges = tou_data.charges.values
    times = tou_data.times.values
    powers = tou_data.powers.values
    socs = tou_data.socs.values

    count = len(times)
    rows_buttons = []

    for i in range(count):
      charge = charges[i]
      time = times[i]
      next_time = times[(i + 1) % count]

      style = ButtonStyle.default
      if not TimeOfUseTimes.is_interval_correct(start = time, end = next_time):
        self._is_data_correct = False
        style = ButtonStyle.danger

      grid = TimeOfUseSwitchButtonNode(enabled = charge.grid_charge)
      gen = TimeOfUseSwitchButtonNode(enabled = charge.gen_charge)
      start = ButtonNode(text = f"{time.hour:02d}:{time.minute:02d}", style = style)
      end = ButtonNode(text = f"{next_time.hour:02d}:{next_time.minute:02d}", style = style)
      power = ButtonNode(text = str(powers[i]))
      soc = ButtonNode(text = f"{socs[i]}%")

      page.register_button_handler(grid, self._create_toggle_grid_handler(i))
      page.register_button_handler(gen, self._create_toggle_gen_handler(i))
      page.register_button_handler(start, self._create_navigation_handler(TimeOfUsePage.start_hours, i))
      page.register_button_handler(end, self._create_navigation_handler(TimeOfUsePage.end_hours, (i + 1) % count))
      page.register_button_handler(power, self._create_navigation_handler(TimeOfUsePage.powers, i))
      page.register_button_handler(soc, self._create_navigation_handler(TimeOfUsePage.socs, i))

      rows_buttons.extend([grid, gen, start, end, power, soc, BreakButtonNode()])

    self._buttons = header_buttons + rows_buttons

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  @property
  def is_data_correct(self) -> bool:
    return self._is_data_correct

  def _create_toggle_grid_handler(self, line_index: int):
    # The handler now accepts both navigator and button_node
    def handler(navigator: TelebotPageNavigator) -> None:
      value = self._tou_data.charges.values[line_index].grid_charge
      self._tou_data.charges.values[line_index].grid_charge = not value
      navigator.update()

    return handler

  def _toggle_all_grid(self, navigator: TelebotPageNavigator):
    # Determine target state: if any is disabled, enable all. Otherwise, disable all.
    charges = self._tou_data.charges.values
    target_state = any(not c.grid_charge for c in charges)

    for charge in charges:
      charge.grid_charge = target_state

    navigator.update()

  def _create_toggle_gen_handler(self, line_index: int):
    # The handler now accepts both navigator and button_node
    def handler(navigator: TelebotPageNavigator) -> None:
      value = self._tou_data.charges.values[line_index].gen_charge
      self._tou_data.charges.values[line_index].gen_charge = not value
      navigator.update()

    return handler

  def _toggle_all_gen(self, navigator: TelebotPageNavigator):
    # Determine target state: if any is disabled, enable all. Otherwise, disable all.
    charges = self._tou_data.charges.values
    target_state = any(not c.gen_charge for c in charges)

    for charge in charges:
      charge.gen_charge = target_state

    navigator.update()

  def _create_navigation_handler(self, target_page: Enum, line_index: int = -1):
    def handler(navigator: TelebotPageNavigator) -> None:
      navigator.navigate(target_page, time_of_use_line_index = line_index)

    return handler
