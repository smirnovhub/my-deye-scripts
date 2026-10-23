import os
import time
import telebot
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import BaseMiddleware

from typing import Optional, cast
from datetime import datetime

from deye_utils import DeyeUtils
from telebot_utils import TelebotUtils
from telebot_users import TelebotUsers
from deye_file_lock import DeyeFileLock
from telebot_base_handler import TelebotBaseHandler

class TelebotLoggingMiddleware(BaseMiddleware):
  """Middleware to log incoming messages and callback queries."""
  def __init__(self, handler: "TelebotLoggingHandler"):
    super().__init__()
    self.update_types = ['message', 'callback_query']
    self._handler = handler

  async def pre_process(self, update, data):
    start_time = time.perf_counter()

    try:
      if isinstance(update, telebot.types.Message):
        self._handler.log_message_event(update)
      elif isinstance(update, telebot.types.CallbackQuery):
        self._handler.log_callback_event(update)
    except Exception as e:
      logging.error("Error while writing log", exc_info = e)

    # Calculate execution time in milliseconds
    elapsed_ms = time.perf_counter() - start_time

    # Output to console or system log
    logging.info(f"Log write took {elapsed_ms:.3f}s")

    return None

  async def post_process(self, update, data, exception = None):
    pass

class TelebotLoggingHandler(TelebotBaseHandler):
  def __init__(self, bot: AsyncTeleBot):
    self.bot = bot
    data_dir = TelebotUtils.get_data_dir()
    self.known_users_messages_path = f'{data_dir}/logs/known_users'
    self.unknown_users_messages_path = f'{data_dir}/logs/unknown_users'
    self.max_file_size = 1024 * 1024 * 1
    self.users = TelebotUsers()

    DeyeUtils.ensure_dir_exists(self.known_users_messages_path)
    DeyeUtils.ensure_dir_exists(self.unknown_users_messages_path)

  def register_handlers(self) -> None:
    # Register logging middleware on AsyncTeleBot instance
    self.bot.setup_middleware(TelebotLoggingMiddleware(self))

  def log_message_event(self, message: telebot.types.Message) -> None:
    self._log_event(
      user = message.from_user,
      event_type = 'send_message',
      content = repr(message.text),
    )

  def log_callback_event(self, call: telebot.types.CallbackQuery) -> None:
    button = TelebotUtils.get_inline_button_by_data(
      cast(
        telebot.types.Message,
        call.message,
      ),
      call.data,
    ) if call.data else None

    button_text = button.text if button is not None else 'Unknown'

    self._log_event(
      user = call.from_user,
      event_type = 'press_button',
      content = f'text = {repr(button_text)}, data = {repr(call.data)}',
    )

  def _log_event(
    self,
    user: Optional[telebot.types.User],
    event_type: str,
    content: str,
  ):
    if user is None:
      return

    first_name = user.first_name if user and user.first_name else 'None'
    last_name = user.last_name if user and user.last_name else 'None'

    name = f'{first_name} {last_name}'.strip() if (first_name or last_name) else 'None'

    if self.users.is_user_allowed(user.id):
      self._log_to_file(
        file_path = self.known_users_messages_path,
        user_id = user.id,
        user_name = name,
        type = event_type,
        message = content,
      )

      self._trim_file(
        file_path = self.known_users_messages_path,
        trim_size = self.max_file_size,
        user_id = user.id,
      )
    else:
      self._log_to_file(
        file_path = self.unknown_users_messages_path,
        user_id = user.id,
        user_name = name,
        type = event_type,
        message = content,
      )

      self._trim_file(
        file_path = self.unknown_users_messages_path,
        trim_size = self.max_file_size,
        user_id = user.id,
      )

  def _log_to_file(
    self,
    file_path: str,
    user_id: int,
    user_name: str,
    type: str,
    message: str,
  ):
    file_name = os.path.join(file_path, f'{user_id}.txt')
    with open(file_name, "a+", encoding = "utf-8") as f:
      try:
        # Acquire exclusive lock for writing
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_EX)

        now = datetime.now()
        milliseconds = int(now.microsecond / 1000)
        now_str = f"{now.strftime(DeyeUtils.time_format_str)}.{milliseconds:03d}"

        f.write(f'[{now_str}] [{user_id}] [{user_name}] [{type}] [{message}]\n')
        f.flush()
      finally:
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

  def _trim_file(
    self,
    file_path: str,
    trim_size: int,
    user_id: int,
  ):
    file_name = os.path.join(file_path, f'{user_id}.txt')
    if not os.path.exists(file_name):
      return

    # Wait while file increases up to 30 percent and then trim
    max_size = int(trim_size * 1.3)
    file_size = os.path.getsize(file_name)

    if file_size <= max_size:
      return # trimming not needed

    logging.warning(f"Trimming log file {file_name} from {file_size} to {max_size}")

    with open(file_name, "rb+") as f:
      try:
        # Acquire exclusive lock for writing
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_EX)

        # Move to position where last max_size bytes start
        f.seek(-trim_size, os.SEEK_END)
        data = f.read()

        # Rewrite file with only last max_size bytes
        f.seek(0)
        f.write(data)
        f.truncate()
      finally:
        # Always release lock
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)
