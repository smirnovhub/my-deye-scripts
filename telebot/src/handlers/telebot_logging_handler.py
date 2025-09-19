import os
import telebot

from typing import Optional, cast
from datetime import datetime
from telebot_users import TelebotUsers
from telebot_base_handler import TelebotBaseHandler
from telebot_utils import get_inline_button_by_data
from deye_utils import ensure_dir_exists

from deye_file_lock import (
  flock,
  LOCK_EX,
  LOCK_UN,
)

telebot.apihelper.ENABLE_MIDDLEWARE = True

class TelebotLoggingHandler(TelebotBaseHandler):
  def __init__(self, bot: telebot.TeleBot):
    self.bot: telebot.TeleBot = bot
    self.known_users_messages_path = 'data/logs/known_users'
    self.unknown_users_messages_path = 'data/logs/unknown_users'
    self.max_file_size = 1024 * 1024 * 1

    ensure_dir_exists(self.known_users_messages_path)
    ensure_dir_exists(self.unknown_users_messages_path)

  def register_handlers(self):
    @self.bot.middleware_handler(update_types = ['message'])
    def handle_message(bot: telebot.TeleBot, message: telebot.types.Message):
      self.log_event(user = message.from_user, event_type = 'message', content = repr(message.text))

    @self.bot.middleware_handler(update_types = ['callback_query'])
    def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery):
      button = get_inline_button_by_data(cast(telebot.types.Message, call.message), call.data) if call.data else None
      button_text = button.text if button is not None else 'Unknown'

      self.log_event(user = call.from_user,
                     event_type = 'button',
                     content = f'text = {repr(button_text)}, data = {repr(call.data)}')

  def log_event(self, user: Optional[telebot.types.User], event_type: str, content: str):
    users = TelebotUsers()

    first_name = user.first_name if user and user.first_name else 'None'
    last_name = user.last_name if user and user.last_name else 'None'

    name = f'{first_name} {last_name}'.strip() if (first_name or last_name) else 'None'

    if users.is_user_allowed(user.id):
      self.log_to_file(self.known_users_messages_path, user.id, name, event_type, content)
    else:
      self.log_to_file(self.unknown_users_messages_path, user.id, name, event_type, content)

    self.trim_file(self.known_users_messages_path, self.max_file_size)
    self.trim_file(self.unknown_users_messages_path, self.max_file_size)

  def log_to_file(self, file_path: str, user_id: int, user_name: str, type: str, message: str):
    file_name = os.path.join(file_path, f'{user_id}.txt')
    with open(file_name, "a+", encoding = "utf-8") as f:
      try:
        # Acquire exclusive lock for writing
        flock(f, LOCK_EX)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f'[{now}] [{user_id}] [{user_name}] [{type}] [{message}]\n')
        f.flush()
      finally:
        flock(f, LOCK_UN)

  def trim_file(self, filename, trim_size):
    if not os.path.exists(filename):
      return

    # wait while file increased up to 20% and then trim
    max_size = int(trim_size * 1.2)
    file_size = os.path.getsize(filename)
    if file_size <= max_size:
      return # trimming not needed

    with open(filename, "rb+") as f:
      try:
        # Acquire exclusive lock for writing
        flock(f, LOCK_EX)

        # Move to position where last `max_size` bytes start
        f.seek(-trim_size, os.SEEK_END)
        data = f.read()

        # Rewrite file with only last `max_size` bytes
        f.seek(0)
        f.write(data)
        f.truncate()
      finally:
        # Always release lock
        flock(f, LOCK_UN)
