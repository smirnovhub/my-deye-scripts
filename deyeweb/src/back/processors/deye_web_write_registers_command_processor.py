from typing import Any, Dict

from deye_web_utils import DeyeWebUtils
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_custom_single_registers import DeyeWebCustomSingleRegisters
from deye_web_colors_calculator import DeyeWebColorsCalculator
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_registers_holder import DeyeRegistersHolder
from processors.deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebWriteRegistersCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([DeyeWebRemoteCommand.write_register])

  def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Any,
  ) -> Dict[str, str]:
    register_name = DeyeWebUtils.get_json_field(json_data, DeyeWebConstants.json_register_name_field)
    register_value = DeyeWebUtils.get_json_field(json_data, DeyeWebConstants.json_register_value_field)

    if register_name not in self.sections_holder.writable_registers:
      raise ValueError(f"Can't write '{register_name}'")

    register = DeyeWebConstants.registers.get_register_by_name(register_name)
    if register is None:
      raise ValueError(f"Unknown register '{register_name}'")

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      name = 'deyeweb',
      loggers = [self.loggers.master],
      socket_timeout = 5,
      auto_reconnect = True,
      register_creator = lambda prefix: DeyeWebCustomSingleRegisters(
        register,
        prefix,
      ),
    )

    try:
      holder.write_register(register, register_value)
    finally:
      holder.disconnect()

    result: Dict[str, str] = {}
    new_colors: Dict[str, DeyeWebColor] = {}

    session_id = DeyeWebUtils.get_json_field(json_data, DeyeWebConstants.json_session_id_field)
    colors_calculator = DeyeWebColorsCalculator(self.sections_holder, session_id)

    colors = colors_calculator.load_colors()

    id = DeyeWebUtils.short(f'{self.loggers.master.name}_{register.name}')
    result[id] = DeyeWebUtils.clean(self.make_register_value(
      holder.master_registers,
      register,
      new_colors,
    ))

    builder = self.selections_builder_config.get_selection_builder_for_register(register.name)
    selections = builder.build_selections(holder, register)
    result.update(selections)

    for reg_name, color in new_colors.items():
      colors[reg_name] = color

    selection_colors = colors_calculator.get_sections_colors(colors)
    result.update(selection_colors)

    colors_calculator.save_colors(colors)

    result[DeyeWebConstants.result_write_styles_field] = self.style_manager.generate_css()

    return result
