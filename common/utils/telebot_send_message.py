import re
import requests

from telebot_credentials import TelebotCredentials

_api_url = "https://api.telegram.org/bot{0}/sendMessage"

def send_private_telegram_message(message: str) -> None:
  try:
    if is_bot_token_correct(TelebotCredentials.BOT_API_TOKEN) and is_chat_id_correct(
        TelebotCredentials.PRIVATE_CHAT_ID):
      payload = {
        'chat_id': TelebotCredentials.PRIVATE_CHAT_ID,
        'text': message[:3072],
        'parse_mode': 'HTML',
      }

      url = _api_url.format(TelebotCredentials.BOT_API_TOKEN)
      response = requests.post(url, data = payload, timeout = 5)
      if response.status_code != requests.codes.ok:
        print(f"Failed to send private telegram message: {response.text}")
  except:
    print(f'Failed to send private telegram messag to {TelebotCredentials.PRIVATE_CHAT_ID}')

def send_public_telegram_message(message: str) -> None:
  try:
    if is_bot_token_correct(TelebotCredentials.BOT_API_TOKEN) and is_chat_id_correct(TelebotCredentials.PUBLIC_CHAT_ID):
      payload = {
        'chat_id': TelebotCredentials.PUBLIC_CHAT_ID,
        'text': message[:3072],
        'parse_mode': 'HTML',
      }

      url = _api_url.format(TelebotCredentials.BOT_API_TOKEN)
      response = requests.post(url, data = payload, timeout = 5)
      if response.status_code != requests.codes.ok:
        print(f"Failed to send public telegram message: {response.text}")
  except:
    print(f'Failed to send public telegram messag to {TelebotCredentials.PUBLIC_CHAT_ID}')

def is_bot_token_correct(token: str) -> bool:
  pattern = re.compile(r"^\d+:.+$")
  if pattern.match(token):
    return True
  else:
    print(f'Bot token is invalid')
    return False

def is_chat_id_correct(chat_id: str) -> bool:
  pattern = re.compile(r"^-?\d+$")
  if pattern.match(str(chat_id)):
    return True
  else:
    print(f"Chat id '{chat_id}' is invalid")
    return False
