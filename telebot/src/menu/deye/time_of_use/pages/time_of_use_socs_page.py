from enum import Enum
from typing import List

from button_node import ButtonNode
from time_of_use_data import TimeOfUseSocs
from break_button_node import BreakButtonNode
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class TimeOfUseSocsPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_socs: TimeOfUseSocs,
  ):
    self.tou_socs = tou_socs
    self._back_button = ButtonNode("Back")
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.socs

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, time_of_use_line_index: int, **kwargs):
    self._time_of_use_line_index = time_of_use_line_index

  def update(self) -> None:
    self._buttons: List[ButtonNode] = [
      ButtonNode("Battery SOC, %:"),
      BreakButtonNode(),
    ]

    values = [
      ['15', '20', '25', '30', '35'],
      ['40', '45', '50', '55', '60'],
      ['65', '70', '75', '80', '85'],
      ['90', '93', '95', '97', '100'],
    ]

    for index, row in enumerate(values):
      # Add a row break before every row except the first one
      if index > 0:
        self._buttons.append(BreakButtonNode())

      for value in row:
        self._buttons.append(TimeOfUseButtonNode(
          text = str(value),
          data = str(value),
          index = index,
        ))

    self._buttons.append(BreakButtonNode())
    self._buttons.append(self._back_button)

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    if button.id == self._back_button.id:
      navigator.navigate(TimeOfUsePage.main)
    elif isinstance(button, TimeOfUseButtonNode):
      self.tou_socs.values[self._time_of_use_line_index] = int(button.data)
      navigator.navigate(TimeOfUsePage.main)
