from common_utils import CommonUtils
from switch_button_node import SwitchButtonNode

class TimeOfUseSwitchButtonNode(SwitchButtonNode):
  def __init__(
    self,
    enabled: bool,
    index: int,
  ):
    super().__init__(
      text = self._get_text(enabled),
      enabled = enabled,
    )

    self._index = index

  @property
  def index(self) -> int:
    return self._index

  @property
  def text(self) -> str:
    return self._get_text(self._enabled)

  def _get_text(self, enabled: bool) -> str:
    return CommonUtils.large_green_circle_emoji if enabled else CommonUtils.large_red_circle_emoji
