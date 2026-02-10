from typing import List

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_registers_section import DeyeWebRegistersSection
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebSettingsSection(DeyeWebBaseInfoSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(
      DeyeWebSection.settings,
      only_master = True,
    )
    self._registers: List[DeyeRegister] = [
      registers.grid_connect_voltage_low_register,
      registers.time_of_use_soc_register,
      registers.time_of_use_power_register,
      registers.battery_max_charge_current_register,
      registers.battery_grid_charge_current_register,
      registers.battery_gen_charge_current_register,
      registers.grid_peak_shaving_power_register,
      registers.battery_capacity_register,
      registers.grid_reconnection_time_register,
    ]

  def build_registers_str(self, registers: List[DeyeRegister]) -> str:
    from deye_web_sections_holder import DeyeWebSectionsHolder
    sections_holder = DeyeWebSectionsHolder()

    result = ''

    for register in registers:
      on_click = self.get_on_click(register, sections_holder.writable_sections)
      result += self.build_register(register.description, register, on_click)

    return result

  def get_on_click(self, register: DeyeRegister, sections: List[DeyeWebRegistersSection]) -> str:
    for section in sections:
      if any(reg.name == register.name for reg in section.registers):
        return self.format_click_string(section.section.id)
    return ''

  def format_click_string(self, section_id: str) -> str:
    tab_id = DeyeWebUtils.short(DeyeWebConstants.tab_template.format(section_id))
    page_id = DeyeWebUtils.short(DeyeWebConstants.page_template.format(section_id))
    return f"openPage('{page_id}', '{tab_id}', true);"
