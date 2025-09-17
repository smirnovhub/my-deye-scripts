import telebot

from telebot_utils import *
from deye_file_lock import *

from typing import List
from datetime import datetime
from telebot_users import TelebotUsers
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuRequestAccess(TelebotMenuItemHandler):
  def __init__(self, bot):
    self.bot: telebot.TeleBot = bot

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.request_access

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return [
      telebot.types.BotCommand(command = self.command.command, description = self.command.description),
    ]

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      user = message.from_user

      first_name = user.first_name or ''
      last_name = user.last_name or ''
      username = f"@{user.username}" if user.username else None
      phone = message.contact.phone_number if message.contact else None
      name = f'{first_name} {last_name}'.strip() if (first_name or last_name) else 'None'

      info = (f"User ID: {user.id}\n"
              f"Name: {name}\n"
              f"Username: {username}\n"
              f"Phone: {phone}")

      users = TelebotUsers()

      if users.has_user(user.id):
        self.bot.send_message(message.chat.id, 'Command is not allowed for this user')
      else:
        result = self.add_user_to_file('data/access_requests.txt', user.id, name)
        if result:
          self.bot.send_message(message.chat.id, 'Access requested')
          send_private_telegram_message(f'<b>Access requested:</b>\n{info}')
        else:
          self.bot.send_message(message.chat.id, 'Access already requested')

  # Checks if the given user_id exists in the file.
  # If user_id already exists → return False.
  # If not → append the entry and return True.
  # Entry format: YYYY-MM-DD HH:MM:SS USER_ID
  def add_user_to_file(self, file_path: str, user_id: int, user_name: str) -> bool:
    with open(file_path, "a+", encoding = "utf-8") as f:
      f.seek(0)

      # Acquire shared lock for reading
      flock(f, LOCK_SH)
      lines = f.readlines()
      flock(f, LOCK_UN)

      # Check if user_id already exists
      for line in lines:
        if str(user_id) in line:
          return False

      # Acquire exclusive lock for writing
      flock(f, LOCK_EX)
      now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      f.write(f'[{now}] [{user_id}] [{user_name}]\n')
      f.flush()
      flock(f, LOCK_UN)

      return True
