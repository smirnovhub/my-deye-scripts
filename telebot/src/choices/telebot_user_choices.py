import asyncio
import telebot

from typing import Any, Callable, Coroutine, List, Optional, Union, cast

from button_node import ButtonNode
from telebot_async_runner import TelebotAsyncRunner
from telebot_page_navigator import TelebotPageNavigator
from telebot_user_choices_page import UserChoicePage

class UserChoices:
  @staticmethod
  def ask_confirmation(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    callback: Union[
      Callable[[int, bool], None],
      Callable[[int, bool], Coroutine[Any, Any, None]],
    ],
    runner: Optional[TelebotAsyncRunner] = None,
  ) -> telebot.types.Message:
    # Check if the original callback is async at the very beginning
    is_async = asyncio.iscoroutinefunction(callback)

    final_callback: Union[
      Callable[[int, ButtonNode], None],
      Callable[[int, ButtonNode], Coroutine[Any, Any, None]],
    ]

    if is_async:
      async_cb = cast(Callable[[int, bool], Coroutine[Any, Any, None]], callback)

      # Use an async wrapper to maintain the async nature for the runner
      async def async_choice_callback(chat_id_inner: int, button: ButtonNode) -> None:
        is_yes = button.text.lower() == 'yes'
        await async_cb(chat_id_inner, is_yes)

      final_callback = async_choice_callback
    else:
      # Use a regular sync wrapper
      def sync_choice_callback(chat_id_inner: int, button: ButtonNode) -> None:
        is_yes = button.text.lower() == 'yes'
        callback(chat_id_inner, is_yes)

      final_callback = sync_choice_callback

    options = [
      ButtonNode(text = 'Yes'),
      ButtonNode(text = 'No'),
    ]

    return UserChoices.ask_choice(
      bot = bot,
      chat_id = chat_id,
      text = text,
      options = options,
      callback = final_callback,
      runner = runner,
      accept_wrong_choice_from_user_input = True,
    )

  @staticmethod
  def ask_choice(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: List[ButtonNode],
    callback: Union[
      Callable[[int, ButtonNode], None],
      Callable[[int, ButtonNode], Coroutine[Any, Any, None]],
    ],
    runner: Optional[TelebotAsyncRunner] = None,
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
      runner = runner,
      max_per_row = max_per_row,
      accept_wrong_choice_from_user_input = accept_wrong_choice_from_user_input,
      wrong_choice_text = wrong_choice_text,
    )

    navigator.register_page(page)
    return navigator.start(page, text, chat_id)
