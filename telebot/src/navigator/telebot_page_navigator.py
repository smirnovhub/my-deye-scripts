import re
import logging
import traceback
import telebot
import threading
import asyncio
import websockets
import json

from datetime import timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast, Callable, Awaitable

from telebot_utils import TelebotUtils
from async_rlock import AsyncRLock

if TYPE_CHECKING:
  from telebot_navigation_page import TelebotNavigationPage

class TelebotPageNavigator:
  """
  Manager class that handles navigation between different pages in a Telegram bot.
  Maintains session state, instances, and global callback routing with native async support.
  """
  _counter: int = 0
  _lock_threading = threading.Lock()
  _navigator_data_prefix = "_nav_"
  _free_ids: List[int] = []
  _instances: Dict[int, "TelebotPageNavigator"] = {}
  _handlers_registered: bool = False

  _prefix_pattern = re.compile(rf"^{_navigator_data_prefix}(\d+)_(.+)")
  _prefix_template = f"{_navigator_data_prefix}{{0}}_"

  def __init__(
    self,
    bot: telebot.TeleBot,
    auto_update_period: Optional[timedelta] = None,
  ):
    """
    Initializes the navigator and registers global handlers if not already done.
    """
    self._bot = bot
    self._auto_update_period = auto_update_period
    self._chat_id: Optional[int] = None
    self._message: Optional[telebot.types.Message] = None
    self._pages: Dict[Enum, "TelebotNavigationPage"] = {}
    self._current_page: Optional["TelebotNavigationPage"] = None
    self._main_page: Optional["TelebotNavigationPage"] = None
    self._logger = logging.getLogger()
    self._delayed_tasks: List[asyncio.Task] = []
    self._ws_task: Optional[asyncio.Task] = None
    self._auto_update_task: Optional[asyncio.Task] = None

    try:
      self._loop = asyncio.get_running_loop()
    except RuntimeError:
      self._loop = asyncio.get_event_loop()

    self._lock = AsyncRLock()

    with TelebotPageNavigator._lock_threading:
      if TelebotPageNavigator._free_ids:
        self._id = TelebotPageNavigator._free_ids.pop()
      else:
        TelebotPageNavigator._counter += 1
        self._id = TelebotPageNavigator._counter

      TelebotPageNavigator._instances[self._id] = self

      if not TelebotPageNavigator._handlers_registered:
        TelebotPageNavigator._register_handlers(self._bot)
        TelebotPageNavigator._handlers_registered = True

  def register_page(self, page: "TelebotNavigationPage") -> None:
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
    for page in pages:
      self.register_page(page)

  async def start(
    self,
    page: "TelebotNavigationPage",
    chat_id: int,
  ) -> telebot.types.Message:
    self._main_page = page
    self._current_page = page
    self._chat_id = chat_id

    async with self._lock:
      try:
        await page.update()
        page.clear_buttons()
        page.create_buttons()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        return self.send_message(str(e))

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

      self._bot.clear_step_handler_by_chat_id(self._chat_id)
      self._bot.register_next_step_handler(
        self._message,
        self._next_step_handler,
        self._message,
      )

      if self._auto_update_period is not None:
        self._start_auto_update_loop()

    return self._message

  async def navigate(
    self,
    page_type: Enum,
    **kwargs,
  ) -> None:
    async with self._lock:
      if not self._message or not self._chat_id:
        raise RuntimeError("Navigation has not started yet")

      if page_type not in self._pages:
        raise RuntimeError(f"Page {page_type.name} is not registered")

      page = self._pages[page_type]
      self._current_page = page

      try:
        await page.on_navigate(navigator = self, **kwargs)
      except Exception as e:
        self._logger.error(traceback.format_exc())
        self.send_message_with_remove_with_delay(str(e))

      try:
        await self.update()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        self.send_message_with_remove_with_delay(str(e))

  async def update(self) -> None:
    async with self._lock:
      if not self._message or not self._chat_id:
        raise RuntimeError("Navigation has not started yet")

      if not self._current_page:
        raise RuntimeError("No current page")

      try:
        await self._current_page.update()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        self.send_message_with_remove_with_delay(str(e))

      self._current_page.clear_buttons()

      try:
        self._current_page.create_buttons()
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
        pass

  async def add_delayed_update(
    self,
    delay: float,
    action: Optional[Callable[[], Awaitable[Any]]],
  ) -> None:
    """
    Schedules a delayed update or custom async action using the event loop.
    """
    async def delayed_task_wrapper() -> None:
      try:
        await asyncio.sleep(delay)
        await action()
      except asyncio.CancelledError:
        raise
      except Exception as e:
        self._logger.error(traceback.format_exc())
        self.send_message_with_remove_with_delay(str(e))

    task = self._loop.create_task(delayed_task_wrapper())

    with self._lock_threading:
      self._delayed_tasks.append(task)

    def on_done(t: asyncio.Task) -> None:
      with self._lock_threading:
        if t in self._delayed_tasks:
          self._delayed_tasks.remove(t)

    task.add_done_callback(on_done)

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
    async def instance_listener_worker():
      while True:
        try:
          async with websockets.connect(uri) as websocket:
            async for raw_message in websocket:
              try:
                data = json.loads(raw_message)
                await self._handle_server_update(data)
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

    task = self._loop.create_task(instance_listener_worker())
    with self._lock_threading:
      self._ws_task = task

    def on_done(t: asyncio.Task) -> None:
      with self._lock_threading:
        if self._ws_task == t:
          self._ws_task = None

    task.add_done_callback(on_done)

  def _start_auto_update_loop(self) -> None:
    async def auto_update_worker() -> None:
      if self._auto_update_period is None:
        return

      period_seconds = self._auto_update_period.total_seconds()

      while True:
        try:
          await asyncio.sleep(period_seconds)

          if not self._current_page:
            continue

          async with self._lock:
            self._logger.info(f"{self.__class__.__name__}: running async on_auto_update for "
                              f"page {self._current_page.page_type.name}")
            await self._current_page.on_auto_update(navigator = self)
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._logger.error(traceback.format_exc())
          self.send_message_with_remove_with_delay(str(e))

    task = self._loop.create_task(auto_update_worker())
    with self._lock_threading:
      self._auto_update_task = task

    def task_done(t: asyncio.Task) -> None:
      with self._lock_threading:
        if self._auto_update_task == t:
          self._auto_update_task = None

    task.add_done_callback(task_done)

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

    self._bot.clear_step_handler_by_chat_id(self._chat_id)
    self._bot.register_next_step_handler(
      self._message,
      self._next_step_handler,
      self._message,
    )

    return self._message

  def stop(self, text: Optional[Union[str, telebot.types.InputRichMessage]] = None) -> None:
    with self._lock_threading:
      tasks_to_cancel = list(self._delayed_tasks)
      self._delayed_tasks.clear()
      ws_task = self._ws_task
      self._ws_task = None
      auto_update_task = self._auto_update_task
      self._auto_update_task = None

    for task in tasks_to_cancel:
      if not task.done():
        task.cancel()

    if ws_task and not ws_task.done():
      ws_task.cancel()

    if auto_update_task and not auto_update_task.done():
      auto_update_task.cancel()

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

    with TelebotPageNavigator._lock_threading:
      if self._id in TelebotPageNavigator._instances:
        del TelebotPageNavigator._instances[self._id]
        TelebotPageNavigator._free_ids.append(self._id)

      exists = any(nav.chat_id == self._chat_id for nav in self._instances.values())
      if not exists:
        self._bot.clear_step_handler_by_chat_id(self._chat_id)

    self._id = -1
    self._message = None
    self._current_page = None
    self._main_page = None
    self._pages.clear()

  async def _handle_callback(self, button_id: str) -> None:
    async with self._lock:
      if not self._current_page:
        raise RuntimeError("No current page")

      try:
        await self._current_page.handle_click(
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

  async def _handle_server_update(self, data: Dict[str, Any]) -> None:
    async with self._lock:
      if not self._current_page:
        return

      try:
        self._logger.info(f"Websocket update received: {data}")
        await self._current_page.on_websocket_update(navigator = self, data = data)
      except Exception as e:
        self.send_message_with_remove_with_delay(str(e))
        self._logger.error(traceback.format_exc())

  @staticmethod
  def _register_handlers(bot: telebot.TeleBot):
    @bot.middleware_handler(update_types = ['callback_query'])
    def handle_callback(bot: telebot.TeleBot, call: telebot.types.CallbackQuery):
      if not call.data:
        return

      button = TelebotUtils.get_inline_button_by_data(cast(telebot.types.Message, call.message), call.data)
      if not button or not button.callback_data or not button.callback_data.startswith("/"):
        return

      with TelebotPageNavigator._lock_threading:
        navigators = [inst for inst in TelebotPageNavigator._instances.values() if inst.chat_id == call.message.chat.id]

      for nav in navigators:
        nav._on_command_button_clicked(button.callback_data)

    @bot.callback_query_handler(func = lambda call: call.data.startswith(TelebotPageNavigator._navigator_data_prefix))
    def _global_nav_handler(call: telebot.types.CallbackQuery):
      if not call.data:
        return

      bot.answer_callback_query(call.id)

      match = TelebotPageNavigator._prefix_pattern.match(call.data)
      if not match:
        return

      navigator_id = int(match.group(1))

      with TelebotPageNavigator._lock_threading:
        instance = TelebotPageNavigator._instances.get(navigator_id)

      if instance:
        button_id = match.group(2)
        asyncio.run_coroutine_threadsafe(
          instance._handle_callback(button_id = button_id),
          instance._loop,
        )

  def _next_step_handler(
    self,
    message: telebot.types.Message,
    sent_message: telebot.types.Message,
  ):
    if not self._main_page or not self._current_page:
      raise RuntimeError("Navigation has not started yet")

    async def step_worker():
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
            async with self._lock:
              if self._current_page.resend_message_on_user_input:
                self._resend(message.text)
                await asyncio.sleep(0.5)

                self._logger.info(f"{self.__class__.__name__}: running async handler for user input")
                await self._current_page.on_user_input(self, message.text)

          except Exception as e:
            self._logger.error(traceback.format_exc())
            self.send_message_with_remove_with_delay(str(e))

    asyncio.run_coroutine_threadsafe(step_worker(), self._loop)
