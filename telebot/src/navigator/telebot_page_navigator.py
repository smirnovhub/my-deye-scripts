import inspect
import logging
import re
import time
import traceback
import telebot
import threading
import asyncio
import websockets
import json

from enum import Enum
from concurrent.futures import Future
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast, Callable, Awaitable

from telebot_utils import TelebotUtils
from telebot_async_runner import TelebotAsyncRunner

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
  _free_ids: List[int] = []
  _instances: Dict[int, "TelebotPageNavigator"] = {}
  _handlers_registered: bool = False

  # Data prefix format:
  # _nav_1_35
  # 1 means navigator id
  # 35 means button id
  _prefix_pattern = re.compile(rf"^{_navigator_data_prefix}(\d+)_(\d+)")
  _prefix_template = f"{_navigator_data_prefix}{{0}}_"

  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: Optional[TelebotAsyncRunner] = None,
  ):
    """
    Initializes the navigator and registers global handlers if not already done.

    Args:
        bot (telebot.TeleBot): The pyTelegramBotAPI instance.
    """
    self._bot = bot
    self._runner = runner
    self._chat_id: Optional[int] = None
    self._message: Optional[telebot.types.Message] = None
    self._pages: Dict[Enum, "TelebotNavigationPage"] = {}
    self._current_page: Optional["TelebotNavigationPage"] = None
    self._main_page: Optional["TelebotNavigationPage"] = None
    self._logger = logging.getLogger()
    self._delayed_tasks: List[Future] = []
    # Track dedicated websocket listener task for this specific navigator instance
    self._ws_task_future: Optional[Future] = None

    with TelebotPageNavigator._lock:
      if TelebotPageNavigator._free_ids:
        self._id = TelebotPageNavigator._free_ids.pop()
      else:
        TelebotPageNavigator._counter += 1
        self._id = TelebotPageNavigator._counter

      TelebotPageNavigator._instances[self._id] = self

      if not TelebotPageNavigator._handlers_registered:
        TelebotPageNavigator._register_handlers(self._bot)
        TelebotPageNavigator._handlers_registered = True

  @property
  def runner(self) -> TelebotAsyncRunner:
    if not self._runner:
      raise RuntimeError("Async runner is not set")
    return self._runner

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

  @property
  def bot(self) -> telebot.TeleBot:
    return self._bot

  @property
  def chat_id(self) -> Optional[int]:
    return self._chat_id

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
    chat_id: int,
  ) -> telebot.types.Message:
    """
    Initializes a navigation session and sends the first message.

    Args:
        page (TelebotNavigationPage): The entry point page.
        chat_id (int): Telegram chat ID.

    Returns:
        telebot.types.Message: The sent message object.
    """
    self._main_page = page
    self._current_page = page
    self._chat_id = chat_id

    try:
      page.clear_button_handlers()
      page.update()
    except Exception as e:
      self._logger.error(traceback.format_exc())
      self.send_message_with_remove_with_delay(str(e))

    keyboard = TelebotUtils.get_keyboard_for_buttons(
      buttons = page.buttons,
      data_prefix = TelebotPageNavigator._prefix_template.format(self._id),
    )

    self._markup = keyboard

    page_text = self._get_page_text(page)

    if isinstance(page_text, telebot.types.InputRichMessage):
      self._message = self._bot.send_rich_message(
        chat_id = self._chat_id,
        rich_message = page_text,
        reply_markup = keyboard,
      )
    else:
      self._message = self._bot.send_message(
        chat_id = self._chat_id,
        text = page_text,
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
    **kwargs,
  ) -> None:
    """
    Switches the current page to the one specified by page_type.

    Args:
        page_type (Enum): The type of the target page.
        **kwargs: Data to pass to the target page's prepare method.

    Raises:
        RuntimeError: If navigation hasn't started or the page is not registered.
    """
    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    if page_type not in self._pages:
      raise RuntimeError(f"Page {page_type.name} is not registered")

    page = self._pages[page_type]

    try:
      result = page.on_navigate(navigator = self, **kwargs)

      # Handle async prepare method if it returns a coroutine
      if inspect.iscoroutine(result):
        self._logger.info(f"{self.__class__.__name__}: running async prepare for page {page_type.name}")
        future = self.runner.run(result)

        def on_done(future: Future) -> None:
          try:
            future.result()
            self._current_page = page
            self.update()
          except Exception as e:
            self._logger.error(traceback.format_exc())
            self.send_message_with_remove_with_delay(str(e))

        future.add_done_callback(on_done)
      else:
        self._current_page = page
        self.update()

    except Exception as e:
      self._logger.error(traceback.format_exc())
      self.send_message_with_remove_with_delay(str(e))

  def update(self) -> None:
    """
    Refreshes the current page's content or buttons in the Telegram message.
    """
    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    if not self._current_page:
      raise RuntimeError("No current page")

    try:
      self._current_page.clear_button_handlers()
      self._current_page.update()
    except Exception as e:
      self._logger.error(traceback.format_exc())
      self.send_message_with_remove_with_delay(str(e))

    keyboard = TelebotUtils.get_keyboard_for_buttons(
      buttons = self._current_page.buttons,
      data_prefix = TelebotPageNavigator._prefix_template.format(self._id),
    )

    self._markup = keyboard
    page_text = self._get_page_text(self._current_page)

    try:
      if isinstance(page_text, telebot.types.InputRichMessage):
        self._bot.edit_message_text(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          rich_message = page_text,
          reply_markup = keyboard,
        )
      else:
        self._bot.edit_message_text(
          text = page_text,
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = keyboard,
          parse_mode = 'HTML',
        )

    except Exception:
      # Ignore "Message is not modified" errors
      pass

  def add_delayed_update(
    self,
    delay: float,
    action: Optional[Union[Callable[[], Any], Awaitable[Any]]] = None,
  ) -> None:
    """
      Schedules a delayed update or custom async/sync action using the async runner.
      If cancelled or stopped, the task won't execute.

      Args:
          delay (float): Delay in seconds before execution.
          action (Callable or Awaitable): Optional custom action to run. If omitted, calls self.update().
      """
    async def delayed_task_wrapper() -> None:
      try:
        await asyncio.sleep(delay)

        if action is None:
          self.update()
        elif callable(action):
          res = action()
          if inspect.iscoroutine(res):
            await res
        elif inspect.isawaitable(action):
          await action
        else:
          raise TypeError("delayed update action must be callable or awaitable")
      except asyncio.CancelledError:
        raise
      except Exception as e:
        self._logger.error(traceback.format_exc())
        self.send_message_with_remove_with_delay(str(e))

    future = self.runner.run(delayed_task_wrapper())

    with self._lock:
      self._delayed_tasks.append(future)

    def on_done(f: Future) -> None:
      with self._lock:
        if f in self._delayed_tasks:
          self._delayed_tasks.remove(f)

    future.add_done_callback(on_done)

  def send_message(self, text: str) -> telebot.types.Message:
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    return self._bot.send_message(
      self._chat_id,
      text,
      parse_mode = "HTML",
    )

  def send_message_with_remove_with_delay(
    self,
    text: str,
    delay = 5,
  ) -> None:
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    sent = self.send_message(text[:512])

    TelebotUtils.remove_message_with_delay(
      bot = self._bot,
      chat_id = self._chat_id,
      message_id = sent.id,
      delay = delay,
    )

  def start_websocket_listener(self, uri: str) -> None:
    """
    Starts a dedicated background WebSocket listener task tied to this specific navigator instance.
    """
    async def instance_listener_worker():
      while True:
        try:
          async with websockets.connect(uri) as websocket:
            async for raw_message in websocket:
              try:
                data = json.loads(raw_message)
                self._handle_server_update(data)
              except json.JSONDecodeError as e:
                self._logger.error(f"Error parsing websocket update json: {e}")
                pass
              except Exception as ee:
                self._logger.error(f"Error handling websocket update: {ee}")
        except (websockets.ConnectionClosed, asyncio.CancelledError):
          raise
        except Exception as e:
          self._logger.error(f"WebSocket client error: {e}")
          await asyncio.sleep(5)

    future = self.runner.run(instance_listener_worker())
    with self._lock:
      self._ws_task_future = future

    def on_done(f: Future) -> None:
      with self._lock:
        if self._ws_task_future == f:
          self._ws_task_future = None

    future.add_done_callback(on_done)

  def _get_page_text(self, page: "TelebotNavigationPage") -> Union[str, telebot.types.InputRichMessage]:
    try:
      return page.text if page.text else "Untitled"
    except Exception as e:
      self._logger.error(traceback.format_exc())
      return str(e)

  def _resend(self, text: str) -> telebot.types.Message:
    if not self._message or not self._chat_id or not self._current_page:
      raise RuntimeError("Navigation has not started yet")

    page_text = self._get_page_text(self._current_page)

    if isinstance(page_text, telebot.types.InputRichMessage):
      try:
        self._bot.edit_message_text(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          rich_message = page_text,
        )
      except Exception:
        pass

      self._message = self._bot.send_rich_message(
        chat_id = self._chat_id,
        rich_message = page_text,
        reply_markup = self._markup,
      )
    else:
      try:
        self._bot.edit_message_text(
          text = f"{page_text} {text}",
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          parse_mode = 'HTML',
        )
      except Exception:
        pass

      self._message = self._bot.send_message(
        chat_id = self._chat_id,
        text = page_text,
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

  def stop(self, text: Optional[Union[str, telebot.types.InputRichMessage]] = None) -> None:
    """
    Ends the navigation session, cancels pending delayed tasks, removes the keyboard and cleans up instance memory.

    Args:
        text (str): Optional final text for the message.
    """
    # Safely extract and clear pending delayed tasks under lock
    with self._lock:
      tasks_to_cancel = list(self._delayed_tasks)
      self._delayed_tasks.clear()
      ws_future = self._ws_task_future
      self._ws_task_future = None

    # Cancel tasks outside the lock to prevent potential deadlocks
    for future in tasks_to_cancel:
      if not future.done():
        future.cancel()

    if ws_future and not ws_future.done():
      ws_future.cancel()

    if not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    try:
      if isinstance(text, str) and text:
        self._bot.edit_message_text(
          text,
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = None,
          parse_mode = 'HTML',
        )
      elif isinstance(text, telebot.types.InputRichMessage):
        self._bot.edit_message_text(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          rich_message = text,
          reply_markup = None,
        )
      else:
        self._bot.edit_message_reply_markup(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          reply_markup = None,
        )
    except Exception:
      pass

    # Cleanup instance to prevent memory leak
    with TelebotPageNavigator._lock:
      if self._id in TelebotPageNavigator._instances:
        # Remove from active instances
        del TelebotPageNavigator._instances[self._id]
        # Return ID to the pool
        TelebotPageNavigator._free_ids.append(self._id)
        # Ensure the ID is not used twice by this instance

      # Clear handlers if there are no navigators for this chat id
      exists = any(nav.chat_id == self._chat_id for nav in self._instances.values())
      if not exists:
        self._bot.clear_step_handler_by_chat_id(self._chat_id)

    self._id = -1
    self._message = None
    # Do not reset chat it to be able to send error messages
    #self._chat_id = None
    self._current_page = None
    self._main_page = None
    self._pages.clear()

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
      self._logger.error(traceback.format_exc())
      self.send_message_with_remove_with_delay(str(e))

  def _on_command_button_clicked(self, command: str) -> None:
    if not self._current_page:
      raise RuntimeError("Navigation has not started yet")

    text = self._current_page.get_stop_by_command_message(command)
    self.stop(text)

  def _handle_server_update(self, data: Dict[str, Any]) -> None:
    """
    Dispatches incoming server update to the currently active page.
    """
    if not self._current_page:
      return

    # Check if the current page implements a server update handler
    try:
      self._logger.info(f"Websocket update received: {data}")
      result = self._current_page.on_server_update(navigator = self, data = data)

      # Support both synchronous and asynchronous page handlers
      if inspect.iscoroutine(result):
        self._logger.info(
          f"{self.__class__.__name__}: running async on_server_update for page {self._current_page.page_type.name}")
        future = self.runner.run(result)

        def on_done(f: Future) -> None:
          try:
            f.result()
          except Exception as e:
            self.send_message_with_remove_with_delay(str(e))
            self._logger.error(traceback.format_exc())

        future.add_done_callback(on_done)
    except Exception as e:
      self.send_message_with_remove_with_delay(str(e))
      self._logger.error(traceback.format_exc())

  @staticmethod
  def _register_handlers(bot: telebot.TeleBot):
    """
    Registers the global callback query handler for all navigator instances.

    Args:
        bot (telebot.TeleBot): The bot instance.
    """
    @bot.middleware_handler(update_types = ['callback_query'])
    def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery):
      if not call.data:
        return

      button = TelebotUtils.get_inline_button_by_data(cast(telebot.types.Message, call.message), call.data)
      if not button or not button.callback_data or not button.callback_data.startswith("/"):
        return

      with TelebotPageNavigator._lock:
        navigators = [inst for inst in TelebotPageNavigator._instances.values() if inst.chat_id == call.message.chat.id]

      for nav in navigators:
        nav._on_command_button_clicked(button.callback_data)

    @bot.callback_query_handler(func = lambda call: call.data.startswith(TelebotPageNavigator._navigator_data_prefix))
    def _global_nav_handler(call: telebot.types.CallbackQuery):
      if not call.data:
        return

      bot.answer_callback_query(call.id)

      # Extract navigator ID and button ID from callback data
      match = TelebotPageNavigator._prefix_pattern.match(call.data)
      if not match:
        return

      navigator_id = int(match.group(1))

      with TelebotPageNavigator._lock:
        instance = TelebotPageNavigator._instances.get(navigator_id)

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
    else:
      self._bot.register_next_step_handler(
        sent_message,
        self._next_step_handler,
        sent_message,
      )

      if message.text and self._current_page.need_user_input:
        try:
          if self._current_page.resend_message_on_user_input:
            self._resend(message.text)
            time.sleep(0.5)

          result = self._current_page.on_user_input(self, message.text)

          # Check if the handler returned a coroutine and run it asynchronously
          if inspect.iscoroutine(result):
            self._logger.info(f"{self.__class__.__name__}: running async handler for user input")
            future = self.runner.run(result)

            def on_done(future: Future) -> None:
              try:
                future.result()
              except Exception as e:
                self.send_message_with_remove_with_delay(str(e))
                self._logger.error(traceback.format_exc())

            future.add_done_callback(on_done)

        except Exception as e:
          self._logger.error(traceback.format_exc())
          self.send_message_with_remove_with_delay(str(e))
