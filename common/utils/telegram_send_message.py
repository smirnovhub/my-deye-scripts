import logging
import requests

from http import HTTPStatus
from env_utils import EnvUtils

class Telegram:
  @staticmethod
  def send_private_telegram_message(message: str) -> None:
    token = EnvUtils.get_telegram_bot_api_token()
    chat_id = EnvUtils.get_telegram_private_chat_id()

    Telegram._send_telegram_message(
      message = message,
      token = token,
      chat_id = chat_id,
      message_type = 'private',
    )

  @staticmethod
  def send_public_telegram_message(message: str) -> None:
    token = EnvUtils.get_telegram_bot_api_token()
    chat_id = EnvUtils.get_telegram_public_chat_id()

    Telegram._send_telegram_message(
      message = message,
      token = token,
      chat_id = chat_id,
      message_type = 'public',
    )

  @staticmethod
  def _send_telegram_message(
    message: str,
    token: str,
    chat_id: str,
    message_type: str,
  ) -> None:

    logger = logging.getLogger()
    payload = {
      'chat_id': chat_id,
      'text': message[:3072],
      'parse_mode': 'HTML',
    }

    url = Telegram.get_api_url(token)

    try:
      response = requests.post(url, data = payload, timeout = 5)
      if response.status_code != HTTPStatus.OK:
        logger.info(f"Failed to send {message_type} telegram message: {response.text}")
    except Exception as e:
      logger.info(f'Failed to send {message_type} telegram message to {chat_id}: {str(e)}')

  @staticmethod
  def get_api_url(token: str) -> str:
    api_url = "https://api.telegram.org/bot{0}/sendMessage"
    return api_url.format(token)
