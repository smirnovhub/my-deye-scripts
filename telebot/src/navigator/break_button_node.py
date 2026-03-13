from button_node import ButtonNode
from telebot_utils import TelebotUtils

class BreakButtonNode(ButtonNode):
  def __init__(self):
    super().__init__(TelebotUtils.row_break_str)
