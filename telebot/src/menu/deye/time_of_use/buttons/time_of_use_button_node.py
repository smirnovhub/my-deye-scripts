from button_node import ButtonNode
from button_style import ButtonStyle

class TimeOfUseButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    index: int,
    data: str = "",
    style = ButtonStyle.default,
  ):
    super().__init__(
      text = text,
      data = data,
      style = style,
    )
    self._index = index

  @property
  def index(self) -> int:
    return self._index
