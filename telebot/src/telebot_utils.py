import threading
import telebot

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
  timer.daemon = True  # thread won't block program exit
  timer.start()
