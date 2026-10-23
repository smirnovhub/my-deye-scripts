import asyncio
import telebot

from telebot.async_telebot import AsyncTeleBot

from typing import List, Union

from telebot_buttons import *
from telebot_page_navigator import TelebotPageNavigator
from telebot_user_choices_page import UserChoicePage

class UserChoices:
  @staticmethod
  async def ask_confirmation(
    bot: AsyncTeleBot,
    chat_id: int,
    text: Union[str, telebot.types.InputRichMessage],
  ) -> bool:
    yes_button = ButtonNode(text = 'Yes')
    no_button = ButtonNode(text = 'No')

    button = await UserChoices.ask_choice(
      bot = bot,
      chat_id = chat_id,
      text = text,
      options = [yes_button, no_button],
      accept_wrong_choice_from_user_input = True,
    )

    return button.text == yes_button.text

  @staticmethod
  async def ask_choice(
    bot: AsyncTeleBot,
    chat_id: int,
    text: Union[str, telebot.types.InputRichMessage],
    options: List[ButtonNode],
    max_per_row: int = 5,
    accept_wrong_choice_from_user_input: bool = False,
    wrong_choice_text: str = 'No such option',
  ) -> ButtonNode:
    navigator = TelebotPageNavigator(bot)

    future = asyncio.get_running_loop().create_future()
    page = UserChoicePage(
      text = text,
      options = options,
      chat_id = chat_id,
      result_future = future,
      max_per_row = max_per_row,
      accept_wrong_choice_from_user_input = accept_wrong_choice_from_user_input,
      wrong_choice_text = wrong_choice_text,
    )

    navigator.register_page(page)

    await navigator.start(
      page = page,
      chat_id = chat_id,
    )

    # Wait until the user completes the selection and the callback is triggered
    return await future
