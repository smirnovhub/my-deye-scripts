import telebot
import asyncio

from typing import Optional
from telebot.async_telebot import AsyncTeleBot
from telebot_async_step_manager import TelebotAsyncStepManager
from telebot_utils import TelebotUtils

class TelebotProgressMessage:
  def __init__(self, bot: AsyncTeleBot) -> None:
    """
    A helper class to show and manage a progress message in a Telegram chat.

    Features:
    - Displays a message with animated dots.
    - Runs the animation asynchronously via asyncio tasks.
    - Registers a next-step handler: if the user sends any message, the progress message will be deleted.
    - Can be hidden manually by calling `hide()`.
    """
    self._bot = bot
    self._chat_id: Optional[int] = None
    self._text: Optional[str] = None
    self._message: Optional[telebot.types.Message] = None
    self._running: bool = False
    self._animation_task: Optional[asyncio.Task] = None

    try:
      self._loop = asyncio.get_running_loop()
    except RuntimeError:
      self._loop = asyncio.get_event_loop()

  async def show(self, chat_id: int, text: str) -> None:
    """
    Show the progress message in the given chat and start animation.
    """
    if self._running:
      await self.hide()

    self._chat_id = chat_id
    self._text = text
    self._running = True

    self._message = await self._bot.send_message(
      chat_id = self._chat_id,
      text = self._text,
      parse_mode = 'HTML',
    )

    # Start animation task instead of thread
    self._animation_task = self._loop.create_task(self._animate())

    # Register next step handler using AsyncStepManager
    TelebotAsyncStepManager.clear_step_handler_by_chat_id(self._message.chat.id)
    TelebotAsyncStepManager.register_next_step_handler(self._message, self._on_user_response)

  async def _animate(self) -> None:
    """
    Internal method: runs asynchronously and updates the message text every half second.
    """
    if self._text is None or self._message is None:
      return

    dots: int = 1
    count: int = 0
    while count < 15 and self._running:
      try:
        await asyncio.sleep(0.5)
        if not self._running:
          break

        text: str = self._text + ("." * dots)
        await self._bot.edit_message_text(
          text = text,
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          parse_mode = 'HTML',
        )
        dots = (dots + 1) % 4
        count += 1
      except asyncio.CancelledError:
        raise
      except Exception:
        pass

    try:
      if self._running and self._message and self._chat_id:
        await self._bot.edit_message_text(
          text = f'{self._text}...',
          chat_id = self._chat_id,
          message_id = self._message.message_id,
          parse_mode = 'HTML',
        )
    except Exception:
      pass

  async def _on_user_response(self, message: telebot.types.Message) -> None:
    """
    Internal method: called when the user sends the next message.
    Automatically hides the progress message.
    """
    await self.hide()
    await TelebotUtils.forward_next(self._bot, message)

  async def hide(self) -> None:
    """
    Stop the animation and delete the progress message.
    Safe to call multiple times.
    """
    self._running = False

    if self._animation_task and not self._animation_task.done():
      self._animation_task.cancel()
      try:
        await self._animation_task
      except asyncio.CancelledError:
        pass
    self._animation_task = None

    try:
      if self._chat_id is not None and self._message is not None:
        await self._bot.delete_message(
          chat_id = self._chat_id,
          message_id = self._message.message_id,
        )
    except Exception:
      pass

    self._message = None
