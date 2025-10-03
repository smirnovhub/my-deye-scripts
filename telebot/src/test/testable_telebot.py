import re
import logging
import telebot

from typing import List, Optional, Union
from telebot_fake_test_message import TelebotFakeTestMessage

class TestableTelebot(telebot.TeleBot):
  def __init__(self, token: str):
    super().__init__(token)
    self.messages: List[str] = []
    self.log = logging.getLogger()

  """
  TeleBot subclass for offline testing.
  All outgoing API calls are blocked.
  process_new_messages still works normally.
  """

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

  # --- Send methods ---
  def send_message(
    self,
    chat_id: Union[int, str],
    text: str,
    *args,
    **kwargs,
  ) -> telebot.types.Message:
    self.log.info(f"[BLOCKED SEND_MESSAGE] chat_id = {chat_id}, text =\n{text}")
    self.messages.append(text)
    return TelebotFakeTestMessage.make(text = text)

  def send_photo(self, *args, **kwargs):
    self.log.info("[BLOCKED SEND_PHOTO]")
    return None

  def send_document(self, *args, **kwargs):
    self.log.info("[BLOCKED SEND_DOCUMENT]")
    return None

  def send_audio(self, *args, **kwargs):
    self.log.info("[BLOCKED SEND_AUDIO]")
    return None

  def send_video(self, *args, **kwargs):
    self.log.info("[BLOCKED SEND_VIDEO]")
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
    self.log.info(f"[BLOCKED EDIT_MESSAGE_TEXT] chat={chat_id}, message_id={message_id}, text={text}")
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
      f"[BLOCKED EDIT_MESSAGE_REPLY_MARKUP] chat = {chat_id}, message_id = {message_id}, inline_message_id = {inline_message_id}"
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
    self.log.info(f"[BLOCKED DELETE_MESSAGE] chat = {chat_id}, message_id = {message_id}")
    return True

  def answer_callback_query(
    self,
    callback_query_id: str,
    text: Optional[str] = None,
    *args,
    **kwargs,
  ):
    """Block answer_callback_query to prevent network requests."""
    self.log.info(f"[BLOCKED ANSWER_CALLBACK_QUERY] id = {callback_query_id}, text = {text}")
    return True
