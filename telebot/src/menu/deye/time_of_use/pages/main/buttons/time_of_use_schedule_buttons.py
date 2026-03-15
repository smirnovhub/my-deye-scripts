from enum import Enum
from typing import List

from button_node import ButtonNode
from time_of_use_data import TimeOfUseData
from time_of_use_page import TimeOfUsePage
from break_button_node import BreakButtonNode
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseScheduleButtons:
  def __init__(
    self,
    root_page: TelebotNavigationPage,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._root_page = root_page
    self._tou_data = tou_data

    header_buttons: List[ButtonNode] = [
      self._root_page.register_button_handler(
        ButtonNode("Grid"),
        self._toggle_all_grid,
      ),
      self._root_page.register_button_handler(
        ButtonNode("Gen"),
        self._toggle_all_gen,
      ),
      ButtonNode("Start"),
      ButtonNode("End"),
      self._root_page.register_button_handler(
        ButtonNode("Pwr"),
        self._create_navigation_handler(TimeOfUsePage.powers),
      ),
      self._root_page.register_button_handler(
        ButtonNode("Batt"),
        self._create_navigation_handler(TimeOfUsePage.socs),
      ),
      BreakButtonNode(),
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

      self._root_page.register_button_handler(grid, self._create_toggle_grid_handler(i))
      self._root_page.register_button_handler(gen, self._create_toggle_gen_handler(i))

      self._root_page.register_button_handler(
        start,
        self._create_navigation_handler(TimeOfUsePage.start_hours, i),
      )

      self._root_page.register_button_handler(
        end,
        self._create_navigation_handler(TimeOfUsePage.end_hours, (i + 1) % count),
      )

      self._root_page.register_button_handler(
        power,
        self._create_navigation_handler(TimeOfUsePage.powers, i),
      )

      self._root_page.register_button_handler(
        soc,
        self._create_navigation_handler(TimeOfUsePage.socs, i),
      )

      rows_buttons.extend([grid, gen, start, end, power, soc, BreakButtonNode()])

    self._buttons = header_buttons + rows_buttons

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

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

  def _toggle_all_gen(self, navigator: TelebotPageNavigator, button: ButtonNode):
    # Determine target state: if any is disabled, enable all. Otherwise, disable all.
    charges = self._tou_data.charges.values
    target_state = any(not c.gen_charge for c in charges)

    for charge in charges:
      charge.gen_charge = target_state

    navigator.update()

  def _create_navigation_handler(self, target_page: Enum, line_index: int = -1):
    # The handler now accepts both navigator and button_node
    def handler(navigator: TelebotPageNavigator, button: ButtonNode) -> None:
      navigator.navigate(target_page, time_of_use_line_index = line_index)

    return handler
