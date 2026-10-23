from telebot_buttons import *
from common_utils import CommonUtils

class TimeOfUseSwitchButtonNode(SwitchButtonNode):
  def __init__(
    self,
    enabled: bool,
    text = "",
    key: str = "",
  ):
    super().__init__(
      text = text,
      key = key,
      enabled = enabled,
    )

  @property
  def text(self) -> str:
    txt = super().text
    sign = CommonUtils.large_green_circle_emoji if self.enabled else CommonUtils.large_red_circle_emoji
    return f"{sign} {txt}" if txt else sign
