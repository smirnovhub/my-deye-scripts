from enum import Enum
from typing import List

from button_node import ButtonNode
from time_of_use_data import TimeOfUsePowers
from break_button_node import BreakButtonNode
from pages.time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class TimeOfUsePowersPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_powers: TimeOfUsePowers,
  ):
    self.tou_powers = tou_powers
    self._back_button = ButtonNode("Back")
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.powers

  def prepare(self, time_of_use_line_index: int, **kwargs):
    self._time_of_use_line_index = time_of_use_line_index

  def update(self) -> None:
    self._buttons: List[ButtonNode] = [
      ButtonNode("Battery power, W:"),
      BreakButtonNode(),
    ]

    values = [
      ['250', '500', '1000'],
      ['1250', '1500', '2000'],
      ['2500', '3000', '3500'],
      ['4000', '5000', '6000'],
    ]

    for index, row in enumerate(values):
      # Add a row break before every row except the first one
      if index > 0:
        self._buttons.append(BreakButtonNode())

      for value in row:
        self._buttons.append(TimeOfUseButtonNode(
          text = str(value),
          index = index,
        ))

    self._buttons.append(BreakButtonNode())
    self._buttons.append(self._back_button)

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    if button.data == self._back_button.data:
      navigator.navigate(TimeOfUsePage.main)
    elif isinstance(button, TimeOfUseButtonNode):
      self.tou_powers.values[self._time_of_use_line_index] = int(button.text)
      navigator.navigate(TimeOfUsePage.main)

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons
