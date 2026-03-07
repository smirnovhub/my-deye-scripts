import re
import requests

from env_utils import EnvUtils

_api_url = "https://api.telegram.org/bot{0}/sendMessage"

def send_private_telegram_message(message: str) -> None:
  token = EnvUtils.get_telegram_bot_api_token()
  chat_id = EnvUtils.get_telegram_private_chat_id()

  _send_telegram_message(
    message = message,
    token = token,
    chat_id = chat_id,
    log_str = 'private',
  )

def send_public_telegram_message(message: str) -> None:
  token = EnvUtils.get_telegram_bot_api_token()
  chat_id = EnvUtils.get_telegram_public_chat_idn()

  _send_telegram_message(
    message = message,
    token = token,
    chat_id = chat_id,
    log_str = 'public',
  )

def _send_telegram_message(
  message: str,
  token: str,
  chat_id: str,
  log_str: str,
) -> None:

  try:
    if _is_bot_token_correct(token) and _is_chat_id_correct(chat_id):
      payload = {
        'chat_id': chat_id,
        'text': message[:3072],
        'parse_mode': 'HTML',
      }

      url = _api_url.format(token)
      response = requests.post(url, data = payload, timeout = 5)
      if response.status_code != requests.codes.ok:
        print(f"Failed to send {log_str} telegram message: {response.text}")
  except:
    print(f'Failed to send {log_str} telegram message to {chat_id}')

def _is_bot_token_correct(token: str) -> bool:
  pattern = re.compile(r"^\d+:.+$")
  if pattern.match(token):
    return True
  else:
    print(f'Bot token is invalid')
    return False

def _is_chat_id_correct(chat_id: str) -> bool:
  pattern = re.compile(r"^-?\d+$")
  if pattern.match(str(chat_id)):
    return True
  else:
    print(f"Chat id '{chat_id}' is invalid")
    return False
