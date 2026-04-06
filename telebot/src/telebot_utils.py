import json
import os
import signal
import time
import threading

import requests
import telebot

from typing import Any, Dict, List, Optional, Sequence

from env_utils import EnvUtils
from button_node import ButtonNode
from button_style import ButtonStyle
from telebot_constants import TelebotConstants

class TelebotUtils:
  row_break_str = '!break!'

  @staticmethod
  def get_data_dir() -> str:
    log_name = EnvUtils.get_log_name()
    return TelebotConstants.data_dir.format(log_name)

  @staticmethod
  def get_inline_button_by_data(
    message: telebot.types.Message,
    button_data: str,
  ) -> Optional[telebot.types.InlineKeyboardButton]:
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

  @staticmethod
  def get_inline_button_by_text(
    message: telebot.types.Message,
    button_text: str,
  ) -> Optional[telebot.types.InlineKeyboardButton]:
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

  @staticmethod
  def remove_message(bot: telebot.TeleBot, chat_id: int, message_id: int) -> None:
    """
    Safely remove a message.
    
    :param bot: TeleBot instance
    :param chat_id: Chat ID where the message was sent
    :param message_id: ID of the message to update
    """
    try:
      bot.delete_message(chat_id, message_id)
    except Exception:
      pass

  @staticmethod
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

  @staticmethod
  def remove_message_with_delay(bot: telebot.TeleBot, chat_id: int, message_id: int, delay: float) -> None:
    """
    Schedule removal of a message after a delay.

    :param bot: TeleBot instance
    :param chat_id: Chat ID where the message was sent
    :param message_id: ID of the message
    :param delay: Time in seconds before removing buttons
    """
    if delay < 0.01:
      TelebotUtils.remove_message(bot, chat_id, message_id)
      return

    timer = threading.Timer(delay, lambda: TelebotUtils.remove_message(bot, chat_id, message_id))
    timer.daemon = True # thread won't block program exit
    timer.start()

  @staticmethod
  def remove_inline_buttons_with_delay(bot: telebot.TeleBot, chat_id: int, message_id: int, delay: float) -> None:
    """
    Schedule removal of inline buttons from a message after a delay.

    :param bot: TeleBot instance
    :param chat_id: Chat ID where the message was sent
    :param message_id: ID of the message
    :param delay: Time in seconds before removing buttons
    """
    if delay < 0.01:
      TelebotUtils.remove_inline_buttons(bot, chat_id, message_id)
      return

    timer = threading.Timer(delay, lambda: TelebotUtils.remove_inline_buttons(bot, chat_id, message_id))
    timer.daemon = True # thread won't block program exit
    timer.start()

  @staticmethod
  def get_keyboard_for_buttons(
    buttons: Sequence[ButtonNode],
    data_prefix: str = '',
    max_per_row: int = -1,
  ) -> telebot.types.InlineKeyboardMarkup:
    """
    Build an inline keyboard where:
      - buttons is a list of ButtonNode objects,
      - button.text is button text,
      - button.data is callback_data string.
    Buttons are arranged in rows with up to max_per_row buttons each.
    """
    keyboard = telebot.types.InlineKeyboardMarkup()
    row: List[telebot.types.InlineKeyboardButton] = []

    for button in buttons:
      # Check for row break in either text or data
      if TelebotUtils.row_break_str in (button.text, button.data):
        # Commit the current row (if not empty) and start a new one
        if row:
          keyboard.row(*row)
          row = []
        continue

      if button.data.startswith("/"):
        callback_data = button.data
      else:
        callback_data = data_prefix + str(button.id)

      btn = telebot.types.InlineKeyboardButton(
        text = button.text,
        callback_data = callback_data,
        style = button.style.name if button.style != ButtonStyle.default else None,
      )

      row.append(btn)

      # Commit row if it's full
      if len(row) == max_per_row:
        keyboard.row(*row)
        row = []

    # Add remaining buttons in the last row
    if row:
      keyboard.row(*row)

    return keyboard

  @staticmethod
  def get_response_message(response_text: str) -> str:
    """
    Extract 'result' or 'detail' from the JSON response and always return a string.
    """
    try:
      # Check if the response body is valid JSON
      data: Dict[str, Any] = json.loads(response_text)

      # If the response is a list or not a dictionary, we can't access keys
      if not isinstance(data, dict):
        return str(data)

      # Priority: 'result' -> 'detail' -> empty string
      # We use str() to ensure the return type is always a string
      if 'result' in data and data['result'] is not None:
        return str(data['result'])

      if 'detail' in data and data['detail'] is not None:
        return str(data['detail'])

      return str(data)

    except (requests.exceptions.JSONDecodeError, ValueError):
      # Fallback if the body is not valid JSON (e.g., empty or HTML)
      return "Wrong json response"

  @staticmethod
  def make_callback_query_filter(prefix: str):
    """
    Creates a callback query filter function for use with TeleBot's
    `callback_query_handler`.

    The returned function checks whether the received `CallbackQuery`
    object has non-empty `data` and whether it starts with the specified
    prefix string. Useful for registering different handlers for
    callback commands with distinct prefixes.

    Args:
        prefix (str): The prefix that `call.data` must start with (e.g., "/").

    Returns:
        A filter function compatible with `callback_query_handler(func=...)`
        that returns True when the callback data starts with the given prefix.
    """
    def filter_func(call):
      return isinstance(call, telebot.types.CallbackQuery) and call.data and call.data.startswith(prefix)

    return filter_func

  @staticmethod
  def forward_next(bot: telebot.TeleBot, message: telebot.types.Message) -> bool:
    is_forward = message.forward_from_chat is not None and message.forward_from_chat.username is not None
    # Forward new commands or forwarded message to the bot
    if is_forward or message.text.startswith('/'):
      bot.process_new_messages([message])
      return True
    return False

  @staticmethod
  def stop_bot(bot: telebot.TeleBot):
    """
    Gracefully stops the running TeleBot instance and terminates the process.

    This method first calls `bot.stop_bot()` to stop all polling and background
    threads associated with the TeleBot instance. If the bot shuts down correctly,
    the process should naturally exit. However, as a safeguard, the method waits
    a minute and then forcefully terminates the process using `os._exit(1)`.

    Args:
        bot (telebot.TeleBot): The TeleBot instance to stop.
    """
    time.sleep(1)
    signal.raise_signal(signal.SIGTERM)
    time.sleep(30)
    # Exit will never fire if bot has stopped in right way
    os._exit(1)
