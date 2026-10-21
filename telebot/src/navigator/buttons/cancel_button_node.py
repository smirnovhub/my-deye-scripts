from button_node import ButtonNode
from button_style import ButtonStyle

class CancelButtonNode(ButtonNode):
  def __init__(
    self,
    data: str = "",
    key: str = "",
    style = ButtonStyle.default,
  ):
    super().__init__(
      text = "Cancel",
      data = data,
      key = key,
      style = style,
    )
