import time
import logging
import telebot

from typing import Any, Callable, List, Optional, Set

from deye_utils import DeyeUtils
from deye_loggers import DeyeLoggers
from telebot_user import TelebotUser
from deye_register import DeyeRegister
from testable_telebot import TestableTelebot
from solarman_server import SolarmanServer
from deye_exceptions import DeyeKnownException
from telebot_fake_test_message import TelebotFakeTestMessage

class TelebotBaseTestModule:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot
    self.log = logging.getLogger()
    self.loggers = DeyeLoggers()
    self.retry_delay_sec = 0.01

  @property
  def description(self) -> str:
    raise NotImplementedError(f'{self.__class__.__name__}: description() is not implemented')

  def run_tests(self, servers: List[SolarmanServer]):
    raise NotImplementedError(f'{self.__class__.__name__}: run_tests() is not implemented')

  def get_all_registered_commands(self) -> List[str]:
    """
    Retrieve all command names registered via @bot.message_handler decorators.

    This method scans the bot's internal message handlers and collects all command
    names declared in their 'filters'. It does not include commands registered
    through the Telegram Bot API (via set_my_commands).

    Returns:
        list[str]: A sorted list of unique command names.
    """
    commands: Set[str] = set()

    for handler in self.bot.message_handlers:
      filters = handler.get("filters", {})
      if isinstance(filters, dict):
        cmds = filters.get("commands")
        if cmds:
          commands.update(cmds)

    return sorted(commands)

  def send_text(self, user: TelebotUser, text: str):
    message = TelebotFakeTestMessage.make(
      text = text,
      user_id = user.id,
      first_name = user.name,
    )
    self.bot.process_new_messages([message])

  def send_button_click(self, user: TelebotUser, data: str):
    message = TelebotFakeTestMessage.make(
      text = data,
      user_id = user.id,
      first_name = user.name,
    )

    query = telebot.types.CallbackQuery(
      id = 321,
      chat_instance = 'fake',
      json_string = '',
      from_user = message.from_user,
      data = data,
      message = message,
    )

    self.bot.process_new_callback_query([query])

  def wait_for_text(self, text: str):
    def check_message():
      if not self.bot.is_messages_contains(text):
        raise DeyeKnownException(f"Waiting for message '{text}'...")

    self.log.info(f"Waiting for message '{text}'...")
    self.call_with_retry(check_message)
    self.log.info(f"Received message '{text}'")
    self.bot.clear_messages()

  def wait_for_text_regex(self, text: str):
    def check_message():
      if not self.bot.is_messages_contains_regex(text):
        raise DeyeKnownException(f"Waiting for message '{text}'...")

    self.log.info(f"Waiting for message '{text}'...")
    self.call_with_retry(check_message)
    self.log.info(f"Received message '{text}'")
    self.bot.clear_messages()

  def wait_for_text_regex_and_get_undo_data(self, text: str) -> str:
    def check_message() -> str:
      undo_data = self.bot.get_undo_data_regex(text)
      if undo_data is None:
        raise DeyeKnownException(f"Waiting for message with undo '{text}'...")
      return str(undo_data)

    self.log.info(f"Waiting for message with undo '{text}'...")
    undo_data = self.call_with_retry(check_message)
    self.log.info(f"Received message with undo '{text}'")
    self.bot.clear_messages()

    return str(undo_data)

  def wait_for_server_changes(self, server: SolarmanServer, register: DeyeRegister):
    def check_server():
      if not server.is_registers_written(register.address, register.quantity):
        raise DeyeKnownException(f"Waiting for register '{register.name}' change on server side...")

    self.log.info(f"Waiting for register '{register.name}' change on server side...")
    self.call_with_retry(check_server)
    self.log.info(f"Register '{register.name}' changed on server side")

  def call_with_retry(self, func: Callable, *args, **kwargs) -> Any:
    """
    Calls a function repeatedly until it succeeds or retries are exhausted.

    :param func: The function to call.
    :param args: Positional arguments to pass to func.
    :param kwargs: Keyword arguments to pass to func.
    :raises Exception: Re-raises the last exception if all retries fail.
    """
    retry_timeout = DeyeUtils.get_test_retry_timeout()
    last_exception: Optional[Exception] = None

    owner = getattr(func, "__self__", None)
    class_name = f'{owner.__class__.__name__}.' if owner else ''
    func_name = func.__name__
    retry_attempt = 1
    total_retry_time = 0.0
    last_print_time = 0.0
    delay = self.retry_delay_sec

    while total_retry_time < retry_timeout:
      try:
        return func(*args, **kwargs)
      except Exception as e:
        last_exception = e
        if total_retry_time - last_print_time > 1:
          last_print_time = total_retry_time
          self.log.info(f"Call to '{class_name}{func_name}' failed: '{e}'. "
                        f"Retrying attempt {retry_attempt}...")
        time.sleep(delay)
        retry_attempt += 1
        total_retry_time += delay
        if delay < 0.5:
          delay *= 2
    else:
      self.log.info(f"Retry timeout of {retry_timeout}s exceeded for {class_name}{func_name}")
      if last_exception is not None:
        raise last_exception

  def error(self, message: str):
    self.log.info(message)
    raise DeyeKnownException(message)
