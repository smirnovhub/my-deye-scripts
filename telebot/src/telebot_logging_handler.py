import os

from datetime import datetime
from telebot_users import TelebotUsers

from deye_file_lock import (
  flock,
  LOCK_EX,
  LOCK_UN,
)

from telebot import apihelper

apihelper.ENABLE_MIDDLEWARE = True

class TelebotLoggingHandler:
  def __init__(self, bot):
    self.bot = bot
    self.known_users_messages_filename = 'data/known_users_messages.txt'
    self.unknown_users_messages_filename = 'data/unknown_users_messages.txt'
    self.max_file_size = 1024 * 1024 * 1

  def register_handlers(self):
    @self.bot.middleware_handler(update_types = ['message'])
    def handle(bot, message):
      users = TelebotUsers()

      user = message.from_user
      first_name = user.first_name or ''
      last_name = user.last_name or ''
      name = f'{first_name} {last_name}'.strip() if (first_name or last_name) else 'None'

      if users.has_user(user.id):
        self.log_to_file(self.known_users_messages_filename, user.id, name, repr(message.text))
      else:
        self.log_to_file(self.unknown_users_messages_filename, user.id, name, repr(message.text))

      self.trim_file(self.known_users_messages_filename, self.max_file_size)
      self.trim_file(self.unknown_users_messages_filename, self.max_file_size)

  def log_to_file(self, file_path: str, user_id: int, user_name: str, message: str):
    with open(file_path, "a+", encoding = "utf-8") as f:
      try:
        # Acquire exclusive lock for writing
        flock(f, LOCK_EX)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f'[{now}] [{user_id}] [{user_name}] [{message}]\n')
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
