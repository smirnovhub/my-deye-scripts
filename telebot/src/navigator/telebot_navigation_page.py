import inspect

from enum import Enum
from typing import Callable, Dict, List, Union

from abc import ABC, abstractmethod
from button_node import ButtonNode
from telebot_page_navigator import TelebotPageNavigator

ButtonHandler = Union[
  Callable[[TelebotPageNavigator], None],
  Callable[[TelebotPageNavigator, ButtonNode], None],
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
    self._button_handlers: Dict[int, ButtonHandler] = {}

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
  def buttons(self) -> List[ButtonNode]:
    """
    Returns the list of buttons to be displayed on this page.

    Returns:
        List[ButtonNode]: A list of button configurations.
    """
    pass

  def prepare(self, **kwargs) -> None:
    """
    Optional hook to pass data into the page before rendering.
    Can be overridden in subclasses to initialize state.

    Args:
        **kwargs: Arbitrary keyword arguments passed during navigation.
    """
    pass

  @abstractmethod
  def update(self) -> None:
    """
    Updates the internal state of the page. 
    Typically used to refresh button labels or register new handlers.
    """
    pass

  def handle_click(
    self,
    navigator: TelebotPageNavigator,
    button_id: int,
  ):
    """
    Finds the button by ID and triggers the click event.

    Args:
        navigator (TelebotPageNavigator): The navigator instance managing this page.
        button_id (int): The unique ID of the clicked button.
    """
    for button in self.buttons:
      if button.id == button_id:
        self.on_button_clicked(navigator, button)

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
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
    if len(params) >= 2:
      # Handler expects at least two arguments (navigator and button)
      handler(navigator, button)
    else:
      # Handler expects only one argument (navigator)
      handler(navigator)

  def register_button_handler(self, button: ButtonNode, handler: ButtonHandler) -> ButtonNode:
    """
    Maps a button to a specific function to be called when clicked.

    Args:
        button (ButtonNode): The button to register.
        handler (ButtonHandler): The function to execute.

    Returns:
        ButtonNode: The same button instance for chaining.
    """
    self._button_handlers[button.id] = handler
    return button

  def clear_button_handlers(self) -> None:
    """
    Removes all registered button handlers from the page.
    """
    self._button_handlers.clear()

  def get_goodbye_message(self) -> str:
    """
    Returns a message to be shown when the navigation session is closed.

    Returns:
        str: The closing message text.
    """
    return ""
