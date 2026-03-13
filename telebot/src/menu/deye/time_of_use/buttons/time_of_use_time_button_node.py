from time_of_use_button_node import TimeOfUseButtonNode

class TimeOfUseTimeButtonNode(TimeOfUseButtonNode):
  def __init__(
    self,
    text: str,
    index: int,
  ):
    super().__init__(
      text = text,
      index = index,
    )
