import requests

from telebot_credentials import *

def send_private_telegram_message(message):
  url = f"https://api.telegram.org/bot{BOT_API_TOKEN}/sendMessage?chat_id={PRIVATE_CHAT_ID}&parse_mode=HTML&text={message}"
  requests.get(url)
