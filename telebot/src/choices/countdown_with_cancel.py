import asyncio
from datetime import timedelta
import telebot

from telebot_page_navigator import TelebotPageNavigator
from countdown_with_cancel_page import CountdownWithCancelPage

class CountdownWithCancel:
  @staticmethod
  async def show_countdown(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    seconds: int,
  ) -> bool:
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    navigator = TelebotPageNavigator(
      bot,
      auto_update_period = timedelta(seconds = 1),
    )

    page = CountdownWithCancelPage(
      chat_id = chat_id,
      text = text,
      seconds = seconds,
      result_future = future,
    )

    navigator.register_page(page)

    await navigator.start(
      page = page,
      chat_id = chat_id,
    )

    # Wait until the user completes the selection and the callback is triggered
    return await future
