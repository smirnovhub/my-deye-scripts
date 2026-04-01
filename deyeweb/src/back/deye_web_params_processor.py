import logging

from typing import Any, Dict, List

from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_reset_cache_command_processor import DeyeWebResetCacheCommandProcessor
from deye_web_base_command_processor import DeyeWebBaseCommandProcessor
from deye_web_forecast_command_processor import DeyeWebForecastCommandProcessor
from deye_web_read_registers_command_processor import DeyeWebReadRegistersCommandProcessor
from deye_web_update_scripts_command_processor import DeyeWebUpdateScriptsCommandProcessor
from deye_web_install_ios_profile_command_processor import DeyeWebInstallIosProfileCommandProcessor
from deye_web_write_registers_command_processor import DeyeWebWriteRegistersCommandProcessor

class DeyeWebParamsProcessor:
  def __init__(self):
    self._processors: List[DeyeWebBaseCommandProcessor] = [
      DeyeWebReadRegistersCommandProcessor(),
      DeyeWebWriteRegistersCommandProcessor(),
      DeyeWebForecastCommandProcessor(),
      DeyeWebResetCacheCommandProcessor(),
      DeyeWebUpdateScriptsCommandProcessor(),
      DeyeWebInstallIosProfileCommandProcessor(),
    ]

  async def get_params(
    self,
    json_data: Dict[str, Any],
    logger: logging.Logger,
  ) -> Dict[str, str]:
    app_id = DeyeWebUtils.get_json_field(json_data, DeyeWebConstants.json_app_id_field)
    if not app_id:
      raise ValueError("App ID value is empty")

    # Verify that the frontend application ID matches the current backend instance ID
    # Prevent requests from being processed by the wrong or mismatched backend instance
    id = await DeyeWebUtils.get_app_id()
    if app_id != id:
      logger.error(f"App ID mismatch: expected {id}, but received {app_id}")
      raise ValueError("App ID mismatch")

    command_value = DeyeWebUtils.get_json_field(json_data, DeyeWebConstants.json_command_field)

    try:
      command = DeyeWebRemoteCommand[command_value]
    except KeyError:
      raise ValueError(f"Invalid command: '{command_value}'")

    processor = next((p for p in self._processors if p.is_acceptable(command)), None)
    if processor is None:
      raise ValueError(f"Unknown command: '{command_value}'")

    return await processor.get_command_result(command, json_data)
