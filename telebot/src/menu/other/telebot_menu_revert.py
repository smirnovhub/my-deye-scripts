import re
import telebot

from telebot.async_telebot import AsyncTeleBot

from typing import List

from button_node import ButtonNode
from git_helper_async import GitHelperAsync
from common_utils import CommonUtils
from telebot_utils import TelebotUtils

from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync
from telebot_local_update_checker_async import TelebotLocalUpdateCheckerAsync
from telebot_user_choices import UserChoices
from telebot_advanced_choice import AdvancedChoice
from countdown_with_cancel import CountdownWithCancel

class TelebotMenuRevert(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(bot = bot, )
    self._git_helper = GitHelperAsync()
    self._update_checker = TelebotLocalUpdateCheckerAsync()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.revert

  async def process_message(self, message: telebot.types.Message) -> None:
    if not await self._remote_update_checker.is_on_branch():
      await self.bot.send_message(message.chat.id, 'Unable to revert: the repository is not currently on a branch')
      return

    try:
      branch_name = await self._git_helper.get_current_branch_name()
      if not await self._git_helper.is_repository_up_to_date():
        last_commit = await self._git_helper.get_last_commit_hash_and_comment()
        last_commit = last_commit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        await self.bot.send_message(
          message.chat.id,
          "Can't revert because repository is not up to date. "
          'Pls run <b>/update</b> and then try again. '
          f"You are currently on branch '{branch_name}':\n<b>{last_commit}</b>",
          parse_mode = "HTML",
        )
        await self._update_checker.check_for_local_updates(self.bot, message.chat.id, force = True)
        return
    except Exception as e:
      await self.bot.send_message(message.chat.id, str(e))
      return

    pos = message.text.find(' ')
    if pos != -1:
      commit_hash = re.sub(r'[^0-9a-f]', '', message.text[pos + 1:])
      if len(commit_hash) >= 32:
        await self._do_revert(message.chat.id, commit_hash)
        return

    try:
      last_commits = await self._git_helper.get_last_commits()
    except Exception as e:
      await self.bot.send_message(message.chat.id, str(e))
      return

    options: List[ButtonNode] = [
      ButtonNode(text = item, data = f"/revert {hash}") for item, hash in last_commits.items()
    ]

    if not last_commits:
      await self.bot.send_message(
        message.chat.id,
        "No commits found",
      )
      return

    await AdvancedChoice.ask_advanced_choice(
      bot = self.bot,
      chat_id = message.chat.id,
      text = (f"You are currently on branch '{branch_name}'.\n"
              "Enter commit hash to revert to:"),
      options = options,
      max_per_row = 1,
      edit_message_with_user_selection = True,
    )

  async def _do_revert(self, chat_id: int, commit_hash: str):
    try:
      await self._git_helper.stash_clear()

      short_hash = await self._git_helper.get_last_commit_short_hash()
      if commit_hash.startswith(short_hash):
        await self.bot.send_message(chat_id, f'You are already on {short_hash}')
        return

      await self._git_helper.stash_push()
      result = await self._git_helper.revert_to_revision(commit_hash)
      await self._git_helper.submodule_update()
      await self._git_helper.stash_pop()
    except Exception as e:
      await self.bot.send_message(chat_id, f'{str(e)}: trying to reset to HEAD and then stash pop again...')
      try:
        await self._git_helper.revert_to_revision('HEAD')
        await self._git_helper.pull()
        await self._git_helper.submodule_update()
        await self._git_helper.stash_pop()

        await self.bot.send_message(
          chat_id,
          'All changes rolled back to the latest commit. '
          'Try to revert to another commit without conflicting changes',
        )
      except Exception as ex:
        await self.bot.send_message(chat_id, str(ex))
      return

    await self.bot.send_message(chat_id, result)

    res = await UserChoices.ask_confirmation(
      self.bot,
      chat_id,
      'Revert completed. For the changes to take effect, need to restart the bot. '
      '<b>Do you want to restart it now?</b>',
    )

    if not res:
      await self.bot.send_message(chat_id, 'Restart cancelled')
      return

    res = await CountdownWithCancel.show_countdown(
      bot = self.bot,
      chat_id = chat_id,
      text = 'Will restart in: ',
      seconds = 5,
    )

    if res:
      await self.bot.send_message(
        chat_id,
        f'{CommonUtils.clock_face_one_oclock} Restarting telebot...',
      )
      await TelebotUtils.stop_bot()
    else:
      await self.bot.send_message(
        chat_id,
        'Restart cancelled',
      )
