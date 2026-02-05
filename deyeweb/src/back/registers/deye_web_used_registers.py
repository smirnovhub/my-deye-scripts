from typing import List

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class DeyeWebUsedRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      # Info registers
      self.battery_soc_register,
      self.battery_soh_register,
      self.battery_current_register,
      self.battery_power_register,
      self.grid_state_register,
      self.grid_voltage_register,
      self.grid_internal_ct_power_register,
      self.grid_external_ct_power_register,
      self.load_power_register,
      self.pv1_power_register,
      self.gen_power_register,
      self.inverter_ac_temperature_register,
      self.inverter_dc_temperature_register,
      self.battery_temperature_register,
      self.inverter_system_time_diff_register,
      self._battery_bms_charge_current_limit_register,
      self._battery_bms_discharge_current_limit_register,

      # Settings registers
      self.time_of_use_soc_register,
      self.time_of_use_power_register,
      self.grid_charging_start_soc_register,
      self.battery_capacity_register,
      self.battery_max_charge_current_register,
      self.battery_max_discharge_current_register,
      self.battery_grid_charge_current_register,
      self.battery_gen_charge_current_register,
      self.grid_connect_voltage_low_register,
      self.grid_reconnection_time_register,
      self.grid_peak_shaving_power_register,

      # Today stat registers
      self.today_pv_production_register,
      self.today_gen_energy_register,
      self.today_load_consumption_register,
      self.today_grid_purchased_energy_register,
      self.today_grid_feed_in_energy_register,
      self.today_battery_charged_energy_register,
      self.today_battery_discharged_energy_register,
      self.today_pv_production_cost_register,
      self.today_grid_purchased_energy_cost_register,
      self.today_gen_energy_cost_register,

      # Total stat registers
      self.total_pv_production_register,
      self.total_gen_energy_register,
      self.total_load_consumption_register,
      self.total_grid_purchased_energy_register,
      self.total_grid_feed_in_energy_register,
      self.total_battery_charged_energy_register,
      self.total_battery_discharged_energy_register,
      self.total_pv_production_cost_register,
      self.total_grid_purchased_energy_cost_register,
      self.total_gen_energy_cost_register,
    ]
