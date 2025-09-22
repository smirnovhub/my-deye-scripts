import telebot
import traceback

from typing import List
from telebot_user import TelebotUser
from telebot_users import TelebotUsers
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
from deye_exceptions import DeyeKnownException
from telebot_base_handler import TelebotBaseHandler

class TelebotMenuItemHandler(TelebotBaseHandler):
  """
  Base class for handling Telebot menu item commands and user authorization
  """
  def __init__(self, bot: telebot.TeleBot):
    """
    Initialize the TelebotMenuItemHandler with a bot instance

    Args:
        bot (telebot.TeleBot): The Telegram bot instance
    """
    self.bot: telebot.TeleBot = bot
    self.users = TelebotUsers()
    self.auth_helper = TelebotAuthHelper()

  @property
  def command(self) -> TelebotMenuItem:
    """Return the TelebotMenuItem associated with this handler"""
    return TelebotMenuItem.unknown

  def get_commands(self) -> List[telebot.types.BotCommand]:
    """
    Return the list of BotCommand objects for this handler

    Returns:
        List[telebot.types.BotCommand]: List of BotCommand objects for this handler
    """
    return [
      telebot.types.BotCommand(command = self.command.command, description = self.command.description),
    ]

  def is_item_allowed_for_user(self, user: TelebotUser) -> bool:
    """
    Check if the command is allowed for the given user

    Args:
        user (TelebotUser): The user to check

    Returns:
        bool: True if allowed, False otherwise
    """
    return self.auth_helper.is_menu_item_allowed_for_user(user, self.command)

  def register_handlers(self):
    """
    Register message handlers for the bot based on the command list

    The registered handler processes messages and handles exceptions
    including known and unknown errors
    """
    commands = [cmd.command for cmd in self.get_commands()]

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      try:
        self.process_message(message)
      except DeyeKnownException as e:
        self.bot.send_message(message.chat.id, str(e))
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
        print(traceback.format_exc())

  def process_message(self, message: telebot.types.Message):
    """
    Process the incoming message for this command

    Must be implemented by subclasses

    Args:
        message (telebot.types.Message): The incoming message

    Raises:
        NotImplementedError: Always, if not implemented in subclass
    """
    raise NotImplementedError(
      f'{self.__class__.__name__}: process_message() for command {self.command.command} is not implemented yet')

  def is_authorized(self, user_id: int, chat_id: int) -> bool:
    """
    Check if the user is authorized to execute this command

    Args:
        user_id (int): Telegram user ID
        chat_id (int): Telegram chat ID to send denial message if needed

    Returns:
        bool: True if authorized, False otherwise
    """
    if self.users.is_user_blocked(user_id):
      return False

    if not self.users.is_user_allowed(user_id):
      self.bot.send_message(chat_id, f'User {user_id} is not authorized')
      return False

    return self._is_item_allowed(user_id, chat_id)

  def _is_item_allowed(self, user_id: int, chat_id: int) -> bool:
    """
    Check if the command is allowed for the user

    Args:
        user_id (int): Telegram user ID
        chat_id (int): Telegram chat ID to send denial message if needed

    Returns:
        bool: True if command is allowed, False otherwise
    """
    if self.users.is_user_blocked(user_id):
      return False

    if not self.auth_helper.is_menu_item_allowed(user_id, self.command):
      self.bot.send_message(chat_id, f'Command is not allowed for user {user_id}')
      return False
    return True
