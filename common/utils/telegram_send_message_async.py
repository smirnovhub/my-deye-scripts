import logging

from http import HTTPStatus
from typing import Optional
from env_utils import EnvUtils
from telegram_send_message import Telegram
from http_session_singleton_async import HttpSessionSingletonAsync

class TelegramAsync:
  @staticmethod
  async def send_private_telegram_message(
    message: str,
    logger: Optional[logging.Logger] = None,
  ) -> None:
    logger = logger or logging.getLogger()

    try:
      token = EnvUtils.get_telegram_bot_api_token()
      chat_id = EnvUtils.get_telegram_private_chat_id()

      await TelegramAsync._send_telegram_message(
        message = message,
        token = token,
        chat_id = chat_id,
        message_type = 'private',
        logger = logger,
      )
    except Exception as e:
      # Caught a specific exception or generic error to prevent crash
      logger.error(f'Failed to send private telegram message: {e}')

  @staticmethod
  async def send_public_telegram_message(
    message: str,
    logger: Optional[logging.Logger] = None,
  ) -> None:
    logger = logger or logging.getLogger()

    try:
      token = EnvUtils.get_telegram_bot_api_token()
      chat_id = EnvUtils.get_telegram_public_chat_id()

      await TelegramAsync._send_telegram_message(
        message = message,
        token = token,
        chat_id = chat_id,
        message_type = 'public',
        logger = logger,
      )
    except Exception as e:
      # Caught a specific exception or generic error to prevent crash
      logger.error(f'Failed to send public telegram message: {e}')

  @staticmethod
  async def _send_telegram_message(
    message: str,
    token: str,
    chat_id: str,
    message_type: str,
    logger: logging.Logger,
  ) -> None:
    payload = {
      'chat_id': chat_id,
      'text': message[:3072],
      'parse_mode': 'HTML',
    }

    session = await HttpSessionSingletonAsync.get_session()
    async with session.post(Telegram.get_api_url(token), data = payload) as response:
      if response.status != HTTPStatus.OK:
        text = await response.text()
        logger.error(f"Failed to send {message_type} telegram message, "
                     f"chat_id = {chat_id}, status {response.status}: {text}")
