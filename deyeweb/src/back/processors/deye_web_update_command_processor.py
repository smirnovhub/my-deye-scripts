import os
import re
import tempfile

from typing import Any, Dict

from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_web_remote_command import DeyeWebRemoteCommand
from processors.deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebUpdateCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([DeyeWebRemoteCommand.update_scripts])

  def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Any,
  ) -> Dict[str, str]:
    def get_result(text: str) -> Dict[str, str]:
      result: Dict[str, str] = {}

      id = DeyeWebUtils.short(DeyeWebSection.service.title)
      result[id] = text

      style_id = DeyeWebConstants.styles_template.format(command.name)
      result[style_id] = self.style_manager.generate_css()

      return result

    try:
      current_branch_name = self.git_helper.get_current_branch_name()

      if current_branch_name == 'HEAD':
        return get_result('Unable to update: the repository is not currently on a branch')

      pull_result = self.git_helper.pull()

      if 'up to date' in pull_result.lower():
        last_commit = self.git_helper.get_last_commit_hash_and_comment()
        return get_result("Already up to date.<br>"
                          f"You are currently on branch '{current_branch_name}':<br>"
                          f"<b>{last_commit}</b>")

      cache_file_path = os.path.join(tempfile.gettempdir(), DeyeWebConstants.front_cache_file_name)
      DeyeWebUtils.file_truncate(cache_file_path)
    except Exception as e:
      err = str(e).replace(': ', ':<br>').replace('\n', '<br>')
      return get_result(f'<p style="color: red;">{err}</p>')

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, pull_result)

    return get_result("\n".join(matches))
