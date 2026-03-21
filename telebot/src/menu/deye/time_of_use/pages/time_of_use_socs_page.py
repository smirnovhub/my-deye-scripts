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
  ):
    super().__init__()
    self._tou_socs = tou_socs
    self._time_of_use_line_index = -1
    self.values = [
      [15, 20, 25, 30],
      [35, 40, 45, 50],
      [55, 60, 65, 70],
      [75, 80, 85, 90],
      [93, 95, 97, 100],
    ]
    self._min_val = min(x for row in self.values for x in row)
    self._max_val = max(x for row in self.values for x in row)

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

    for row_index, row in enumerate(self.values):
      if row_index > 0:
        buttons.append(BreakButtonNode())

      for value in row:
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
    if self._time_of_use_line_index < 0:
      # Replace all elements in the list with the new value
      self._tou_socs.values[:] = [soc] * len(self._tou_socs.values)
    else:
      self._tou_socs.values[self._time_of_use_line_index] = soc

    navigator.navigate(TimeOfUsePage.main)
