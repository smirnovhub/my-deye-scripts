from button_node import ButtonNode

class TimeOfUseButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    index: int,
  ):
    super().__init__(text = text)
    self._index = index

  @property
  def index(self) -> int:
    return self._index
