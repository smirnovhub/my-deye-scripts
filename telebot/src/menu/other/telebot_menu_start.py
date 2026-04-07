import telebot
import traceback

from datetime import datetime

from env_utils import EnvUtils
from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock
from deye_exceptions import DeyeKnownException
from telebot_menu_item import TelebotMenuItem
from telegram_send_message import Telegram
from telebot_utils import TelebotUtils
from telebot_menu_item_handler_sync import TelebotMenuItemHandlerSync

class TelebotMenuStart(TelebotMenuItemHandlerSync):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self._data_dir = TelebotUtils.get_data_dir()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.start

  def register_handlers(self) -> None:
    """
    Register message handlers for the bot based on the command list

    The registered handler processes messages and handles exceptions
    including known and unknown errors
    """
    commands = [cmd.command for cmd in self.get_commands()]

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      try:
        if self.users.is_user_blocked(message.from_user.id):
          self.bot.send_message(message.chat.id, 'Command is not allowed for this user')
          return

        self.process_message(message)
      except DeyeKnownException as e:
        self.bot.send_message(message.chat.id, str(e))
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
        self.logger.error(traceback.format_exc())

  def process_message(self, message: telebot.types.Message) -> None:
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
      result = self.add_user_to_file(f'{self._data_dir}/access_requests.txt', user.id, name)
      if result:
        self.bot.send_message(message.chat.id, f'Access requested for user {user.id}')
        if not EnvUtils.is_tests_on():
          Telegram.send_private_telegram_message(f'<b>Access requested:</b>\n{info}')
      else:
        self.bot.send_message(message.chat.id, f'Access already requested for user {user.id}')

  # Checks if the given user_id exists in the file.
  # If user_id already exists → return False.
  # If not → append the entry and return True.
  # Entry format: YYYY-MM-DD HH:MM:SS USER_ID
  def add_user_to_file(self, file_path: str, user_id: int, user_name: str) -> bool:
    if EnvUtils.is_tests_on():
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
