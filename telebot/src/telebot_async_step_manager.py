import asyncio
import telebot
import threading

from telebot.async_telebot import AsyncTeleBot
from typing import Dict, Set, Tuple, Callable, Awaitable, Any
from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate

class TelebotAsyncStepManager:
  """
  Universal helper that provides drop-in asynchronous equivalents for
  clear_step_handler_by_chat_id and register_next_step_handler.
  """
  _registered_bots: Set[AsyncTeleBot] = set()
  _callbacks: Dict[int, Tuple[Callable[..., Awaitable[Any]], Tuple]] = {}
  _lock = threading.Lock()

  @classmethod
  def setup(cls, bot: AsyncTeleBot) -> None:
    """Initializes the middleware on the bot instance once."""
    if bot not in cls._registered_bots:
      bot.setup_middleware(cls._StepMiddleware())
      cls._registered_bots.add(bot)

  @classmethod
  def clear_step_handler_by_chat_id(cls, chat_id: int) -> None:
    """Equivalent to clear_step_handler_by_chat_id."""
    with cls._lock:
      cls._callbacks.pop(chat_id, None)

  @classmethod
  def register_next_step_handler(
    cls,
    message: telebot.types.Message,
    callback: Callable[..., Awaitable[Any]],
    *args: Any,
  ) -> None:
    """Equivalent to register_next_step_handler with async callback execution."""
    if not message.chat:
      return

    chat_id = message.chat.id
    with cls._lock:
      cls._callbacks[chat_id] = (callback, args)

  class _StepMiddleware(BaseMiddleware):
    def __init__(self):
      super().__init__()
      self.update_types = ['message']

    async def pre_process(self, message: telebot.types.Message, data):
      if not message.chat:
        return

      chat_id = message.chat.id

      with TelebotAsyncStepManager._lock:
        item = TelebotAsyncStepManager._callbacks.get(chat_id)

      if item:
        callback, args = item
        # Clear step immediately for one-shot behavior
        TelebotAsyncStepManager.clear_step_handler_by_chat_id(chat_id)
        # Run callback asynchronously in background without waiting
        asyncio.ensure_future(callback(message, *args))
        # Block other handlers
        return CancelUpdate()

    async def post_process(self, message, data, exception = None):
      pass
