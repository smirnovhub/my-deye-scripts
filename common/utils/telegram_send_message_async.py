import logging
import aiohttp

from http import HTTPStatus
from env_utils import EnvUtils
from telegram_send_message import Telegram

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

    if not (Telegram.is_bot_token_correct(token, logger) and Telegram.is_chat_id_correct(chat_id, logger)):
      return

    payload = {
      'chat_id': chat_id,
      'text': message[:3072],
      'parse_mode': 'HTML',
    }

    url = Telegram.get_api_url(token)

    try:
      # We use a timeout to prevent the coroutine from hanging indefinitely
      timeout = aiohttp.ClientTimeout(total = 5)
      async with aiohttp.ClientSession(timeout = timeout) as session:
        async with session.post(url, data = payload) as response:
          if response.status != HTTPStatus.OK:
            response_text = await response.text()
            logger.info(f"Failed to send {message_type} telegram message: {response_text}")
    except Exception as e:
      # Caught a specific exception or generic error to prevent crash
      logger.info(f'Failed to send {message_type} telegram message to {chat_id}: {str(e)}')
