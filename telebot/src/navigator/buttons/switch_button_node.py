from button_node import ButtonNode
from button_style import ButtonStyle

class SwitchButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    enabled: bool = True,
    data: str = "",
    key: str = "",
    style = ButtonStyle.default,
  ):
    self._enabled = enabled
    super().__init__(
      text = text,
      data = data,
      key = key,
      style = style,
    )

  @property
  def enabled(self) -> bool:
    return self._enabled
