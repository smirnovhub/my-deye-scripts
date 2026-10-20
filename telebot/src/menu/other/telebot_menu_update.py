import re
import telebot

from telebot.async_telebot import AsyncTeleBot

from git_helper_async import GitHelperAsync
from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from git_exceptions import GitException
from telebot_menu_item import TelebotMenuItem

from telebot_user_choices import UserChoices
from countdown_with_cancel import CountdownWithCancel
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuUpdate(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(bot = bot, )
    self._git_helper = GitHelperAsync()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.update

  async def process_message(self, message: telebot.types.Message) -> None:
    if not await self._remote_update_checker.is_on_branch():
      await self.bot.send_message(message.chat.id, 'Unable to update: the repository is not currently on a branch')
      return

    try:
      result = await self._git_helper.pull()
      await self._git_helper.submodule_update()
    except GitException as e:
      await self.bot.send_message(
        message.chat.id,
        str(e),
      )
      return

    if 'up to date' in result.lower():
      try:
        branch_name = await self._git_helper.get_current_branch_name()
        last_commit = await self._git_helper.get_last_commit_hash_and_comment()
      except Exception as ee:
        await self.bot.send_message(
          message.chat.id,
          str(ee),
        )
        return

      last_commit = last_commit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

      await self.bot.send_message(
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
      await self.bot.send_message(message.chat.id, match)

    res = await UserChoices.ask_confirmation(
      self.bot,
      message.chat.id,
      'Update completed. For the changes to take effect, need to restart the bot. '
      '<b>Do you want to restart it now?</b>',
    )

    if not res:
      await self.bot.send_message(message.chat.id, 'Restart cancelled')
      return

    res = await CountdownWithCancel.show_countdown(
      bot = self.bot,
      chat_id = message.chat.id,
      text = 'Will restart in: ',
      seconds = 5,
    )

    if res:
      await self.bot.send_message(
        message.chat.id,
        f'{CommonUtils.clock_face_one_oclock} Restarting telebot...',
      )
      await TelebotUtils.stop_bot()
    else:
      await self.bot.send_message(
        message.chat.id,
        'Restart cancelled',
      )
