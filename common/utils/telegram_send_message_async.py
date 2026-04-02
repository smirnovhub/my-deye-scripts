import logging

from http import HTTPStatus
from env_utils import EnvUtils
from telegram_send_message import Telegram
from http_session_singleton_async import HttpSessionSingletonAsync

class TelegramAsync:
  @staticmethod
  async def send_private_telegram_message(message: str) -> None:
    token = EnvUtils.get_telegram_bot_api_token()
    chat_id = EnvUtils.get_telegram_private_chat_id()

    await TelegramAsync._send_telegram_message(
      message = message,
      token = token,
      chat_id = chat_id,
      message_type = 'private',
    )

  @staticmethod
  async def send_public_telegram_message(message: str) -> None:
    token = EnvUtils.get_telegram_bot_api_token()
    chat_id = EnvUtils.get_telegram_public_chat_id()

    await TelegramAsync._send_telegram_message(
      message = message,
      token = token,
      chat_id = chat_id,
      message_type = 'public',
    )

  @staticmethod
  async def _send_telegram_message(
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
      session = await HttpSessionSingletonAsync.get_session()
      async with session.post(url, data = payload) as response:
        if response.status != HTTPStatus.OK:
          response_text = await response.text()
          logger.info(f"Failed to send {message_type} telegram message: {response_text}")
    except Exception as e:
      # Caught a specific exception or generic error to prevent crash
      logger.info(f'Failed to send {message_type} telegram message to {chat_id}: {str(e)}')
