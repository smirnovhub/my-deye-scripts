import inspect
import logging
import telebot

from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from abc import ABC, abstractmethod
from button_node import ButtonNode
from telebot_page_navigator import TelebotPageNavigator

ButtonHandler = Union[
  Callable[[TelebotPageNavigator], Awaitable[Any]],
  Callable[[TelebotPageNavigator, ButtonNode], Awaitable[Any]],
]

class TelebotNavigationPage(ABC):
  """
  Abstract base class representing a single UI page in the telegram bot navigation system.
  Each page manages its own buttons and click handlers.
  """
  def __init__(self):
    """
    Initializes the page and its internal button handler storage.
    """
    self._buttons: List[ButtonNode] = []
    self._button_handlers: Dict[str, ButtonHandler] = {}
    self._logger = logging.getLogger()

  @property
  @abstractmethod
  def page_type(self) -> Enum:
    """
    Returns the unique identifier for the page type.

    Returns:
        Enum: The enumeration value identifying this page.
    """
    pass

  @property
  @abstractmethod
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    pass

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def resend_message_on_user_input(self) -> bool:
    return True

  @property
  def buttons(self) -> List[ButtonNode]:
    """
    Returns the list of buttons to be displayed on this page.

    Returns:
        List[ButtonNode]: A list of button configurations.
    """
    return self._buttons

  async def on_navigate(
    self,
    navigator: TelebotPageNavigator,
    **kwargs: Any,
  ) -> None:
    """
    Optional hook to pass data into the page before rendering.
    Can be overridden in subclasses to initialize state.

    Args:
        **kwargs: Arbitrary keyword arguments passed during navigation.
    """
    pass

  @abstractmethod
  def create_buttons(self) -> None:
    """
    Creates buttons for the page. 
    """
    pass

  async def update(self) -> None:
    """
    Updates state of the page. 
    """
    pass

  async def handle_click(
    self,
    navigator: TelebotPageNavigator,
    button_id: str,
  ):
    """
    Finds the button by ID and triggers the click event.

    Args:
        navigator (TelebotPageNavigator): The navigator instance managing this page.
        button_id (int): The unique ID of the clicked button.
    """
    for button in self.buttons:
      if button.id == button_id:
        await self.on_button_clicked(navigator, button)
        break

  async def on_button_clicked(
    self,
    navigator: TelebotPageNavigator,
    button: ButtonNode,
  ) -> None:
    """
    Executes the registered handler for the specific button.
    Supports handlers with (navigator) or (navigator, button) signatures.

    Args:
        navigator (TelebotPageNavigator): The current navigator instance.
        button (ButtonNode): The button that was clicked.
    """
    handler = self._button_handlers.get(button.id)
    if not handler:
      return

    # Check the handler signature to provide flexible callback arguments
    signature = inspect.signature(handler)
    params = list(signature.parameters.values())

    # Logic to decide how many arguments to pass
    if len(params) == 1:
      # Handler expects only one argument (navigator)
      await handler(navigator) # type: ignore
    elif len(params) == 2:
      # Handler expects two arguments (navigator and button)
      await handler(navigator, button) # type: ignore
    else:
      raise ValueError(f"Unsupported argument count for button {button.text}")

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    pass

  async def on_websocket_update(
    self,
    navigator: TelebotPageNavigator,
    data: Dict[str, Any],
  ) -> None:
    pass

  def on_stop(self):
    pass

  async def on_auto_update(self, navigator: TelebotPageNavigator) -> None:
    pass

  def register_button(
    self,
    button: ButtonNode,
    handler: Optional[ButtonHandler] = None,
  ) -> None:
    page_key = f":{self.page_type}"

    if page_key in button.key:
      raise RuntimeError(f"Button was already used on page {self.page_type} {button.__class__.__name__} "
                         f"(id: '{button.id}', text: '{button.text}', data: '{button.data}', key: '{button.key}')")

    button.set_key(f"{button.key}{page_key}")

    if handler is not None:
      self._register_button_handler(button, handler)

    self._buttons.append(button)

  def _register_button_handler(self, button: ButtonNode, handler: ButtonHandler) -> None:
    """
    Maps a button to a specific function to be called when clicked.

    Args:
        button (ButtonNode): The button to register.
        handler (ButtonHandler): The function to execute.

    Returns:
        ButtonNode: The same button instance for chaining.
    """
    if button.id in self._button_handlers:
      raise RuntimeError(f"Duplicated button handler detected on page {self.page_type} {button.__class__.__name__} "
                         f"(id: '{button.id}', text: '{button.text}', data: '{button.data}', key: '{button.key}')")

    self._button_handlers[button.id] = handler

  def clear_buttons(self) -> None:
    """
    Removes all registered buttons and handlers from the page.
    """
    self._buttons.clear()
    self._button_handlers.clear()

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    """
    Returns a message to be shown when the navigation session is closed.

    Returns:
        str: The closing message text.
    """
    return ""

  def get_stop_by_command_message(self, command: str) -> Union[str, telebot.types.InputRichMessage]:
    return ""
