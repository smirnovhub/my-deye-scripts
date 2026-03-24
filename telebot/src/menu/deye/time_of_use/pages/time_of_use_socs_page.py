from enum import Enum
from typing import Any, List

from button_node import ButtonNode
from time_of_use_data import TimeOfUseSocs
from break_button_node import BreakButtonNode
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseSocsPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_socs: TimeOfUseSocs,
    minimum_soc: int,
  ):
    super().__init__()
    self._tou_socs = tou_socs
    self._time_of_use_line_index = -1

    self._values = self._generate_values(min_val = minimum_soc)

    self._min_val = min(self._values)
    self._max_val = max(self._values)

    if minimum_soc > self._min_val:
      self._min_val = minimum_soc

    self._row_length = 4

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.socs

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, **kwargs: Any):
    index = kwargs.get("time_of_use_line_index")
    if index is None:
      raise RuntimeError("time_of_use_line_index not found")

    TimeOfUseHelper.check_upper_bounds(self._tou_socs.values, index)
    self._time_of_use_line_index = index

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode("Battery SOC, %:"),
      BreakButtonNode(),
    ]

    for index, value in enumerate(self._values):
      if index > 0 and (index % self._row_length) == 0:
        buttons.append(BreakButtonNode())

      btn = ButtonNode(text = str(value), data = str(value))
      buttons.append(self.register_button_handler(btn, self._create_soc_handler(value)))

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))

    self._buttons = buttons

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      soc = int(text)
    except Exception:
      raise ValueError(f"SOC value should be from {self._min_val} to {self._max_val}")

    if not (self._min_val <= soc <= self._max_val):
      raise ValueError(f"SOC value should be from {self._min_val} to {self._max_val}")

    self._set_soc_and_go_back(
      navigator = navigator,
      soc = soc,
    )

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(TimeOfUsePage.main)

  def _create_soc_handler(self, soc: int):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._set_soc_and_go_back(navigator, soc)

    return handler

  def _set_soc_and_go_back(
    self,
    navigator: TelebotPageNavigator,
    soc: int,
  ) -> None:
    if not (self._min_val <= soc <= self._max_val):
      raise ValueError(f"SOC value should be from {self._min_val} to {self._max_val}")

    if self._time_of_use_line_index < 0:
      # Replace all elements in the list with the new value
      self._tou_socs.values[:] = [soc] * len(self._tou_socs.values)
    else:
      self._tou_socs.values[self._time_of_use_line_index] = soc

    navigator.navigate(TimeOfUsePage.main)

  def _generate_values(
    self,
    min_val: int,
    step: int = 5,
    target_count: int = 20,
    transition_point: int = 90,
    max_val: int = 100,
  ) -> List[int]:
    # Start with min_val
    result: List[int] = [min_val]

    # Fill Zone A: multiples of step strictly below transition_point
    first_multiple = min_val if min_val % step == 0 else min_val + (step - min_val % step)
    current = first_multiple
    while current < transition_point:
      if current > min_val:
        result.append(current)
      current += step

    # FORCE transition_point into the sequence
    if result[-1] != transition_point:
      result.append(transition_point)

    # Calculate how many slots are left to reach target_count
    # max_val will be the last one, so we need (target_count - current_len) more
    current_len = len(result)
    needed_count = target_count - current_len

    if needed_count <= 0:
      # If we already have enough, trim and ensure max_val
      final = result[:target_count - 1]
      final.append(max_val)
      return final

    # Zone B: Uniformly distribute remaining integers between transition_point and max_val
    last_val = result[-1] # This is now exactly 90
    total_gap = max_val - last_val

    for i in range(1, needed_count + 1):
      # Linear interpolation to find the next integer
      # (i / needed_count) ensures we land exactly on max_val at the last step
      next_val = last_val + (total_gap * i) // needed_count

      # Ensure uniqueness
      if next_val > result[-1]:
        result.append(int(next_val))
      else:
        result.append(result[-1] + 1)

    # Final safeguard for length
    if len(result) > target_count:
      result = result[:target_count - 1] + [max_val]

    return result
