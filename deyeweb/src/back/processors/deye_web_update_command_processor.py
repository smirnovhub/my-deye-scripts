import re

from typing import Any, Dict

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
    def get_result(result: str) -> Dict[str, str]:
      id = DeyeWebUtils.short(DeyeWebSection.update.title)
      return {id: result + self.style_manager.generate_css()}

    try:
      current_branch_name = self.git_helper.get_current_branch_name()

      if current_branch_name == 'HEAD':
        return get_result('Unable to update: the repository is not currently on a branch')

      pull_result = self.git_helper.pull()

      if 'up to date' in pull_result.lower():
        last_commit = self.git_helper.get_last_commit_hash_and_comment()
        return get_result("Already up to date.<br>"
                          f"You are currently on '{current_branch_name}':<br><b>{last_commit}</b>")
    except Exception as e:
      err = str(e).replace(': ', ':<br>')
      return get_result(f'<p style="color: red;">{err}</p>')

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, pull_result)

    return get_result("\n".join(matches))
