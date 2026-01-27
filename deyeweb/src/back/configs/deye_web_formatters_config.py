from typing import Dict

from simple_singleton import singleton
from deye_web_constants import DeyeWebConstants
from deye_web_base_formatter import DeyeWebBaseFormatter
from deye_web_battery_power_formatter import DeyeWebBatteryPowerFormatter
from deye_web_grid_state_formatter import DeyeWebGridStateFormatter
from deye_web_pv_power_formatter import DeyeWebPvPowerFormatter
from deye_web_threshold_formatter import DeyeWebThresholdFormatter
from deye_web_battery_soc_formatter import DeyeWebBatterySocFormatter
from deye_web_grid_power_formatter import DeyeWebGridPowerFormatter

@singleton
class DeyeWebFormattersConfig:
  def __init__(self):
    self.base_formatter = DeyeWebBaseFormatter()
    registers = DeyeWebConstants.registers

    self.formatters: Dict[str, DeyeWebBaseFormatter] = {
      registers.battery_bms_charge_current_limit_register.name: DeyeWebThresholdFormatter(320, 100, DeyeWebConstants.threshold_colors, will_affect_tab_color = False),
      registers.battery_bms_discharge_current_limit_register.name: DeyeWebThresholdFormatter(320, 320, DeyeWebConstants.threshold_colors),
      registers.battery_power_register.name: DeyeWebBatteryPowerFormatter(3000, 1500),
      registers.battery_current_register.name: DeyeWebBatteryPowerFormatter(60, 30),
      registers.battery_soc_register.name: DeyeWebBatterySocFormatter(50, 30),
      registers.battery_soh_register.name: DeyeWebBatterySocFormatter(98, 90),
      registers.battery_temperature_register.name: DeyeWebThresholdFormatter(35, 30, DeyeWebConstants.threshold_reversed_colors),
      registers.gen_power_register.name: DeyeWebPvPowerFormatter(500, 100),
      registers.grid_charging_start_soc_register.name: DeyeWebThresholdFormatter(91 - 10, 81 - 10, DeyeWebConstants.threshold_reversed_colors, will_affect_tab_color = False),
      registers.grid_connect_voltage_low_register.name: DeyeWebThresholdFormatter(220, 220, DeyeWebConstants.threshold_reversed_colors),
      registers.grid_external_ct_power_register.name: DeyeWebGridPowerFormatter(3500, 1750),
      registers.grid_internal_ct_power_register.name: DeyeWebGridPowerFormatter(3500, 1750),
      registers.grid_reconnection_time_register.name: DeyeWebThresholdFormatter(600, 300, DeyeWebConstants.threshold_colors),
      registers.grid_state_register.name: DeyeWebGridStateFormatter(),
      registers.grid_voltage_register.name: DeyeWebThresholdFormatter(210, 195, DeyeWebConstants.threshold_colors, will_affect_tab_color = False),
      registers.inverter_ac_temperature_register.name: DeyeWebThresholdFormatter(55, 50, DeyeWebConstants.threshold_reversed_colors),
      registers.inverter_dc_temperature_register.name: DeyeWebThresholdFormatter(65, 60, DeyeWebConstants.threshold_reversed_colors),
      registers.inverter_system_time_diff_register.name: DeyeWebThresholdFormatter(60, 30, DeyeWebConstants.threshold_reversed_colors, will_affect_tab_color = False),
      registers.load_power_register.name: DeyeWebThresholdFormatter(4000, 3000, DeyeWebConstants.threshold_reversed_colors),
      registers.pv1_power_register.name: DeyeWebPvPowerFormatter(250, 50),
      registers.pv2_power_register.name: DeyeWebPvPowerFormatter(250, 50),
      registers.pv_total_power_register.name: DeyeWebPvPowerFormatter(500, 100),
      registers.time_of_use_soc_register.name: DeyeWebThresholdFormatter(35, 25, DeyeWebConstants.threshold_colors),
    }

  def get_formatter_for_register(self, register_name: str) -> DeyeWebBaseFormatter:
    return self.formatters.get(register_name, self.base_formatter)
