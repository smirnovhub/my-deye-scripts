import os
import tempfile

from typing import Any, Dict

from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_registers_holder import DeyeRegistersHolder
from deye_web_remote_command import DeyeWebRemoteCommand
from processors.deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebResetCacheCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([DeyeWebRemoteCommand.reset_cache])

  def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Any,
  ) -> Dict[str, str]:
    result: Dict[str, str] = {}

    cache_file_path = os.path.join(tempfile.gettempdir(), DeyeWebConstants.front_cache_file_name)
    DeyeWebUtils.file_truncate(cache_file_path)

    id = DeyeWebUtils.short(DeyeWebSection.service.title)
    result[id] = 'Cache has been reset. The page will now refresh to apply the changes.'

    result['need_reload'] = 'true'

    holder = DeyeRegistersHolder(name = 'deyeweb', loggers = self.loggers.loggers)

    try:
      holder.reset_cache()
    except Exception as e:
      result[id] = f'<p style="color: red;">{str(e)}</p>'
      result['need_reload'] = 'false'
    finally:
      holder.disconnect()

    DeyeWebUtils.shutdown_with_delay()

    style_id = DeyeWebConstants.styles_template.format(command.name)
    result[style_id] = self.style_manager.generate_css()

    return result
