from typing import Any, Dict, List

from git_helper import GitHelper
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_formatters_config import DeyeWebFormattersConfig
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_sections_holder import DeyeWebSectionsHolder
from deye_web_selections_config import DeyeWebSelectionsConfig
from deye_register_average_type import DeyeRegisterAverageType
from deye_web_selections_builder_config import DeyeWebSelectionsBuilderConfig
from deye_web_style_manager import DeyeWebStyleManager

class DeyeWebBaseCommandProcessor:
  def __init__(
    self,
    commands: List[DeyeWebRemoteCommand],
  ):
    self.commands = commands
    self.loggers = DeyeWebConstants.loggers
    self.sections_holder = DeyeWebSectionsHolder()
    self.formatters_config = DeyeWebFormattersConfig()
    self.selections_config = DeyeWebSelectionsConfig()
    self.selections_builder_config = DeyeWebSelectionsBuilderConfig()
    self.style_manager = DeyeWebStyleManager()
    self.git_helper = GitHelper()

  def is_acceptable(self, command: DeyeWebRemoteCommand) -> bool:
    return command in self.commands

  def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Any,
  ) -> Dict[str, str]:
    raise NotImplementedError('get_command_result() is not implemented')

  def make_register_value(
    self,
    registers: DeyeRegisters,
    register: DeyeRegister,
    colors: Dict[str, DeyeWebColor],
  ) -> str:
    formatter = self.formatters_config.get_formatter_for_register(register.name)
    old_color = colors.get(register.name, DeyeWebColor.gray)
    new_color = formatter.get_color(registers, register)

    if register.avg_type == DeyeRegisterAverageType.only_master and registers.prefix != self.loggers.master.name:
      new_color = DeyeWebColor.gray

    if register.can_accumulate and registers.prefix != self.loggers.accumulated_registers_prefix:
      new_color = DeyeWebColor.gray

    if new_color.id > old_color.id and formatter.will_affect_tab_color:
      colors[register.name] = new_color

    return formatter.format_register(registers, register)
