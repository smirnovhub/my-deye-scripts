from typing import List, Optional

from button_node import ButtonNode

class SequentialChoiceButton(ButtonNode):
  def __init__(
    self,
    text: str,
    data: str = "",
    max_children_per_row: int = 3,
    children: Optional[List["SequentialChoiceButton"]] = None,
  ):
    super().__init__(
      text = text,
      data = data,
    )
    self._max_children_per_row = max_children_per_row
    self._children = children if children else []

  @property
  def max_children_per_row(self) -> int:
    return self._max_children_per_row

  @property
  def children(self) -> List["SequentialChoiceButton"]:
    return self._children
