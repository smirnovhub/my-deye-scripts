import time
import telebot

class TelebotFakeTestMessage:
  @staticmethod
  def make(
    text: str,
    user_id: int = 1234,
    chat_id: int = 1234,
  ) -> telebot.types.Message:
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
