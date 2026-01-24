from typing import Dict

from simple_singleton import singleton
from deye_web_constants import DeyeWebConstants
from deye_web_base_selection_builder import DeyeWebBaseSelectionBuilder
from deye_web_grid_connect_voltage_low_selection_builder import DeyeWebGridConnectVoltageLowSelectionBuilder

@singleton
class DeyeWebSelectionsBuilderConfig:
  def __init__(self):
    self.base_builder = DeyeWebBaseSelectionBuilder()
    registers = DeyeWebConstants.registers

    self.builders: Dict[str, DeyeWebBaseSelectionBuilder] = {
      registers.grid_connect_voltage_low_register.name: DeyeWebGridConnectVoltageLowSelectionBuilder(),
    }

  def get_selection_builder_for_register(self, register_name: str) -> DeyeWebBaseSelectionBuilder:
    return self.builders.get(register_name, self.base_builder)
