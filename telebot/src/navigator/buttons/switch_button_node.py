from button_node import ButtonNode
from button_style import ButtonStyle

class SwitchButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    enabled: bool = True,
    data: str = "",
    style = ButtonStyle.default,
  ):
    super().__init__(
      text = text,
      data = data,
      style = style,
    )

    self._enabled = enabled

  @property
  def enabled(self) -> bool:
    return self._enabled
