import logging
import telebot

from typing import List
from abc import abstractmethod

from telebot_user import TelebotUser
from telebot_users import TelebotUsers
from deye_loggers import DeyeLoggers
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
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
    self.bot = bot
    self.users = TelebotUsers()
    self.loggers = DeyeLoggers()
    self.logger = logging.getLogger()
    self.auth_helper = TelebotAuthHelper()

  @property
  @abstractmethod
  def command(self) -> TelebotMenuItem:
    """Return the TelebotMenuItem associated with this handler"""
    pass

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

  def is_authorized(self, message: telebot.types.Message) -> bool:
    """
    Check if the user is authorized to execute this command

    Args:
        user_id (int): Telegram user ID
        chat_id (int): Telegram chat ID to send denial message if needed

    Returns:
        bool: True if authorized, False otherwise
    """
    if self.users.is_user_blocked(message.from_user.id):
      self.bot.send_message(message.chat.id, 'User is not authorized')
      return False

    if not self.users.is_user_allowed(message.from_user.id):
      self.bot.send_message(message.chat.id, f'User {message.from_user.id} is not authorized')
      return False

    if not self._is_item_allowed(message.from_user.id, message.chat.id):
      return False

    return True

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
