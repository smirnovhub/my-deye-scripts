import copy
from telebot.types import Message
from telebot.types import User

class TelebotFakeMessage(Message):
  """
  A subclass of `telebot.types.Message` that creates a modified copy of an existing message.

  This class is useful when you want to simulate or modify an incoming message,
  for example to change its text or sender, while preserving all the original fields.
  """
  def __init__(self, message: Message, text: str, from_user: User):
    """
    Initialize a fake message based on an existing one.

    The constructor deep-copies the internal dictionary of the original message,
    then overrides its `text` and `from_user` fields with the provided values.

    Args:
        message (Message): The original message object to copy.
        text (str): The new text content to set for the fake message.
        from_user (User): The user who should appear as the sender of the fake message.
    """
    self.__dict__ = copy.deepcopy(message.__dict__)
    self.text = text
    self.from_user = from_user
