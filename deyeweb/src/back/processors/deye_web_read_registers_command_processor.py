from typing import Any, Dict

from deye_web_utils import DeyeWebUtils
from deye_web_color import DeyeWebColor
from deye_web_used_registers import DeyeWebUsedRegisters
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_registers_holder import DeyeRegistersHolder
from deye_web_constants import DeyeWebConstants
from deye_web_colors_calculator import DeyeWebColorsCalculator
from deye_register_average_type import DeyeRegisterAverageType
from processors.deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebReadRegistersCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([DeyeWebRemoteCommand.read_registers])

  def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Any,
  ) -> Dict[str, str]:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      name = 'deyeweb',
      loggers = self.loggers.loggers,
      socket_timeout = 5,
      auto_reconnect = True,
      register_creator = lambda prefix: DeyeWebUsedRegisters(prefix),
    )

    try:
      holder.read_registers()
    finally:
      holder.disconnect()

    result: Dict[str, str] = {}
    colors: Dict[str, DeyeWebColor] = {}

    for inverter, registers in holder.all_registers.items():
      for register in registers.all_registers:
        if register.name not in self.sections_holder.used_registers:
          continue

        if register.avg_type == DeyeRegisterAverageType.only_master and inverter != self.loggers.master.name:
          continue

        if not register.can_accumulate and inverter == self.loggers.accumulated_registers_prefix:
          continue

        id = DeyeWebUtils.short(f'{inverter}_{register.name}')
        result[id] = DeyeWebUtils.clean(self.make_register_value(
          registers,
          register,
          colors,
        ))

    registers = holder.master_registers
    for register in registers.all_registers:
      if register.name not in self.sections_holder.used_registers:
        continue

      builder = self.selections_builder_config.get_selection_builder_for_register(register.name)
      selections = builder.build_selections(holder, register)
      result.update(selections)

    session_id = DeyeWebUtils.get_json_field(json_data, DeyeWebConstants.json_session_id_field)
    colors_calculator = DeyeWebColorsCalculator(self.sections_holder, session_id)

    selection_colors = colors_calculator.get_sections_colors(colors)
    result.update(selection_colors)

    colors_calculator.save_colors(colors)

    result[DeyeWebConstants.result_read_styles_field] = self.style_manager.generate_css()

    return result
