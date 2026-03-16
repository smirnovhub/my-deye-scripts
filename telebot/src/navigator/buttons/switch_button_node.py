from button_node import ButtonNode

class SwitchButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    enabled: bool = True,
    data: str = "",
  ):
    super().__init__(
      text = text,
      data = data,
    )

    self._enabled = enabled

  @property
  def enabled(self) -> bool:
    return self._enabled
