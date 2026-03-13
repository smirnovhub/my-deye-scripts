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

  # Regexp to extract prefix like _n_123_ from string _n_123_action
  _prefix_pattern = re.compile(rf"^({_navigator_data_prefix}\d+_).+")

  def __init__(self, bot: telebot.TeleBot):
    self._bot = bot
    self._chat_id: Optional[int] = None
    self._message: Optional[telebot.types.Message] = None
    self._pages: Dict[Enum, "TelebotNavigationPage"] = {}
    self._current_page: Optional["TelebotNavigationPage"] = None

    with TelebotPageNavigator._lock:
      TelebotPageNavigator._counter += 1
      self._data_prefix = f"{TelebotPageNavigator._navigator_data_prefix}{TelebotPageNavigator._counter}_"
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
  ) -> None:
    self._chat_id = chat_id

    page.update()

    user_choices = [TelebotUserChoice(
      text = node.text,
      data = node.data,
    ) for node in page.buttons]

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

    self._current_page = page

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

    page.prepare(**kwargs)
    page.update()
    self.update(text)

  def update(
    self,
    text: str = '',
  ) -> None:
    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    if not self._current_page:
      raise RuntimeError("No current page")

    user_choices = [TelebotUserChoice(
      text = node.text,
      data = node.data,
    ) for node in self._current_page.buttons]

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

  def _handle_callback(self, call: telebot.types.CallbackQuery):
    # Logic for handling navigation
    # Use self._data_prefix to filter or parse data
    if not self._current_page:
      raise RuntimeError("No current page")

    data = call.data.replace(self._data_prefix, "")
    self._current_page.handle_click(self, data)

  def stop(self) -> None:
    self._message = None
    self._chat_id = None
    self._current_page = None

    with TelebotPageNavigator._lock:
      if self._data_prefix in TelebotPageNavigator._instances:
        del TelebotPageNavigator._instances[self._data_prefix]

  @staticmethod
  def _register_handlers(bot: telebot.TeleBot):
    @bot.callback_query_handler(func = lambda call: call.data.startswith(TelebotPageNavigator._navigator_data_prefix))
    def _global_nav_handler(call: telebot.types.CallbackQuery):
      if not call.data:
        return

      # Fast lookup using regex match
      match = TelebotPageNavigator._prefix_pattern.match(call.data)
      if match:
        prefix = match.group(1)
        instance = TelebotPageNavigator._instances.get(prefix)
        if instance:
          bot.answer_callback_query(call.id)
          instance._handle_callback(call)
