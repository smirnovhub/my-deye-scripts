from enum import Enum
from typing import Any, List

from button_node import ButtonNode
from time_of_use_base_page import TimeOfUseBasePage
from time_of_use_times import TimeOfUseTimes
from break_button_node import BreakButtonNode
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from telebot_page_navigator import TelebotPageNavigator

class TimeOfUseHoursPage(TimeOfUseBasePage):
  def __init__(
    self,
    tou_times: TimeOfUseTimes,
    title: str,
    page_type: TimeOfUsePage,
    next_page_type: TimeOfUsePage,
  ):
    super().__init__()
    self._tou_times = tou_times
    self._title = title
    self._page_type = page_type
    self._next_page_type = next_page_type
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return self._page_type

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def prepare(self, **kwargs: Any):
    index = kwargs.get("time_of_use_line_index")
    if index is None:
      raise RuntimeError("time_of_use_line_index not found")

    self.check_bounds(self._tou_times.values, index)
    self._time_of_use_line_index = index

  def update(self) -> None:
    buttons: List[ButtonNode] = [
      ButtonNode(self._title),
      BreakButtonNode(),
    ]

    for i in range(24):
      if i > 0 and i % 4 == 0:
        buttons.append(BreakButtonNode())

      btn = TimeOfUseButtonNode(
        text = f"{i:02}",
        data = str(i),
        index = i,
      )

      self.register_button_handler(btn, self._create_hour_handler(i))
      buttons.append(btn)

    buttons.append(BreakButtonNode())
    buttons.append(self.register_button_handler(ButtonNode("Back"), self._handle_back))

    self._buttons = buttons

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      hour = int(text)
    except Exception:
      raise ValueError(f"Hour value should be from 0 to 23")

    if not (0 <= hour <= 23):
      raise ValueError(f"Hour value should be from 0 to 23")

    self._set_hour_and_go_next(navigator, hour)

  def _handle_back(self, navigator: TelebotPageNavigator):
    navigator.navigate(TimeOfUsePage.main)

  def _create_hour_handler(self, hour: int):
    def handler(navigator: TelebotPageNavigator) -> None:
      self._set_hour_and_go_next(navigator, hour)

    return handler

  def _set_hour_and_go_next(self, navigator: TelebotPageNavigator, hour: int) -> None:
    self._tou_times.values[self._time_of_use_line_index].hour = hour
    navigator.navigate(self._next_page_type, time_of_use_line_index = self._time_of_use_line_index)
