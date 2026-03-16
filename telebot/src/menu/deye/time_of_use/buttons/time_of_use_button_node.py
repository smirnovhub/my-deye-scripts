from button_node import ButtonNode

class TimeOfUseButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    index: int,
    data: str = "",
  ):
    super().__init__(
      text = text,
      data = data,
    )
    self._index = index

  @property
  def index(self) -> int:
    return self._index
