import re
import requests

from telebot_credentials import TelebotCredentials

_api_url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&parse_mode=HTML&text={2}"

def send_private_telegram_message(message):
  try:
    if is_bot_token_correct(TelebotCredentials.BOT_API_TOKEN) and is_chat_id_correct(
        TelebotCredentials.PRIVATE_CHAT_ID):
      url = _api_url.format(TelebotCredentials.BOT_API_TOKEN, TelebotCredentials.PRIVATE_CHAT_ID, message)
      requests.get(url)
  except:
    print(f'Error while sending message to {TelebotCredentials.PRIVATE_CHAT_ID}')

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
