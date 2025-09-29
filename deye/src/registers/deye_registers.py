from typing import List, Optional

from deye_register import DeyeRegister
from deye_exceptions import DeyeNotImplementedException

class DeyeRegisters:
  def __init__(self, prefix: str = ''):
    self._prefix = prefix

  @property
  def prefix(self) -> str:
    return self._prefix

  def get_register_by_name(self, name: str) -> Optional[DeyeRegister]:
    for register in self.all_registers:
      if register.name == name:
        return register
    return None

  @property
  def all_registers(self) -> List[DeyeRegister]:
    raise self.not_implemented('all_registers')

  @property
  def forecast_registers(self) -> List[DeyeRegister]:
    raise self.not_implemented('forecast_registers')

  @property
  def test_registers(self) -> List[DeyeRegister]:
    raise self.not_implemented('test_registers')

  @property
  def read_only_registers(self) -> List[DeyeRegister]:
    raise self.not_implemented('read_only_registers')

  @property
  def read_write_registers(self) -> List[DeyeRegister]:
    raise self.not_implemented('read_write_registers')

  @property
  def ac_couple_frz_high_register(self) -> DeyeRegister:
    raise self.not_implemented('ac_couple_frz_high_register')

  @property
  def backup_delay_register(self) -> DeyeRegister:
    raise self.not_implemented('backup_delay_register')

  @property
  def battery_bms_charge_current_limit_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_bms_charge_current_limit_register')

  @property
  def battery_bms_discharge_current_limit_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_bms_discharge_current_limit_register')

  @property
  def battery_capacity_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_capacity_register')

  @property
  def battery_current_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_current_register')

  @property
  def battery_gen_charge_current_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_gen_charge_current_register')

  @property
  def battery_grid_charge_current_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_grid_charge_current_register')

  @property
  def battery_low_batt_soc_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_low_batt_soc_register')

  @property
  def battery_max_charge_current_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_max_charge_current_register')

  @property
  def battery_max_discharge_current_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_max_discharge_current_register')

  @property
  def battery_power_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_power_register')

  @property
  def battery_restart_soc_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_restart_soc_register')

  @property
  def battery_soc_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_soc_register')

  @property
  def battery_soh_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_soh_register')

  @property
  def battery_shutdown_soc_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_shutdown_soc_register')

  @property
  def battery_temperature_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_temperature_register')

  @property
  def battery_voltage_register(self) -> DeyeRegister:
    raise self.not_implemented('battery_voltage_register')

  @property
  def ct_ratio_register(self) -> DeyeRegister:
    raise self.not_implemented('ct_ratio_register')

  @property
  def charge_forecast_register(self) -> DeyeRegister:
    raise self.not_implemented('charge_forecast_register')

  @property
  def discharge_forecast_register(self) -> DeyeRegister:
    raise self.not_implemented('discharge_forecast_register')

  @property
  def gen_peak_shaving_power_register(self) -> DeyeRegister:
    raise self.not_implemented('gen_peak_shaving_power_register')

  @property
  def gen_power_register(self) -> DeyeRegister:
    raise self.not_implemented('gen_power_register')

  @property
  def grid_charging_start_soc_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_charging_start_soc_register')

  @property
  def grid_connect_voltage_high_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_connect_voltage_high_register')

  @property
  def grid_connect_voltage_low_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_connect_voltage_low_register')

  @property
  def grid_reconnect_voltage_high_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_reconnect_voltage_high_register')

  @property
  def grid_reconnect_voltage_low_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_reconnect_voltage_low_register')

  @property
  def grid_frequency_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_frequency_register')

  @property
  def grid_peak_shaving_power_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_peak_shaving_power_register')

  @property
  def grid_power_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_power_register')

  @property
  def grid_internal_ct_power_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_internal_ct_power_register')

  @property
  def grid_external_ct_power_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_external_ct_power_register')

  @property
  def grid_reconnection_time_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_reconnection_time_register')

  @property
  def grid_state_code_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_state_code_register')

  @property
  def grid_state_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_state_register')

  @property
  def grid_voltage_register(self) -> DeyeRegister:
    raise self.not_implemented('grid_voltage_register')

  @property
  def gen_port_mode_register(self) -> DeyeRegister:
    raise self.not_implemented('gen_port_mode_register')

  @property
  def inverter_ac_temperature_register(self) -> DeyeRegister:
    raise self.not_implemented('inverter_ac_temperature_register')

  @property
  def inverter_dc_temperature_register(self) -> DeyeRegister:
    raise self.not_implemented('inverter_dc_temperature_register')

  @property
  def inverter_self_consumption_power_register(self) -> DeyeRegister:
    raise self.not_implemented('inverter_self_consumption_power_register')

  @property
  def inverter_system_time_diff_register(self) -> DeyeRegister:
    raise self.not_implemented('inverter_system_time_diff_register')

  @property
  def inverter_system_time_register(self) -> DeyeRegister:
    raise self.not_implemented('inverter_system_time_register')

  @property
  def load_frequency_register(self) -> DeyeRegister:
    raise self.not_implemented('load_frequency_register')

  @property
  def load_power_register(self) -> DeyeRegister:
    raise self.not_implemented('load_power_register')

  @property
  def load_voltage_register(self) -> DeyeRegister:
    raise self.not_implemented('load_voltage_register')

  @property
  def pv1_current_register(self) -> DeyeRegister:
    raise self.not_implemented('pv1_current_register')

  @property
  def pv1_power_register(self) -> DeyeRegister:
    raise self.not_implemented('pv1_power_register')

  @property
  def pv1_voltage_register(self) -> DeyeRegister:
    raise self.not_implemented('pv1_voltage_register')

  @property
  def pv2_current_register(self) -> DeyeRegister:
    raise self.not_implemented('pv2_current_register')

  @property
  def pv2_power_register(self) -> DeyeRegister:
    raise self.not_implemented('pv2_power_register')

  @property
  def pv2_voltage_register(self) -> DeyeRegister:
    raise self.not_implemented('pv2_voltage_register')

  @property
  def pv_total_current_register(self) -> DeyeRegister:
    raise self.not_implemented('pv_total_current_register')

  @property
  def pv_total_power_register(self) -> DeyeRegister:
    raise self.not_implemented('pv_total_power_register')

  @property
  def system_work_mode_register(self) -> DeyeRegister:
    raise self.not_implemented('system_work_mode_register')

  @property
  def time_of_use_power_register(self) -> DeyeRegister:
    raise self.not_implemented('time_of_use_power_register')

  @property
  def time_of_use_soc_register(self) -> DeyeRegister:
    raise self.not_implemented('time_of_use_soc_register')

  @property
  def today_battery_charged_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('today_battery_charged_energy_register')

  @property
  def today_battery_discharged_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('today_battery_discharged_energy_register')

  @property
  def today_grid_feed_in_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('today_grid_feed_in_energy_register')

  @property
  def today_grid_purchased_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('today_grid_purchased_energy_register')

  @property
  def today_gen_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('today_gen_energy_register')

  @property
  def today_load_consumption_register(self) -> DeyeRegister:
    raise self.not_implemented('today_load_consumption_register')

  @property
  def today_production_register(self) -> DeyeRegister:
    raise self.not_implemented('today_production_register')

  @property
  def today_production_cost_register(self) -> DeyeRegister:
    raise self.not_implemented('today_production_cost_register')

  @property
  def today_gen_energy_cost_register(self) -> DeyeRegister:
    raise self.not_implemented('today_gen_energy_cost_register')

  @property
  def total_battery_charged_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('total_battery_charged_energy_register')

  @property
  def total_battery_discharged_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('total_battery_discharged_energy_register')

  @property
  def total_grid_feed_in_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('total_grid_feed_in_energy_register')

  @property
  def total_grid_purchased_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('total_grid_purchased_energy_register')

  @property
  def total_gen_energy_register(self) -> DeyeRegister:
    raise self.not_implemented('total_gen_energy_register')

  @property
  def total_load_consumption_register(self) -> DeyeRegister:
    raise self.not_implemented('total_load_consumption_register')

  @property
  def total_production_register(self) -> DeyeRegister:
    raise self.not_implemented('total_production_register')

  @property
  def total_production_cost_register(self) -> DeyeRegister:
    raise self.not_implemented('total_production_cost_register')

  @property
  def total_gen_energy_cost_register(self) -> DeyeRegister:
    raise self.not_implemented('total_gen_energy_cost_register')

  @property
  def zero_export_power_register(self) -> DeyeRegister:
    raise self.not_implemented('zero_export_power_register')

  def not_implemented(self, message: str) -> Exception:
    return DeyeNotImplementedException(f'{type(self).__name__}.{message} is not implemented')
