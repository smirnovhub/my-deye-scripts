import telebot

from typing import Callable, List

from telebot_page_navigator import TelebotPageNavigator
from telebot_sequential_choice_button import SequentialChoiceButton
from telebot_sequential_choices_page import SequentialChoicePage

class SequentialChoices:
  @staticmethod
  def ask_sequential_choices(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    root: SequentialChoiceButton,
    final_callback: Callable[[int, List[SequentialChoiceButton]], None],
  ) -> telebot.types.Message:
    if not root.children:
      return bot.send_message(
        chat_id,
        text,
        parse_mode = "HTML",
      )

    navigator = TelebotPageNavigator(bot)

    page = SequentialChoicePage(
      text = text,
      root = root,
      chat_id = chat_id,
      final_callback = final_callback,
    )

    navigator.register_page(page)
    return navigator.start(page, text, chat_id)
