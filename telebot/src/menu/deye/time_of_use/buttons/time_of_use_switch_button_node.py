from common_utils import CommonUtils
from switch_button_node import SwitchButtonNode

class TimeOfUseSwitchButtonNode(SwitchButtonNode):
  def __init__(
    self,
    enabled: bool,
  ):
    super().__init__(
      text = "",
      enabled = enabled,
    )

  @property
  def text(self) -> str:
    return CommonUtils.large_green_circle_emoji if self.enabled else CommonUtils.large_red_circle_emoji
