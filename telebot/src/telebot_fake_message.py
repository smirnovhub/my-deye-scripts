import copy
from telebot.types import Message
from telebot.types import User

class TelebotFakeMessage(Message):
  def __init__(self, message: Message, text: str, from_user: User):
    self.__dict__ = copy.deepcopy(message.__dict__)
    self.text = text
    self.from_user = from_user
