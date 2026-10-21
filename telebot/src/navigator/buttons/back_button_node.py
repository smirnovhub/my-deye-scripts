from button_node import ButtonNode
from button_style import ButtonStyle

class BackButtonNode(ButtonNode):
  def __init__(
    self,
    data: str = "",
    key: str = "",
    style = ButtonStyle.default,
  ):
    super().__init__(
      text = "Back",
      data = data,
      key = key,
      style = style,
    )
