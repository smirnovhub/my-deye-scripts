from enum import Enum
from typing import List

from button_node import ButtonNode
from time_of_use_base_page import TimeOfUseBasePage
from time_of_use_data import TimeOfUseSocs
from break_button_node import BreakButtonNode
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_page_navigator import TelebotPageNavigator

class TimeOfUseSocsPage(TimeOfUseBasePage):
  def __init__(
    self,
    tou_socs: TimeOfUseSocs,
  ):
    super().__init__()
    self._tou_socs = tou_socs
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.socs

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, time_of_use_line_index: int, **kwargs):
    self.check_upper_bounds(self._tou_socs.values, time_of_use_line_index)
    self._time_of_use_line_index = time_of_use_line_index

  def update(self) -> None:
    self.clear_button_handlers()

    buttons: List[ButtonNode] = [
      ButtonNode("Battery SOC, %:"),
      BreakButtonNode(),
    ]

    values = [
      [15, 20, 25, 30, 35],
      [40, 45, 50, 55, 60],
      [65, 70, 75, 80, 85],
      [90, 93, 95, 97, 100],
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

        self.register_button_handler(btn, self._create_soc_handler(value))
        buttons.append(btn)

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))

    self._buttons = buttons

  def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(TimeOfUsePage.main)

  def _create_soc_handler(self, soc: int):
    def handler(navigator: TelebotPageNavigator) -> None:
      if self._time_of_use_line_index < 0:
        # Replace all elements in the list with the new value
        self._tou_socs.values[:] = [soc] * len(self._tou_socs.values)
      else:
        self._tou_socs.values[self._time_of_use_line_index] = soc

      navigator.navigate(TimeOfUsePage.main)

    return handler
