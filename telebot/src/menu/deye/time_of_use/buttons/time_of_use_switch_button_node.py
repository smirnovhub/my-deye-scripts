from typing import List, Optional

from common_utils import CommonUtils
from telebot_sequential_choices import ButtonNode
from time_of_use_button_node import TimeOfUseButtonNode
from time_of_use_button_type import TimeOfUseButtonType

class TimeOfUseSwitchButtonNode(TimeOfUseButtonNode):
  def __init__(
    self,
    enabled: bool,
    button_type: TimeOfUseButtonType,
    time_of_use_index: int,
    children: Optional[List["ButtonNode"]] = None,
  ):
    super().__init__(
      label = self._get_label(enabled),
      button_type = button_type,
      time_of_use_index = time_of_use_index,
      children = children,
    )

    self._enabled = enabled

  @property
  def is_enabled(self) -> bool:
    return self._enabled

  def set_enabled(self, enabled: bool) -> None:
    self._enabled = enabled
    self.set_label(self._get_label(enabled))

  def _get_label(self, enabled: bool) -> str:
    return CommonUtils.large_green_circle_emoji if enabled else CommonUtils.large_red_circle_emoji
