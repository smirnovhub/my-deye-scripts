import re
import telebot

from git_helper_async import GitHelperAsync
from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from git_exceptions import GitException
from telebot_menu_item import TelebotMenuItem
from telebot_async_runner import TelebotAsyncRunner
from telebot_user_choices import UserChoices
from countdown_with_cancel import CountdownWithCancel
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuUpdate(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
    )
    self._git_helper = GitHelperAsync()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.update

  async def process_message(self, message: telebot.types.Message) -> None:
    if not await self._remote_update_checker.is_on_branch():
      self.bot.send_message(message.chat.id, 'Unable to update: the repository is not currently on a branch')
      return

    try:
      result = await self._git_helper.pull()
      await self._git_helper.submodule_update()
    except GitException as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    if 'up to date' in result.lower():
      try:
        branch_name = await self._git_helper.get_current_branch_name()
        last_commit = await self._git_helper.get_last_commit_hash_and_comment()
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
        return

      last_commit = last_commit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

      self.bot.send_message(
        message.chat.id,
        'Already up to date. '
        f"You are currently on branch '{branch_name}':\n<b>{last_commit}</b>",
        parse_mode = "HTML",
      )

      await self._local_update_checker.check_for_local_updates(self.bot, message.chat.id, force = True)

      return

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, result)

    for match in matches:
      self.bot.send_message(message.chat.id, match)

    UserChoices.ask_confirmation(
      self.bot,
      message.chat.id,
      'Update completed. For the changes to take effect, need to restart the bot. '
      '<b>Do you want to restart it now?</b>',
      self.on_user_confirmation,
    )

  def on_user_confirmation(self, chat_id: int, result: bool):
    if not result:
      self.bot.send_message(chat_id, 'Restart cancelled')
      return

    CountdownWithCancel.show_countdown(
      bot = self.bot,
      chat_id = chat_id,
      text = 'Will restart in: ',
      seconds = 5,
      on_finish = self.on_finish,
      on_cancel = self.on_cancel,
    )

  def on_finish(self, chat_id: int):
    self.bot.send_message(chat_id, f'{CommonUtils.clock_face_one_oclock} Restarting telebot...')
    TelebotUtils.stop_bot()

  def on_cancel(self, chat_id: int):
    self.bot.send_message(chat_id, 'Restart cancelled')
