import os
import re
import tempfile

from typing import Any, Dict

from git_helper_async import GitHelperAsync
from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_registers_holder_async import DeyeRegistersHolderAsync
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebUpdateScriptsCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([DeyeWebRemoteCommand.update_scripts])
    self._git_helper = GitHelperAsync()

  async def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Dict[str, Any],
  ) -> Dict[str, str]:
    def get_result(text: str) -> Dict[str, str]:
      result: Dict[str, str] = {}

      id = DeyeWebUtils.short(DeyeWebSection.service.title)
      result[id] = text

      style_id = DeyeWebConstants.styles_template.format(command.name)
      result[style_id] = self.style_manager.generate_css()

      return result

    try:
      current_branch_name = await self._git_helper.get_current_branch_name()

      if current_branch_name == 'HEAD':
        return get_result('Unable to update: the repository is not currently on a branch')

      pull_result = await self._git_helper.pull()
      await self._git_helper.submodule_update()

      if 'up to date' in pull_result.lower():
        last_commit = await self._git_helper.get_last_commit_hash_and_comment()
        return get_result('<p style="color: green;">'
                          "Already up to date.<br>"
                          f"You are currently on branch '{current_branch_name}':<br>"
                          f"<b>{last_commit}</b></p>")

      cache_file_path = os.path.join(tempfile.gettempdir(), DeyeWebConstants.front_cache_file_name)
      DeyeWebUtils.file_truncate(cache_file_path)

      holder = DeyeRegistersHolderAsync(
        name = 'deyeweb',
        loggers = self.loggers.loggers,
      )

      try:
        await holder.reset_cache()
      finally:
        holder.disconnect()

      await DeyeWebUtils.shutdown_with_delay()
    except Exception as e:
      err = str(e).replace(': ', ':<br>').replace('\n', '<br>')
      return get_result(f'<p style="color: red;">{err}</p>')

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, pull_result)

    text = "\n".join(matches)
    text += '<br>Update completed. Please wait for page refresh to apply the changes...'

    result = get_result(text)
    result['need_reload'] = 'true'

    return result
