from enum import Enum
from typing import List

from abc import ABC, abstractmethod
from button_node import ButtonNode
from telebot_page_navigator import TelebotPageNavigator

class TelebotNavigationPage(ABC):
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

  def handle_click(self, navigator: TelebotPageNavigator, data: str):
    for button in self.buttons:
      if button.data == data:
        self.on_button_clicked(navigator, button)

  @abstractmethod
  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    pass
