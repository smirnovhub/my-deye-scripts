import requests

from telebot_credentials import (
  BOT_API_TOKEN,
  PRIVATE_CHAT_ID,
)

def send_private_telegram_message(message):
  try:
    url = f"https://api.telegram.org/bot{BOT_API_TOKEN}/sendMessage?chat_id={PRIVATE_CHAT_ID}&parse_mode=HTML&text={message}"
    requests.get(url)
  except:
    print(f'Error while sending message to {PRIVATE_CHAT_ID}')
