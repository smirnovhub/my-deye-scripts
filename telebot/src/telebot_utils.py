import os
import threading
import time
import telebot

from typing import Union

def get_inline_button_by_data(
  message: telebot.types.Message,
  button_data: str,
) -> Union[telebot.types.InlineKeyboardButton, None]:
  """
  Retrieve an InlineKeyboardButton from a message by its callback_data.

  :param message: The Telegram message containing the inline keyboard
  :param button_data: The callback_data of the button to search for
  :return: The InlineKeyboardButton if found, otherwise None
  """
  # Get the reply_markup (inline keyboard) from the message
  markup = message.reply_markup
  if markup is None:
    return None

  # Iterate through each row of buttons in the keyboard
  for row in markup.keyboard:
    # Iterate through each button in the row
    for btn in row:
      # Check if the button's callback_data matches the requested data
      if btn.callback_data == button_data:
        return btn

  return None

def get_inline_button_by_text(
  message: telebot.types.Message,
  button_text: str,
) -> Union[telebot.types.InlineKeyboardButton, None]:
  """
  Retrieve an InlineKeyboardButton from a message by its text.

  :param message: The Telegram message containing the inline keyboard
  :param button_text: The text of the button to search for
  :return: The InlineKeyboardButton if found, otherwise None
  """
  markup = message.reply_markup
  if markup is None:
    return None

  for row in markup.keyboard:
    for btn in row:
      if btn.text == button_text:
        return btn

  return None

def remove_inline_buttons(bot: telebot.TeleBot, chat_id: int, message_id: int) -> None:
  """
  Safely remove inline buttons from a message.
  
  :param bot: TeleBot instance
  :param chat_id: Chat ID where the message was sent
  :param message_id: ID of the message to update
  """
  try:
    bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = None)
  except Exception:
    # Ignore errors (e.g., already removed, message deleted, not modified)
    pass

def remove_inline_buttons_with_delay(bot: telebot.TeleBot, chat_id: int, message_id: int, delay: float) -> None:
  """
  Schedule removal of inline buttons from a message after a delay.

  :param bot: TeleBot instance
  :param chat_id: Chat ID where the message was sent
  :param message_id: ID of the message
  :param delay: Time in seconds before removing buttons
  """
  if delay < 0.01:
    remove_inline_buttons(bot, chat_id, message_id)
    return

  timer = threading.Timer(delay, lambda: remove_inline_buttons(bot, chat_id, message_id))
  timer.daemon = True # thread won't block program exit
  timer.start()

def stop_bot(bot: telebot.TeleBot):
  bot.stop_bot()
  # exit will never fire if bot has stopped in right way
  time.sleep(30)
  os._exit(1)
