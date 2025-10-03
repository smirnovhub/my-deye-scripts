import time
import telebot

class TelebotFakeTestMessage:
  """
  Utility class to create fake `telebot.types.Message` objects for testing purposes.

  This class provides static methods to generate Telegram message objects
  without connecting to the Telegram API. Useful for unit tests and
  simulating bot interactions.

  Methods
  -------
  make(text: str, user_id: int = 1234, chat_id: int = 1234) -> telebot.types.Message
      Create a fake Message object with the given text, user ID, and chat ID.
      The message mimics a real Telegram message, including timestamp and sender info.
  """
  @staticmethod
  def make(
    text: str,
    user_id: int = 1234,
    chat_id: int = 1234,
  ) -> telebot.types.Message:
    """
    Generate a fake Telegram Message object.

    Parameters
    ----------
    text : str
        The message text.
    user_id : int, optional
        The sender's user ID (default is 1234).
    chat_id : int, optional
        The chat ID where the message is sent (default is 1234).

    Returns
    -------
    telebot.types.Message
        A Telegram Message object populated with the provided text and IDs.
    """
    payload = {
      "message_id": 1,
      "from": {
        "id": user_id,
        "is_bot": False,
        "first_name": "Tester",
        "username": "tester"
      },
      "chat": {
        "id": chat_id,
        "type": "private",
        "first_name": "Tester",
        "username": "tester"
      },
      "date": int(time.time()),
      "text": text
    }

    return telebot.types.Message.de_json(payload)
