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
  def __init__(self):
    self._button_handlers: Dict[int, ButtonHandler] = {}

  @property
  @abstractmethod
  def page_type(self) -> Enum:
    pass

  @property
  @abstractmethod
  def buttons(self) -> List[ButtonNode]:
    pass

  def prepare(self, **kwargs) -> None:
    """
    Optional hook to pass data into the page before rendering.
    Can be overridden in subclasses.
    """
    pass

  @abstractmethod
  def update(self) -> None:
    pass

  def handle_click(
    self,
    navigator: TelebotPageNavigator,
    button_id: int,
  ):
    for button in self.buttons:
      if button.id == button_id:
        self.on_button_clicked(navigator, button)

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    handler = self._button_handlers.get(button.id)
    if not handler:
      return

    # Get the number of parameters the handler accepts
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
    self._button_handlers[button.id] = handler
    return button

  def clear_button_handlers(self) -> None:
    self._button_handlers.clear()
