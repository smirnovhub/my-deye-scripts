import telebot
import threading
import time

from typing import Optional, List

class TelebotProgressMessage:
  def __init__(self, bot: telebot.TeleBot) -> None:
    """
    A helper class to show and manage a progress message in a Telegram chat.

    Features:
    - Displays a message with animated dots (1 → 2 → 3 → 1 ...).
    - Runs the animation in a background thread.
    - Registers a next-step handler: if the user sends any message, the progress message will be deleted.
    - Can be hidden manually by calling `hide()`.
    """
    self.bot = bot # TeleBot instance
    self._chat_id: Optional[int] = None # Chat ID (set in show())
    self._text: Optional[str] = None # Base message text (set in show())
    self._message: Optional[telebot.types.Message] = None # The sent Telegram message
    self._running: bool = False # Running flag for animation loop
    self._threads: List[threading.Thread] = [] # List of animation threads

  def show(self, chat_id: int, text: str) -> None:
    """
    Show the progress message in the given chat and start animation.

    Args:
        chat_id (int): Chat ID where the message should be sent.
        base_text (str): The base text to display before the animated dots.
    """
    # Stop all previous animations
    self._running = False
    for t in self._threads:
      t.join()
    self._threads.clear()

    # Store parameters
    self._chat_id = chat_id
    self._text = text

    self._running = True
    # Send initial message
    self._message = self.bot.send_message(self._chat_id, self._text, parse_mode = 'HTML')
    # Start animation thread
    thread = threading.Thread(target = self._animate, daemon = True)
    self._threads.append(thread)
    thread.start()
    # Register next step handler
    self.bot.clear_step_handler_by_chat_id(self._message.chat.id)
    self.bot.register_next_step_handler(self._message, self._on_user_response)

  def _animate(self) -> None:
    """
    Internal method: runs in a background thread and updates the message text every second.
    Cycles the number of dots from 1 to 3 and back to 1.
    """
    if self._text is None or self._message is None:
      return

    dots: int = 1
    count: int = 0
    while count < 15 and self._running:
      try:
        time.sleep(0.5)
        text: str = self._text + ("." * dots)
        self.bot.edit_message_text(text, self._chat_id, self._message.message_id, parse_mode = 'HTML')
        dots = (dots + 1) % 4
        count += 1
      except Exception:
        pass

    try:
      self.bot.edit_message_text(f'{self._text}...', self._chat_id, self._message.message_id, parse_mode = 'HTML')
    except Exception:
      pass

  def _on_user_response(self, message: telebot.types.Message) -> None:
    """
    Internal method: called when the user sends the next message.
    Automatically hides the progress message.
    """
    self.hide()

    # If we received new command, process it
    if message.text.startswith('/'):
      self.bot.process_new_messages([message])

  def hide(self) -> None:
    """
    Stop the animation and delete the progress message.
    Safe to call multiple times.
    """
    self._running = False

    for t in self._threads:
      t.join()

    self._threads.clear()

    try:
      if self._chat_id is not None and self._message is not None:
        self.bot.delete_message(self._chat_id, self._message.message_id)
    except Exception:
      pass

    self._message = None
