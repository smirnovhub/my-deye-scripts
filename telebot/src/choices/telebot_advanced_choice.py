import asyncio

from typing import List

from telebot_buttons import *
from telebot.async_telebot import AsyncTeleBot
from telebot_advanced_choice_page import AdvancedChoicePage
from telebot_page_navigator import TelebotPageNavigator

class AdvancedChoice:
  @staticmethod
  async def ask_advanced_choice(
    bot: AsyncTeleBot,
    chat_id: int,
    text: str,
    options: List[ButtonNode],
    max_per_row: int = 5,
    max_lines_per_page: int = 5,
    add_cancel_button: bool = True,
    edit_message_with_user_selection: bool = False,
  ) -> ButtonNode:
    navigator = TelebotPageNavigator(bot)

    loop = asyncio.get_running_loop()
    future = loop.create_future()

    page = AdvancedChoicePage(
      text = text,
      options = options,
      chat_id = chat_id,
      result_future = future,
      max_per_row = max_per_row,
      max_lines_per_page = max_lines_per_page,
      add_cancel_button = add_cancel_button,
      edit_message_with_user_selection = edit_message_with_user_selection,
    )

    navigator.register_page(page)

    await navigator.start(
      page = page,
      chat_id = chat_id,
    )

    # Wait until the user completes the selection and the callback is triggered
    return await future
