from enum import Enum
from typing import List

from button_node import ButtonNode
from time_of_use_data import TimeOfUseTimes
from break_button_node import BreakButtonNode
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class TimeOfUseHoursPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_times: TimeOfUseTimes,
    title: str,
    page_type: TimeOfUsePage,
    next_page_type: TimeOfUsePage,
  ):
    self.tou_times = tou_times
    self._title = title
    self._back_button = ButtonNode("Back")
    self._page_type = page_type
    self._next_page_type = next_page_type
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return self._page_type

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, time_of_use_line_index: int, **kwargs):
    self._time_of_use_line_index = time_of_use_line_index

  def update(self) -> None:
    self._buttons: List[ButtonNode] = [
      ButtonNode(self._title),
      BreakButtonNode(),
    ]

    for index, value in enumerate(range(24)):
      # Insert row break every 6 elements (except before the first one)
      if index > 0 and index % 4 == 0:
        self._buttons.append(BreakButtonNode())

      self._buttons.append(TimeOfUseButtonNode(
        text = f"{value:02}",
        data = str(value),
        index = index,
      ))

    self._buttons.append(BreakButtonNode())
    self._buttons.append(self._back_button)

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    if button.id == self._back_button.id:
      navigator.navigate(TimeOfUsePage.main)
    elif isinstance(button, TimeOfUseButtonNode):
      self.tou_times.values[self._time_of_use_line_index].hour = int(button.data)
      navigator.navigate(self._next_page_type, time_of_use_line_index = self._time_of_use_line_index)
