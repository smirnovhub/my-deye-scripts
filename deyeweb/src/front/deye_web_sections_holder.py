from typing import List

from simple_singleton import singleton
from deye_web_base_section import DeyeWebBaseSection
from deye_web_base_select_section import DeyeWebBaseSelectSection
from deye_web_bms_section import DeyeWebBmsSection
from custom.deye_web_forecast_section import DeyeWebForecastSection
from deye_web_update_section import DeyeWebUpdateSection
from deye_web_constants import DeyeWebConstants
from deye_web_registers_section import DeyeWebRegistersSection
from deye_web_info_section import DeyeWebInfoSection
from deye_web_today_section import DeyeWebTodaySection
from deye_web_total_section import DeyeWebTotalSection
from deye_web_settings_section import DeyeWebSettingsSection
from deye_web_time_of_use_soc_section import DeyeWebTimeOfUseSocSection
from deye_web_time_of_use_power_section import DeyeWebTimeOfUsePowerSection
from deye_web_grid_peak_shaving_power_section import DeyeWebGridPeakShavingPowerSection
from deye_web_gen_charge_current_section import DeyeWebGenChargeCurrentSection
from deye_web_grid_charge_current_section import DeyeWebGridChargeCurrentSection
from deye_web_max_charge_current_section import DeyeWebMaxChargeCurrentSection
from deye_web_grid_reconnection_time_section import DeyeWebGridReconnectionTimeSection
from deye_web_grid_connect_voltage_low_section import DeyeWebGridConnectVoltageLowSection

@singleton
class DeyeWebSectionsHolder:
  def __init__(self):
    self._settings_menu_position = 4
    registers = DeyeWebConstants.registers
    self._sections: List[DeyeWebBaseSection] = [
      DeyeWebInfoSection(registers),
      DeyeWebGridConnectVoltageLowSection(registers),
      DeyeWebTodaySection(registers),
      DeyeWebTotalSection(registers),
      DeyeWebForecastSection(registers),
      DeyeWebTimeOfUseSocSection(registers),
      DeyeWebTimeOfUsePowerSection(registers),
      DeyeWebMaxChargeCurrentSection(registers),
      DeyeWebGridChargeCurrentSection(registers),
      DeyeWebGenChargeCurrentSection(registers),
      DeyeWebGridPeakShavingPowerSection(registers),
      DeyeWebGridReconnectionTimeSection(registers),
      DeyeWebBmsSection(registers),
      DeyeWebUpdateSection(),
    ]

    self._registers_sections: List[DeyeWebRegistersSection] = []
    self._writable_sections: List[DeyeWebRegistersSection] = []

    for section in self._sections:
      if isinstance(section, DeyeWebRegistersSection):
        self._registers_sections.append(section)
      if isinstance(section, DeyeWebBaseSelectSection):
        self._writable_sections.append(section)

    self._sections.insert(self._settings_menu_position, DeyeWebSettingsSection(self._writable_sections))
    self._used_registers = [reg.name for section in self._registers_sections for reg in section.registers]
    self._writable_registers = [reg.name for section in self._writable_sections for reg in section.registers]

  @property
  def sections(self) -> List[DeyeWebBaseSection]:
    return self._sections

  @property
  def registers_sections(self) -> List[DeyeWebRegistersSection]:
    return self._registers_sections

  @property
  def writable_sections(self) -> List[DeyeWebRegistersSection]:
    return self._writable_sections

  @property
  def used_registers(self) -> List[str]:
    return self._used_registers

  @property
  def writable_registers(self) -> List[str]:
    return self._writable_registers
