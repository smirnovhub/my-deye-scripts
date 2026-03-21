import telebot

from typing import Callable, List, Optional

from button_node import ButtonNode
from telebot_advanced_choice_page import AdvancedChoicePage
from telebot_page_navigator import TelebotPageNavigator

class AdvancedChoice:
  @staticmethod
  def ask_advanced_choice(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: List[ButtonNode],
    callback: Optional[Callable[[int, ButtonNode], None]] = None,
    max_per_row: int = 5,
    max_lines_per_page: int = 5,
    edit_message_with_user_selection: bool = False,
  ) -> telebot.types.Message:
    navigator = TelebotPageNavigator(bot)

    page = AdvancedChoicePage(
      text = text,
      options = options,
      chat_id = chat_id,
      callback = callback,
      max_per_row = max_per_row,
      max_lines_per_page = max_lines_per_page,
      edit_message_with_user_selection = edit_message_with_user_selection,
    )

    navigator.register_page(page)
    return navigator.start(page, text, chat_id)
