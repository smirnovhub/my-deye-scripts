from enum import Enum
from typing import List

from button_node import ButtonNode
from time_of_use_base_page import TimeOfUseBasePage
from time_of_use_data import TimeOfUsePowers
from break_button_node import BreakButtonNode
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_page_navigator import TelebotPageNavigator

class TimeOfUsePowersPage(TimeOfUseBasePage):
  def __init__(
    self,
    tou_powers: TimeOfUsePowers,
  ):
    super().__init__()
    self._tou_powers = tou_powers
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.powers

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, time_of_use_line_index: int, **kwargs):
    self.check_bounds(self._tou_powers.values, time_of_use_line_index)
    self._time_of_use_line_index = time_of_use_line_index

  def update(self) -> None:
    self.clear_button_handlers()

    buttons: List[ButtonNode] = [
      ButtonNode("Battery power, W:"),
      BreakButtonNode(),
    ]

    values = [
      [250, 500, 1000],
      [1250, 1500, 2000],
      [2500, 3000, 3500],
      [4000, 5000, 6000],
    ]

    for row_index, row in enumerate(values):
      if row_index > 0:
        buttons.append(BreakButtonNode())

      for value in row:

        btn = TimeOfUseButtonNode(
          text = str(value),
          data = str(value),
          index = row_index,
        )

        self.register_button_handler(btn, self._create_power_handler(value))
        buttons.append(btn)

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))

    self._buttons = buttons

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(TimeOfUsePage.main)

  def _create_power_handler(self, power: int):
    def handler(navigator: TelebotPageNavigator) -> None:
      if self._time_of_use_line_index < 0:
        # Replace all elements in the list with the new value
        self._tou_powers.values[:] = [power] * len(self._tou_powers.values)
      else:
        self._tou_powers.values[self._time_of_use_line_index] = power

      navigator.navigate(TimeOfUsePage.main)

    return handler
