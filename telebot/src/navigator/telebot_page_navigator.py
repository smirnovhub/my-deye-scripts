import re
import time
import telebot
import threading

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

from telebot_utils import TelebotUtils

if TYPE_CHECKING:
  from telebot_navigation_page import TelebotNavigationPage

class TelebotPageNavigator:
  """
  Manager class that handles navigation between different pages in a Telegram bot.
  Maintains session state, instances, and global callback routing.
  """
  _counter: int = 0
  _lock = threading.Lock()
  _navigator_data_prefix = "_nav_"
  _instances: Dict[str, "TelebotPageNavigator"] = {}
  _handlers_registered: bool = False

  # Data prefix format:
  # _nav_1_35
  # 1 means navigator id
  # 35 means button id
  _prefix_pattern = re.compile(rf"^{_navigator_data_prefix}(\d+)_(\d+)")
  _instance_id_template = f"{_navigator_data_prefix}{{0}}_"

  def __init__(self, bot: telebot.TeleBot):
    """
    Initializes the navigator and registers global handlers if not already done.

    Args:
        bot (telebot.TeleBot): The pyTelegramBotAPI instance.
    """
    self._bot = bot
    self._chat_id: Optional[int] = None
    self._message: Optional[telebot.types.Message] = None
    self._pages: Dict[Enum, "TelebotNavigationPage"] = {}
    self._current_page: Optional["TelebotNavigationPage"] = None
    self._main_page: Optional["TelebotNavigationPage"] = None

    with TelebotPageNavigator._lock:
      TelebotPageNavigator._counter += 1
      self._data_prefix = TelebotPageNavigator._instance_id_template.format(TelebotPageNavigator._counter)
      TelebotPageNavigator._instances[self._data_prefix] = self

      if not TelebotPageNavigator._handlers_registered:
        TelebotPageNavigator._register_handlers(self._bot)
        TelebotPageNavigator._handlers_registered = True

  def register_page(self, page: "TelebotNavigationPage") -> None:
    """
    Adds a page to the navigator's registry.

    Args:
        page (TelebotNavigationPage): The page instance to register.

    Raises:
        RuntimeError: If a page with the same type is already registered.
    """
    if page.page_type in self._pages:
      raise RuntimeError(f"Page {page.page_type.name} already registered")
    self._pages[page.page_type] = page

  def register_pages(self, pages: List["TelebotNavigationPage"]) -> None:
    """
    Registers multiple pages at once from a provided list.

    Args:
        pages (List[TelebotNavigationPage]): A list of page instances to register.
    """
    for page in pages:
      self.register_page(page)

  def start(
    self,
    page: "TelebotNavigationPage",
    text: str,
    chat_id: int,
  ) -> telebot.types.Message:
    """
    Initializes a navigation session and sends the first message.

    Args:
        page (TelebotNavigationPage): The entry point page.
        text (str): Message text to display.
        chat_id (int): Telegram chat ID.

    Returns:
        telebot.types.Message: The sent message object.
    """
    self._main_page = page
    self._current_page = page
    self._chat_id = chat_id
    self._text = text

    try:
      page.clear_button_handlers()
      page.update()
    except Exception as e:
      self._on_error(str(e))
      raise

    keyboard = TelebotUtils.get_keyboard_for_buttons(
      buttons = page.buttons,
      data_prefix = self._data_prefix,
    )

    self._markup = keyboard

    self._message = self._bot.send_message(
      chat_id = self._chat_id,
      text = text,
      reply_markup = keyboard,
      parse_mode = "HTML",
    )

    # Setup cleanup on any user text input
    self._bot.clear_step_handler_by_chat_id(self._chat_id)
    self._bot.register_next_step_handler(
      self._message,
      self._next_step_handler,
      self._message,
    )

    return self._message

  def navigate(
    self,
    page_type: Enum,
    text: str = '',
    **kwargs,
  ) -> None:
    """
    Switches the current page to the one specified by page_type.

    Args:
        page_type (Enum): The type of the target page.
        text (str): Optional new text for the message.
        **kwargs: Data to pass to the target page's prepare method.

    Raises:
        RuntimeError: If navigation hasn't started or the page is not registered.
    """
    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    if page_type not in self._pages:
      raise RuntimeError(f"Page {page_type.name} is not registered")

    page = self._pages[page_type]
    self._current_page = page

    try:
      page.clear_button_handlers()
      page.prepare(**kwargs)
      page.update()
    except Exception as e:
      self._on_error(str(e))
      raise

    self.update(text)

  def update(
    self,
    text: str = '',
  ) -> None:
    """
    Refreshes the current page's content or buttons in the Telegram message.

    Args:
        text (str): Optional new text to edit the message.
    """
    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    if not self._current_page:
      raise RuntimeError("No current page")

    try:
      self._current_page.clear_button_handlers()
      self._current_page.update()
    except Exception as e:
      self._on_error(str(e))
      raise

    keyboard = TelebotUtils.get_keyboard_for_buttons(
      buttons = self._current_page.buttons,
      data_prefix = self._data_prefix,
    )

    self._markup = keyboard

    try:
      if text:
        self._text = text
        self._bot.edit_message_text(
          text,
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = keyboard,
          parse_mode = 'HTML',
        )
      else:
        self._bot.edit_message_reply_markup(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = keyboard,
        )
    except Exception:
      # Ignore "Message is not modified" errors
      pass

  def send_message(self, text: str) -> telebot.types.Message:
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    return self._bot.send_message(
      self._chat_id,
      text,
      parse_mode = "HTML",
    )

  def _resend(self, text: str) -> telebot.types.Message:
    if not self._message or not self._chat_id or not self._text:
      raise RuntimeError("Navigation has not started yet")

    try:
      self._bot.edit_message_text(
        f"{self._text} {text}",
        chat_id = self._chat_id,
        message_id = self._message.message_id,
        parse_mode = 'HTML',
      )
    except Exception:
      pass

    self._message = self._bot.send_message(
      chat_id = self._chat_id,
      text = self._text,
      reply_markup = self._markup,
      parse_mode = "HTML",
    )

    # Setup cleanup on any user text input
    self._bot.clear_step_handler_by_chat_id(self._chat_id)
    self._bot.register_next_step_handler(
      self._message,
      self._next_step_handler,
      self._message,
    )

    return self._message

  def stop(self, text: str = '') -> None:
    """
    Ends the navigation session, removes the keyboard and cleans up instance memory.

    Args:
        text (str): Optional final text for the message.
    """
    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    try:
      if text:
        self._bot.edit_message_text(
          text,
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = None,
          parse_mode = 'HTML',
        )
      else:
        self._bot.edit_message_reply_markup(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = None,
        )
    except Exception:
      pass

    self._bot.clear_step_handler_by_chat_id(self._chat_id)

    self._message = None
    self._chat_id = None
    self._current_page = None
    self._main_page = None

    # Cleanup instance to prevent memory leak
    with TelebotPageNavigator._lock:
      if self._data_prefix in TelebotPageNavigator._instances:
        del TelebotPageNavigator._instances[self._data_prefix]

  def _handle_callback(self, button_id: int):
    """
    Internal handler for processing button clicks routed from global callback.

    Args:
        button_id (int): ID of the button that was pressed.
    """
    if not self._current_page:
      raise RuntimeError("No current page")

    try:
      self._current_page.handle_click(
        navigator = self,
        button_id = button_id,
      )
    except Exception as e:
      self._on_error(str(e))
      raise

  def _on_error(self, message: str) -> None:
    """
    Sends an error message to the chat.

    Args:
        message (str): The error description.
    """
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    self._message = self._bot.send_message(
      self._chat_id,
      message,
      parse_mode = "HTML",
    )

  @staticmethod
  def _register_handlers(bot: telebot.TeleBot):
    """
    Registers the global callback query handler for all navigator instances.

    Args:
        bot (telebot.TeleBot): The bot instance.
    """
    @bot.callback_query_handler(func = lambda call: call.data.startswith(TelebotPageNavigator._navigator_data_prefix))
    def _global_nav_handler(call: telebot.types.CallbackQuery):
      if not call.data:
        return

      bot.answer_callback_query(call.id)

      # Extract navigator ID and button ID from callback data
      match = TelebotPageNavigator._prefix_pattern.match(call.data)
      if not match:
        return

      navigator_id = match.group(1)
      data_prefix = TelebotPageNavigator._instance_id_template.format(navigator_id)

      instance = TelebotPageNavigator._instances.get(data_prefix)
      if instance:
        button_id = int(match.group(2))
        instance._handle_callback(button_id = button_id)

  def _next_step_handler(
    self,
    message: telebot.types.Message,
    sent_message: telebot.types.Message,
  ):
    """
    Auto-stops navigation if the user sends a text message or command.

    Args:
        message (telebot.types.Message): The message received from the user.
    """
    if not self._main_page or not self._current_page:
      raise RuntimeError("Navigation has not started yet")

    # If we received new command, process it
    if TelebotUtils.forward_next(self._bot, message):
      text = self._main_page.get_goodbye_message()
      self.stop(text)
    elif message.text:
      self._bot.register_next_step_handler(
        sent_message,
        self._next_step_handler,
        sent_message,
      )

      try:
        self._resend(message.text)
        time.sleep(1)
        self._current_page.on_user_input(self, message.text)
      except Exception as e:
        sent = self.send_message(str(e))
        if self._chat_id:
          TelebotUtils.remove_message_with_delay(
            bot = self._bot,
            chat_id = self._chat_id,
            message_id = sent.id,
            delay = 5,
          )
