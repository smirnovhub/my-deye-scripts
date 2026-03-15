import re
import telebot
import threading

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional

from telebot_user_choice import TelebotUserChoice
from telebot_utils import TelebotUtils

if TYPE_CHECKING:
  from telebot_navigation_page import TelebotNavigationPage

class TelebotPageNavigator:
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
  _instance_id_template = f"{_navigator_data_prefix}{0}_"

  def __init__(self, bot: telebot.TeleBot):
    self._bot = bot
    self._chat_id: Optional[int] = None
    self._message: Optional[telebot.types.Message] = None
    self._pages: Dict[Enum, "TelebotNavigationPage"] = {}
    self._current_page: Optional["TelebotNavigationPage"] = None

    with TelebotPageNavigator._lock:
      TelebotPageNavigator._counter += 1
      self._data_prefix = TelebotPageNavigator._instance_id_template.format(TelebotPageNavigator._counter)
      TelebotPageNavigator._instances[self._data_prefix] = self

      if not TelebotPageNavigator._handlers_registered:
        TelebotPageNavigator._register_handlers(self._bot)
        TelebotPageNavigator._handlers_registered = True

  def register_page(self, page: "TelebotNavigationPage") -> None:
    if page.page_type in self._pages:
      raise RuntimeError(f"Page {page.page_type.name} already registered")
    self._pages[page.page_type] = page

  def start(
    self,
    chat_id: int,
    text: str,
    page: "TelebotNavigationPage",
  ) -> telebot.types.Message:
    self._chat_id = chat_id
    self._current_page = page

    try:
      page.clear_button_handlers()
      page.update()
    except Exception as e:
      self._on_error(str(e))
      raise

    user_choices = [TelebotUserChoice(
      text = button.text,
      data = str(button.id),
    ) for button in page.buttons]

    keyboard = TelebotUtils.get_keyboard_for_choices_ext(
      options = user_choices,
      data_prefix = self._data_prefix,
    )

    self._message = self._bot.send_message(
      self._chat_id,
      text,
      reply_markup = keyboard,
      parse_mode = "HTML",
    )

    return self._message

  def navigate(
    self,
    page_type: Enum,
    text: str = '',
    **kwargs,
  ) -> None:
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

    user_choices = [
      TelebotUserChoice(
        text = button.text,
        data = str(button.id),
      ) for button in self._current_page.buttons
    ]

    keyboard = TelebotUtils.get_keyboard_for_choices_ext(
      options = user_choices,
      data_prefix = self._data_prefix,
    )

    try:
      if text:
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
      pass

  def _handle_callback(self, button_id: int):
    # Logic for handling navigation
    # Use self._data_prefix to filter or parse data
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

  def stop(self, text: str = '') -> None:
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

    with TelebotPageNavigator._lock:
      if self._data_prefix in TelebotPageNavigator._instances:
        del TelebotPageNavigator._instances[self._data_prefix]

  def _on_error(self, message: str) -> None:
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    self._message = self._bot.send_message(
      self._chat_id,
      message,
      parse_mode = "HTML",
    )

  @staticmethod
  def _register_handlers(bot: telebot.TeleBot):
    @bot.callback_query_handler(func = lambda call: call.data.startswith(TelebotPageNavigator._navigator_data_prefix))
    def _global_nav_handler(call: telebot.types.CallbackQuery):
      if not call.data:
        return

      bot.answer_callback_query(call.id)

      # Fast lookup using regex match
      match = TelebotPageNavigator._prefix_pattern.match(call.data)
      if not match:
        return

      navigator_id = match.group(1)
      data_prefix = TelebotPageNavigator._instance_id_template.format(navigator_id)

      instance = TelebotPageNavigator._instances.get(data_prefix)
      if instance:
        button_id = int(match.group(2))
        instance._handle_callback(button_id = button_id)
