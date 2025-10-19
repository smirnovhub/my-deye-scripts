import telebot

from datetime import datetime

from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_send_message import send_private_telegram_message

class TelebotMenuRequestAccess(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.request_access

  def process_message(self, message: telebot.types.Message):
    user = message.from_user
    first_name = user.first_name if user and user.first_name else 'None'
    last_name = user.last_name if user and user.last_name else 'None'
    user_name = f'@{user.username}' if user and user.username else 'None'
    phone = message.contact.phone_number if message.contact else 'None'
    name = f'{first_name} {last_name}'.strip()

    info = (f"User ID: {user.id}\n"
            f"Name: {name}\n"
            f"User name: {user_name}\n"
            f"Phone: {phone}")

    if self.users.is_user_blocked(user.id) or self.users.is_user_allowed(user.id):
      self.bot.send_message(message.chat.id, 'Command is not allowed for this user')
    else:
      result = self.add_user_to_file('data/access_requests.txt', user.id, name)
      if result:
        self.bot.send_message(message.chat.id, f'Access requested for user {user.id}')
        if not DeyeUtils.is_tests_on():
          send_private_telegram_message(f'<b>Access requested:</b>\n{info}')
      else:
        self.bot.send_message(message.chat.id, f'Access already requested for user {user.id}')

  # Checks if the given user_id exists in the file.
  # If user_id already exists → return False.
  # If not → append the entry and return True.
  # Entry format: YYYY-MM-DD HH:MM:SS USER_ID
  def add_user_to_file(self, file_path: str, user_id: int, user_name: str) -> bool:
    if DeyeUtils.is_tests_on():
      return True

    with open(file_path, "a+", encoding = "utf-8") as f:
      f.seek(0)

      # Acquire shared lock for reading
      DeyeFileLock.flock(f, DeyeFileLock.LOCK_SH)
      lines = f.readlines()
      DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

      # Check if user_id already exists
      for line in lines:
        if str(user_id) in line:
          return False

      # Acquire exclusive lock for writing
      DeyeFileLock.flock(f, DeyeFileLock.LOCK_EX)
      now = datetime.now().strftime(DeyeUtils.time_format_str)
      f.write(f'[{now}] [{user_id}] [{user_name}]\n')
      f.flush()
      DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

      return True
