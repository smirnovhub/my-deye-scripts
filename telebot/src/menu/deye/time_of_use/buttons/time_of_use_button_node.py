from typing import List, Optional

from telebot_sequential_choices import ButtonNode
from time_of_use_button_type import TimeOfUseButtonType

class TimeOfUseButtonNode(ButtonNode):
  def __init__(
    self,
    label: str,
    button_type: TimeOfUseButtonType,
    time_of_use_index: int,
    children: Optional[List["ButtonNode"]] = None,
  ):
    super().__init__(
      label = label,
      children = children,
    )

    self._button_type = button_type
    self._time_of_use_index = time_of_use_index

  @property
  def button_type(self) -> TimeOfUseButtonType:
    return self._button_type

  @property
  def time_of_use_index(self) -> int:
    return self._time_of_use_index
