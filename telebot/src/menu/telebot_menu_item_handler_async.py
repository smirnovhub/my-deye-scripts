import telebot
import traceback

from typing import Any, Coroutine
from concurrent.futures import Future

from deye_exceptions import DeyeKnownException
from telebot_async_runner import TelebotAsyncRunner
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker_async import TelebotLocalUpdateCheckerAsync
from telebot_remote_update_checker_async import TelebotRemoteUpdateCheckerAsync

class TelebotMenuItemHandlerAsync(TelebotMenuItemHandler):
  """
  Base class for handling Telebot menu item commands and user authorization
  """
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    """
    Initialize the TelebotMenuItemHandler with a bot instance

    Args:
        bot (telebot.TeleBot): The Telegram bot instance
    """
    super().__init__(bot = bot)

    self._runner = runner
    self._local_update_checker = TelebotLocalUpdateCheckerAsync()
    self._remote_update_checker = TelebotRemoteUpdateCheckerAsync()

  def register_handlers(self) -> None:
    """
    Register message handlers for the bot based on the command list

    The registered handler processes messages and handles exceptions
    including known and unknown errors
    """
    commands = [cmd.command for cmd in self.get_commands()]

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      # Wrap sync handler → async execution
      self._runner.run(self._handle_async(message))

  async def _handle_async(self, message: telebot.types.Message) -> None:
    """
    Async processing pipeline
    """
    try:
      if not self.is_authorized(message):
        return

      if await self.has_updates(message):
        return

      await self.process_message(message)
    except DeyeKnownException as e:
      self.bot.send_message(message.chat.id, str(e))
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      self.logger.error(traceback.format_exc())

  async def process_message(self, message: telebot.types.Message) -> None:
    """
    Process the incoming message for this command

    Must be implemented by subclasses

    Args:
        message (telebot.types.Message): The incoming message

    Raises:
        NotImplementedError: Always, if not implemented in subclass
    """
    raise NotImplementedError(
      f'{self.__class__.__name__}: process_message() for command {self.command.command} is not implemented')

  async def has_updates(self, message: telebot.types.Message) -> bool:
    try:
      if not await self._remote_update_checker.is_on_branch():
        self.bot.send_message(message.chat.id, 'Update check skipped: the repository is not currently on a branch')
        return False

      if await self._remote_update_checker.check_for_remote_updates(self.bot, message):
        return True

      if await self._local_update_checker.check_for_local_updates(
          self.bot,
          message.chat.id,
          force = False,
          message = message,
      ):
        return True
    except Exception as e:
      self.bot.send_message(message.chat.id, f'Error while checking for updates: {str(e)}')
      self.logger.info(f'Error while checking for updates: {str(e)}')

    return False

  def run_async(self, coro: Coroutine[Any, Any, Any]) -> Future[Any]:
    return self._runner.run(coro)
