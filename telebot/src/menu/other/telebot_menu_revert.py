import re
import telebot

from git_helper import GitHelper
from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker import TelebotLocalUpdateChecker
from telebot_constants import TelebotConstants
from telebot_user_choices import UserChoices
from telebot_advanced_choice import AdvancedChoice
from countdown_with_cancel import CountdownWithCancel

class TelebotMenuRevert(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.git_helper = GitHelper()
    self.update_checker = TelebotLocalUpdateChecker()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.revert

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if not self.remote_update_checker.is_on_branch():
      self.bot.send_message(message.chat.id, 'Unable to revert: the repository is not currently on a branch')
      return

    try:
      branch_name = self.git_helper.get_current_branch_name()
      if not self.git_helper.is_repository_up_to_date():
        last_commit = self.git_helper.get_last_commit_hash_and_comment()
        last_commit = last_commit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.bot.send_message(
          message.chat.id,
          "Can't revert because repository is not up to date. "
          'Pls run <b>/update</b> and then try again. '
          f"You are currently on branch '{branch_name}':\n<b>{last_commit}</b>",
          parse_mode = "HTML",
        )
        self.update_checker.check_for_local_updates(self.bot, message.chat.id, force = True)
        return
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    pos = message.text.find(' ')
    if pos != -1:
      commit_hash = re.sub(r'[^0-9a-f]', '', message.text[pos + 1:])
      if len(commit_hash) >= 32:
        self.do_revert(message.chat.id, commit_hash)
        return

    try:
      last_commits = self.git_helper.get_last_commits()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    if last_commits:
      sent = AdvancedChoice.ask_advanced_choice(
        self.bot,
        message.chat.id,
        f"You are currently on branch '{branch_name}'.\n"
        'Enter commit hash to revert to:',
        {
          item: f"/revert {hash}"
          for item, hash in last_commits.items()
        },
        callback = lambda _, __: None,
        max_per_row = 1,
        edit_message_with_user_selection = True,
      )
    else:
      sent = self.bot.send_message(message.chat.id, 'Enter commit hash to revert to:')

    self.bot.clear_step_handler_by_chat_id(message.chat.id)
    self.bot.register_next_step_handler(message, self.handle_step2, sent.message_id)

  def handle_step2(self, message: telebot.types.Message, message_id: int):
    TelebotUtils.remove_inline_buttons_with_delay(
      bot = self.bot,
      chat_id = message.chat.id,
      message_id = message_id,
      delay = TelebotConstants.buttons_remove_delay_sec,
    )

    # If we received new command, skip it
    if TelebotUtils.forward_next(self.bot, message):
      return

    if message.text is not None:
      commit_hash = re.sub(r'[^0-9a-f]', '', message.text)
      if len(commit_hash) >= 32:
        self.do_revert(message.chat.id, message.text)
      else:
        self.bot.send_message(message.chat.id, f'Wrong commit hash')

  def do_revert(self, chat_id: int, commit_hash: str):
    try:
      self.git_helper.stash_clear()

      short_hash = self.git_helper.get_last_commit_short_hash()
      if commit_hash.startswith(short_hash):
        self.bot.send_message(chat_id, f'You are already on {short_hash}')
        return

      self.git_helper.stash_push()
      result = self.git_helper.revert_to_revision(commit_hash)
      self.git_helper.stash_pop()
    except Exception as e:
      self.bot.send_message(chat_id, f'{str(e)}: trying to reset to HEAD and then stash pop again...')
      try:
        self.git_helper.revert_to_revision('HEAD')
        self.git_helper.pull()
        self.git_helper.stash_pop()
        self.bot.send_message(
          chat_id,
          'All changes rolled back to the latest commit. '
          'Try to revert to another commit without conflicting changes',
        )
      except Exception as ex:
        self.bot.send_message(chat_id, str(ex))
      return

    self.bot.send_message(chat_id, result)

    UserChoices.ask_confirmation(
      self.bot,
      chat_id,
      'Revert completed. For the changes to take effect, need to restart the bot. '
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
    self.bot.send_message(chat_id, f'{CommonUtils.clock_face_one_oclock} Restarting telebot...', parse_mode = 'HTML')
    TelebotUtils.stop_bot(self.bot)

  def on_cancel(self, chat_id: int):
    self.bot.send_message(chat_id, 'Restart cancelled')
