import logging
import traceback
import telebot
import asyncio
import websockets
import json

from telebot.async_telebot import AsyncTeleBot

from datetime import timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union, cast, Callable, Awaitable

from telebot.asyncio_handler_backends import BaseMiddleware
from telebot_async_step_manager import TelebotAsyncStepManager
from telebot_utils import TelebotUtils
from async_rlock import AsyncRLock

if TYPE_CHECKING:
  from telebot_navigation_page import TelebotNavigationPage

class CallbackCommandMiddleware(BaseMiddleware):
  """Middleware to intercept command-like callback queries and route them to the active navigator instance."""
  def __init__(self, navigator_cls: Type["TelebotPageNavigator"]) -> None:
    super().__init__()
    self.update_types = ['callback_query']
    self._navigator_cls = navigator_cls

  async def pre_process(
    self,
    call: telebot.types.CallbackQuery,
    data: Dict[str, Any],
  ) -> None:
    if not call.data or not call.message:
      return

    button = TelebotUtils.get_inline_button_by_data(cast(telebot.types.Message, call.message), call.data)
    if not button or not button.callback_data or not button.callback_data.startswith("/"):
      return

    chat_id = call.message.chat.id
    instance = self._navigator_cls._instances.get(chat_id)

    if instance:
      await instance._on_command_button_clicked(button.callback_data)

  async def post_process(
    self,
    call: telebot.types.CallbackQuery,
    data: Dict[str, Any],
    exception: Optional[Exception] = None,
  ) -> None:
    pass

class TelebotPageNavigator:
  """
  Manager class that handles navigation between different pages in a Telegram bot.
  Maintains session state, instances mapped by chat_id, and global callback routing with native async support.
  """
  _navigator_data_prefix = "_nav_"
  _instances: Dict[int, "TelebotPageNavigator"] = {}
  _handlers_registered: bool = False

  def __init__(
    self,
    bot: AsyncTeleBot,
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
    self._markup: Optional[telebot.types.InlineKeyboardMarkup] = None
    self._logger = logging.getLogger()
    self._tasks: List[asyncio.Task] = []
    self._async_lock = AsyncRLock()

    if not TelebotPageNavigator._handlers_registered:
      TelebotPageNavigator._register_handlers(self._bot)
      TelebotPageNavigator._handlers_registered = True

  def register_page(self, page: "TelebotNavigationPage") -> None:
    if page.page_type in self._pages:
      raise RuntimeError(f"Page {page.page_type.name} already registered")
    self._pages[page.page_type] = page

  @property
  def bot(self) -> AsyncTeleBot:
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
    # Retrieve and stop the previous navigator for this chat before registering the new one
    old_nav = TelebotPageNavigator._instances.get(chat_id)

    if old_nav and old_nav != self:
      try:
        await old_nav.stop()
      except Exception as e:
        self._logger.error(f"Error stopping previous navigator for chat {chat_id}: {e}")

    TelebotPageNavigator._instances[chat_id] = self

    self._main_page = page
    self._current_page = page
    self._chat_id = chat_id

    async with self._async_lock:
      try:
        await page.update()
        page.clear_buttons()
        page.create_buttons()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        return await self.send_message(str(e))

      keyboard = TelebotUtils.get_keyboard_for_buttons(
        buttons = page.buttons,
        data_prefix = TelebotPageNavigator._navigator_data_prefix,
      )

      self._markup = keyboard
      page_text = self._get_page_text(page)

      if isinstance(page_text, telebot.types.InputRichMessage):
        self._message = await self._bot.send_rich_message(
          chat_id = self._chat_id,
          rich_message = page_text,
          reply_markup = keyboard,
        )
      else:
        self._message = await self._bot.send_message(
          chat_id = self._chat_id,
          text = page_text,
          reply_markup = keyboard,
          parse_mode = "HTML",
        )

      TelebotAsyncStepManager.clear_step_handler_by_chat_id(self._chat_id)
      TelebotAsyncStepManager.register_next_step_handler(
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
    async with self._async_lock:
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
        await self.send_message_with_remove_with_delay(str(e))

      try:
        await self.update()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        await self.send_message_with_remove_with_delay(str(e))

  async def update(self) -> None:
    async with self._async_lock:
      if not self._message or not self._chat_id:
        raise RuntimeError("Navigation has not started yet")

      if not self._current_page:
        raise RuntimeError("No current page")

      try:
        await self._current_page.update()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        await self.send_message_with_remove_with_delay(str(e))

      self._current_page.clear_buttons()

      try:
        self._current_page.create_buttons()
      except Exception as e:
        self._logger.error(traceback.format_exc())
        await self.send_message_with_remove_with_delay(str(e))

      keyboard = TelebotUtils.get_keyboard_for_buttons(
        buttons = self._current_page.buttons,
        data_prefix = TelebotPageNavigator._navigator_data_prefix,
      )

      self._markup = keyboard
      page_text = self._get_page_text(self._current_page)

      try:
        if isinstance(page_text, telebot.types.InputRichMessage):
          await self._bot.edit_message_text(
            chat_id = self._chat_id,
            message_id = self._message.message_id,
            rich_message = page_text,
            reply_markup = keyboard,
          )
        else:
          await self._bot.edit_message_text(
            text = page_text,
            chat_id = self._chat_id,
            message_id = self._message.message_id,
            reply_markup = keyboard,
            parse_mode = 'HTML',
          )
      except Exception as e:
        if "message is not modified" not in str(e).lower():
          self._logger.error(f"Failed to edit message: {e}")

  async def add_delayed_action(
    self,
    delay: float,
    action: Callable[[], Awaitable[Any]],
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
        await self.send_message_with_remove_with_delay(str(e))

    task = asyncio.create_task(delayed_task_wrapper())

    self._tasks.append(task)

    def on_done(t: asyncio.Task) -> None:
      if t in self._tasks:
        self._tasks.remove(t)

    task.add_done_callback(on_done)

  async def send_message(self, text: str) -> telebot.types.Message:
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    return await self._bot.send_message(
      self._chat_id,
      text,
      parse_mode = "HTML",
    )

  async def send_message_with_remove_with_delay(
    self,
    text: str,
    delay = 5,
  ) -> None:
    if not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    sent = await self.send_message(text[:512])

    await TelebotUtils.remove_message_with_delay(
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
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._logger.error(f"WebSocket client error: {e}")
          await asyncio.sleep(5)

    task = asyncio.create_task(instance_listener_worker())
    self._tasks.append(task)

    def on_done(t: asyncio.Task) -> None:
      if t in self._tasks:
        self._tasks.remove(t)

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

          async with self._async_lock:
            self._logger.info(f"{self.__class__.__name__}: running async on_auto_update for "
                              f"page {self._current_page.page_type.name}")
            await self._current_page.on_auto_update(navigator = self)
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._logger.error(traceback.format_exc())
          await self.send_message_with_remove_with_delay(str(e))

    task = asyncio.create_task(auto_update_worker())
    self._tasks.append(task)

    def task_done(t: asyncio.Task) -> None:
      if t in self._tasks:
        self._tasks.remove(t)

    task.add_done_callback(task_done)

  def _get_page_text(self, page: "TelebotNavigationPage") -> Union[str, telebot.types.InputRichMessage]:
    try:
      return page.text if page.text else "Untitled"
    except Exception as e:
      self._logger.error(traceback.format_exc())
      return str(e)

  async def _resend(self, text: str) -> telebot.types.Message:
    if not self._message or not self._chat_id or not self._current_page:
      raise RuntimeError("Navigation has not started yet")

    page_text = self._get_page_text(self._current_page)

    if isinstance(page_text, telebot.types.InputRichMessage):
      try:
        await self._bot.edit_message_text(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          rich_message = page_text,
        )
      except Exception:
        pass

      self._message = await self._bot.send_rich_message(
        chat_id = self._chat_id,
        rich_message = page_text,
        reply_markup = self._markup,
      )
    else:
      try:
        await self._bot.edit_message_text(
          text = f"{page_text} {text}",
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          parse_mode = 'HTML',
        )
      except Exception:
        pass

      self._message = await self._bot.send_message(
        chat_id = self._chat_id,
        text = page_text,
        reply_markup = self._markup,
        parse_mode = "HTML",
      )

    TelebotAsyncStepManager.clear_step_handler_by_chat_id(self._chat_id)
    TelebotAsyncStepManager.register_next_step_handler(
      self._message,
      self._next_step_handler,
      self._message,
    )

    return self._message

  async def stop(
    self,
    text: Optional[Union[str, telebot.types.InputRichMessage]] = None,
    delete_message: bool = False,
  ) -> None:
    if not self._current_page or not self._message or not self._chat_id:
      raise RuntimeError("Navigation has not started yet")

    tasks_to_cancel = list(self._tasks)
    self._tasks.clear()

    for task in tasks_to_cancel:
      if not task.done():
        task.cancel()

    if not self._current_page or not self._message or not self._chat_id:
      if self._chat_id and TelebotPageNavigator._instances.get(self._chat_id) == self:
        del TelebotPageNavigator._instances[self._chat_id]
      raise RuntimeError("Navigation has not started yet")

    self._current_page.on_stop()

    async def execute_message_action(
      bot: AsyncTeleBot,
      chat_id: int,
      message_id: int,
      delete_message: bool,
      text: Optional[Union[str, telebot.types.InputRichMessage]],
    ) -> None:
      """Execute message modification or deletion action."""
      try:
        if delete_message:
          await bot.delete_message(
            chat_id = chat_id,
            message_id = message_id,
          )
        elif isinstance(text, str) and text:
          await bot.edit_message_text(
            text,
            chat_id = chat_id,
            message_id = message_id,
            reply_markup = None,
            parse_mode = 'HTML',
          )
        elif isinstance(text, telebot.types.InputRichMessage):
          await bot.edit_message_text(
            chat_id = chat_id,
            message_id = message_id,
            rich_message = text,
            reply_markup = None,
          )
        else:
          await bot.edit_message_reply_markup(
            chat_id = chat_id,
            message_id = message_id,
            reply_markup = None,
          )
      except Exception:
        pass

    # Run in background task passing all parameters explicitly
    asyncio.create_task(
      execute_message_action(
        bot = self._bot,
        chat_id = self._chat_id,
        message_id = self._message.message_id,
        delete_message = delete_message,
        text = text,
      ))

    if self._chat_id and TelebotPageNavigator._instances.get(self._chat_id) == self:
      del TelebotPageNavigator._instances[self._chat_id]
    if self._chat_id:
      TelebotAsyncStepManager.clear_step_handler_by_chat_id(self._chat_id)

    self._chat_id = None
    self._message = None
    self._current_page = None
    self._main_page = None
    self._pages.clear()

  async def _handle_callback(self, button_id: str) -> None:
    async with self._async_lock:
      if not self._current_page:
        raise RuntimeError("No current page")

      try:
        await self._current_page.handle_click(
          navigator = self,
          button_id = button_id,
        )
      except Exception as e:
        self._logger.error(traceback.format_exc())
        await self.send_message_with_remove_with_delay(str(e))

  async def _on_command_button_clicked(self, command: str) -> None:
    if not self._current_page:
      raise RuntimeError("Navigation has not started yet")

    text = self._current_page.get_stop_by_command_message(command)
    await self.stop(text)

  async def _handle_server_update(self, data: Dict[str, Any]) -> None:
    async with self._async_lock:
      if not self._current_page:
        return

      try:
        self._logger.info(f"Websocket update received: {data}")
        await self._current_page.on_websocket_update(navigator = self, data = data)
      except Exception as e:
        await self.send_message_with_remove_with_delay(str(e))
        self._logger.error(traceback.format_exc())

  @staticmethod
  def _register_handlers(bot: AsyncTeleBot):
    bot.setup_middleware(CallbackCommandMiddleware(TelebotPageNavigator))

    @bot.callback_query_handler(
      func = lambda call: call.data and call.data.startswith(TelebotPageNavigator._navigator_data_prefix))
    async def _global_nav_handler(call: telebot.types.CallbackQuery):
      if not call.data or not call.message:
        return

      # Run callback answering in the background to avoid blocking execution
      asyncio.create_task(bot.answer_callback_query(call.id))

      button_id = call.data[len(TelebotPageNavigator._navigator_data_prefix):]
      chat_id = call.message.chat.id

      instance = TelebotPageNavigator._instances.get(chat_id)
      if instance:
        await instance._handle_callback(button_id = button_id)

  async def _next_step_handler(
    self,
    message: telebot.types.Message,
    sent_message: telebot.types.Message,
  ):
    # Cache references locally to prevent race conditions during await points
    main_page = self._main_page
    current_page = self._current_page

    if not main_page or not current_page:
      raise RuntimeError("Navigation has not started yet")

    if await TelebotUtils.forward_next(self._bot, message):
      text = main_page.get_goodbye_message()
      await self.stop(text)
    else:
      TelebotAsyncStepManager.register_next_step_handler(
        sent_message,
        self._next_step_handler,
        sent_message,
      )

      if message.text and current_page.need_user_input:
        try:
          async with self._async_lock:
            if current_page.resend_message_on_user_input:
              await self._resend(message.text)
              await asyncio.sleep(0.5)

            self._logger.info(f"{self.__class__.__name__}: running async handler for user input")
            await current_page.on_user_input(self, message.text)

        except Exception as e:
          self._logger.error(traceback.format_exc())
          await self.send_message_with_remove_with_delay(str(e))
