import os
import re
import logging
import telebot

from typing import List, Union
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_deye_helper import get_object_as_str
from deye_utils import ensure_dir_exists

class TestableTelebot(telebot.TeleBot):
  """
  A test-friendly subclass of `telebot.TeleBot` for unit testing and
  simulating Telegram bot behavior without sending real messages.

  This class overrides message sending, editing, and deletion methods to:
    - Log actions instead of performing network calls.
    - Store sent message texts internally for test assertions.
    - Provide simple fake responses mimicking Telegram API objects.

  Features
  --------
  - `messages`: a list of all message texts sent during testing.
  - `clear_messages()`: clears the stored messages.
  - `is_messages_contains(text)`: checks if any sent message contains the given text.
  - `is_messages_contains_regex(pattern)`: checks if any sent message matches a regex pattern.
  - Overrides `send_message`, `send_photo`, `send_document`, `send_audio`, `send_video`
    to avoid real network calls while logging actions.
  - Overrides `edit_message_text`, `edit_message_reply_markup`, `delete_message`,
    `answer_callback_query` for test-friendly logging and return values.

  Notes
  -----
  - Intended solely for testing and development; does not communicate with Telegram.
  - `TelebotFakeTestMessage` is used to simulate `Message` objects returned by `send_message`.
  """

  telebot_test_log_file_name = 'data/logs/telebot_telegram_test.log'

  def __init__(self, token: str):
    super().__init__(token)
    self.messages: List[str] = []
    self.log = logging.getLogger()

    ensure_dir_exists(os.path.dirname(TestableTelebot.telebot_test_log_file_name))

    if os.path.exists(TestableTelebot.telebot_test_log_file_name):
      os.remove(TestableTelebot.telebot_test_log_file_name)

    logging.basicConfig(
      filename = TestableTelebot.telebot_test_log_file_name,
      filemode = 'w',
      level = logging.INFO,
      format = "[%(asctime)s] [%(levelname)s] %(message)s",
      datefmt = "%Y-%m-%d %H:%M:%S",
    )

  def clear_messages(self):
    self.messages.clear()

  def is_messages_contains(self, text: str) -> bool:
    for message in self.messages:
      if text.lower() in message.lower():
        return True
    return False

  def is_messages_contains_regex(self, pattern: str) -> bool:
    for message in self.messages:
      if re.search(pattern, message, flags = re.IGNORECASE):
        return True
    return False

  def set_my_commands(self, *args, **kwargs) -> bool:
    self.log.info(f'[set_my_commands] {self.get_args(*args, **kwargs)}')
    return True

  def set_chat_menu_button(self, *args, **kwargs) -> bool:
    self.log.info(f'[set_chat_menu_button] {self.get_args(*args, **kwargs)}')
    return True

  # Just for logging
  def process_new_messages(self, new_messages: List[telebot.types.Message], *args, **kwargs):
    for message in new_messages:
      self.log.info(f'[process_new_messages] {self.get_args(json = message.json, *args, **kwargs)}')
    super().process_new_messages(new_messages)

  # Just for logging
  def process_new_callback_query(self, new_callback_queries: List[telebot.types.CallbackQuery], *args, **kwargs):
    for callback_query in new_callback_queries:
      self.log.info(f'[process_new_callback_query] {self.get_args(data = callback_query.data, *args, **kwargs)}')
    super().process_new_callback_query(new_callback_queries)

  def send_message(
    self,
    chat_id: Union[int, str],
    text: str,
    *args,
    **kwargs,
  ) -> telebot.types.Message:
    self.log.info(f'[send_message] {self.get_args(chat_id = chat_id, text = text, *args, **kwargs)}')
    self.messages.append(text)
    return TelebotFakeTestMessage.make(text = text, chat_id = chat_id)

  def send_photo(self, *args, **kwargs):
    self.log.info("[send_photo]")
    return None

  def send_document(self, *args, **kwargs):
    self.log.info(f'[send_document] {self.get_args(*args, **kwargs)}')
    return None

  def send_audio(self, *args, **kwargs):
    self.log.info(f'[send_audio] {self.get_args(*args, **kwargs)}')
    return None

  def send_video(self, *args, **kwargs):
    self.log.info(f'[send_video] {self.get_args(*args, **kwargs)}')
    return None

  def send_media_group(self, *args, **kwargs):
    self.log.info(f'[send_media_group] {self.get_args(*args, **kwargs)}')

  def edit_message_text(self, *args, **kwargs):
    self.log.info(f'[edit_message_text] {self.get_args(*args, **kwargs)}')
    return None

  def edit_message_reply_markup(self, *args, **kwargs) -> Union[telebot.types.Message, bool]:
    self.log.info(f'[edit_message_reply_markup] {self.get_args(*args, **kwargs)}')
    return True

  def delete_message(self, *args, **kwargs) -> bool:
    self.log.info(f'[delete_message] {self.get_args(*args, **kwargs)}')
    return True

  def answer_callback_query(self, *args, **kwargs):
    self.log.info(f'[answer_callback_query] {self.get_args(*args, **kwargs)}')
    return True

  def get_updates(self, *args, **kwargs):
    self.log.info(f'[get_updates] {self.get_args(*args, **kwargs)}')

  def infinity_polling(self, *args, **kwargs):
    self.log.info(f'[infinity_polling] {self.get_args(*args, **kwargs)}')

  def polling(self, *args, **kwargs):
    self.log.info(f'[polling] {self.get_args(*args, **kwargs)}')

  def stop_polling(self, *args, **kwargs):
    self.log.info(f'[stop_polling] {self.get_args(*args, **kwargs)}')

  def get_args(self, *args, **kwargs) -> str:
    """
    Return all arguments (positional and keyword) as a readable string.
    Each argument (positional or keyword) starts on a new line.
    Complex objects are formatted using debug_str().
    """
    parts = []

    def fmt(value):
      """Format a value for logging."""
      s = get_object_as_str(value)
      # Replace literal "\n" with actual newline
      if isinstance(value, str):
        s = s.replace(r"\n", "\n")
      return s

    # If a single positional argument is a dict and no kwargs, treat as kwargs
    if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
      kwargs = args[0]
      args = ()

    # Format positional arguments
    for i, arg in enumerate(args):
      parts.append(f"{i}: {fmt(arg)}")

    # Format keyword arguments
    for k, v in kwargs.items():
      parts.append(f"{k} = {fmt(v)}")

    # Join everything with newline
    return ",\n".join(parts)
