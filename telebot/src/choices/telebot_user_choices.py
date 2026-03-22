import telebot

from typing import Callable, List

from button_node import ButtonNode
from telebot_page_navigator import TelebotPageNavigator
from telebot_user_choices_page import UserChoicePage

class UserChoices:
  @staticmethod
  def ask_confirmation(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    callback: Callable[[int, bool], None],
  ) -> telebot.types.Message:
    def choice_callback(chat_id_inner: int, button: ButtonNode):
      callback(chat_id_inner, button.text.lower() == 'yes')

    options = [
      ButtonNode(text = 'Yes'),
      ButtonNode(text = 'No'),
    ]

    return UserChoices.ask_choice(
      bot = bot,
      chat_id = chat_id,
      text = text,
      options = options,
      callback = choice_callback,
      accept_wrong_choice_from_user_input = True,
    )

  @staticmethod
  def ask_choice(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: List[ButtonNode],
    callback: Callable[[int, ButtonNode], None],
    max_per_row: int = 5,
    accept_wrong_choice_from_user_input: bool = False,
    wrong_choice_text: str = 'No such option',
  ) -> telebot.types.Message:
    navigator = TelebotPageNavigator(bot)

    page = UserChoicePage(
      text = text,
      options = options,
      chat_id = chat_id,
      callback = callback,
      max_per_row = max_per_row,
      accept_wrong_choice_from_user_input = accept_wrong_choice_from_user_input,
      wrong_choice_text = wrong_choice_text,
    )

    navigator.register_page(page)
    return navigator.start(page, text, chat_id)
