from enum import Enum
from typing import Any, List

from button_node import ButtonNode
from time_of_use_data import TimeOfUsePowers
from break_button_node import BreakButtonNode
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUsePowersPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_powers: TimeOfUsePowers,
  ):
    super().__init__()
    self._tou_powers = tou_powers
    self._time_of_use_line_index = -1
    self._values = [
      [0, 250, 500],
      [1000, 1250, 1500],
      [2000, 2500, 3000],
      [3500, 4000, 4500],
      [5000, 5500, 6000],
    ]
    self._min_val = min(x for row in self._values for x in row)
    self._max_val = max(x for row in self._values for x in row)

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.powers

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, **kwargs: Any):
    index = kwargs.get("time_of_use_line_index")
    if index is None:
      raise RuntimeError("time_of_use_line_index not found")

    TimeOfUseHelper.check_upper_bounds(self._tou_powers.values, index)
    self._time_of_use_line_index = index

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode("Battery power, W:"),
      BreakButtonNode(),
    ]

    for row_index, row in enumerate(self._values):
      if row_index > 0:
        buttons.append(BreakButtonNode())

      for value in row:
        btn = ButtonNode(text = str(value), data = str(value))
        buttons.append(self.register_button_handler(btn, self._create_power_handler(value)))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))

    self._buttons = buttons

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      power = int(text)
    except Exception:
      raise ValueError(f"Power value should be from {self._min_val} to {self._max_val}")

    if not (self._min_val <= power <= self._max_val):
      raise ValueError(f"Power value should be from {self._min_val} to {self._max_val}")

    self._set_power_and_go_back(
      navigator = navigator,
      power = power,
    )

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(TimeOfUsePage.main)

  def _create_power_handler(self, power: int):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._set_power_and_go_back(navigator, power)

    return handler

  def _set_power_and_go_back(
    self,
    navigator: TelebotPageNavigator,
    power: int,
  ) -> None:
    if self._time_of_use_line_index < 0:
      # Replace all elements in the list with the new value
      self._tou_powers.values[:] = [power] * len(self._tou_powers.values)
    else:
      self._tou_powers.values[self._time_of_use_line_index] = power

    navigator.navigate(TimeOfUsePage.main)
