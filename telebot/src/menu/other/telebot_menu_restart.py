import telebot

from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from telebot_menu_item import TelebotMenuItem
from telebot_user_choices import UserChoices
from telebot_async_runner import TelebotAsyncRunner
from countdown_with_cancel import CountdownWithCancel
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuRestart(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
    )

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.restart

  async def process_message(self, message: telebot.types.Message) -> None:
    result = await UserChoices.ask_confirmation(
      self.bot,
      message.chat.id,
      f'<b>Warning!</b> Bot process will be killed '
      'and will <b>not</b> restart automatically if you didn\'t configure it '
      'for automatic restart. <b>Do you really want to kill bot process?</b>',
    )

    if not result:
      self.bot.send_message(message.chat.id, 'Restart cancelled')
      return

    result = await CountdownWithCancel.show_countdown(
      bot = self.bot,
      chat_id = message.chat.id,
      text = 'Will restart in: ',
      seconds = 5,
    )

    if result:
      self.bot.send_message(
        message.chat.id,
        f'{CommonUtils.clock_face_one_oclock} Restarting telebot...',
      )
      TelebotUtils.stop_bot()
    else:
      self.bot.send_message(
        message.chat.id,
        'Restart cancelled',
      )
