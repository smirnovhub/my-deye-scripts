import os
import re
import logging
import telebot

from typing import List, Optional, Union
from telebot_fake_test_message import TelebotFakeTestMessage

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

  telebot_test_log_file_name = 'data/telebot_test_log.txt'

  def __init__(self, token: str):
    super().__init__(token)
    self.messages: List[str] = []
    self.log = logging.getLogger()

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

  def set_my_commands(
    self,
    *args,
    **kwargs,
  ) -> bool:
    self.log.info("[set_my_commands]")
    return True

  def set_chat_menu_button(
    self,
    *args,
    **kwargs,
  ) -> bool:
    self.log.info("[set_chat_menu_button]")
    return True

  # --- Send methods ---
  def send_message(
    self,
    chat_id: Union[int, str],
    text: str,
    *args,
    **kwargs,
  ) -> telebot.types.Message:
    self.log.info(f"[send_message] chat_id = {chat_id}, text =\n{text}")
    self.messages.append(text)
    return TelebotFakeTestMessage.make(text = text)

  def send_photo(self, *args, **kwargs):
    self.log.info("[send_photo]")
    return None

  def send_document(self, *args, **kwargs):
    self.log.info("[send_document]")
    return None

  def send_audio(self, *args, **kwargs):
    self.log.info("[send_audio]")
    return None

  def send_video(self, *args, **kwargs):
    self.log.info("[send_video]")
    return None

  # --- Edit message ---
  def edit_message_text(
    self,
    text: str,
    chat_id: Optional[Union[int, str]] = None,
    message_id: Optional[int] = None,
    *args,
    **kwargs,
  ):
    self.log.info(f"[edit_message_text] chat={chat_id}, message_id={message_id}, text={text}")
    return None

  def edit_message_reply_markup(
    self,
    chat_id: Optional[Union[int, str]] = None,
    message_id: Optional[int] = None,
    inline_message_id: Optional[str] = None,
    *args,
    **kwargs,
  ) -> Union[telebot.types.Message, bool]:
    self.log.info(
      f"[edit_message_reply_markup] chat = {chat_id}, message_id = {message_id}, inline_message_id = {inline_message_id}"
    )
    return True

  # --- Delete message ---
  def delete_message(
    self,
    chat_id: Optional[Union[int, str]] = None,
    message_id: Optional[int] = None,
    *args,
    **kwargs,
  ) -> bool:
    self.log.info(f"[delete_message] chat = {chat_id}, message_id = {message_id}")
    return True

  def answer_callback_query(
    self,
    callback_query_id: str,
    text: Optional[str] = None,
    *args,
    **kwargs,
  ):
    self.log.info(f"[answer_callback_query] id = {callback_query_id}, text = {text}")
    return True
