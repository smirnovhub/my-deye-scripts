import asyncio

from telebot.async_telebot import AsyncTeleBot

from typing import List

from telebot_page_navigator import TelebotPageNavigator
from telebot_sequential_choice_button import SequentialChoiceButton
from telebot_sequential_choices_page import SequentialChoicePage

class SequentialChoices:
  @staticmethod
  async def ask_sequential_choices(
    bot: AsyncTeleBot,
    chat_id: int,
    text: str,
    root: SequentialChoiceButton,
  ) -> List[SequentialChoiceButton]:
    if not root.children:
      await bot.send_message(
        chat_id,
        text,
        parse_mode = "HTML",
      )
      return []

    loop = asyncio.get_running_loop()
    future = loop.create_future()

    navigator = TelebotPageNavigator(bot)

    page = SequentialChoicePage(
      text = text,
      root = root,
      chat_id = chat_id,
      result_future = future,
    )

    navigator.register_page(page)

    await navigator.start(
      page = page,
      chat_id = chat_id,
    )

    # Wait until the user completes the selection and the callback is triggered
    return await future
