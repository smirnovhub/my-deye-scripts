from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from deye_register import DeyeRegister

class DeyeBaseRegisters(ABC):
  def __init__(self, prefix: str = ''):
    self._prefix = prefix

  @property
  @abstractmethod
  def _all_registers_internal(self) -> List[DeyeRegister]:
    pass

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return self._all_registers_internal

  @property
  def all_registers_map(self) -> Dict[str, DeyeRegister]:
    return {reg.name: reg for reg in self._all_registers_internal}

  @property
  def read_only_registers(self) -> List[DeyeRegister]:
    return [register for register in self._all_registers_internal if not register.can_write]

  @property
  def read_write_registers(self) -> List[DeyeRegister]:
    return [register for register in self._all_registers_internal if register.can_write]

  def get_register_by_name(self, name: str) -> Optional[DeyeRegister]:
    return self.all_registers_map.get(name)

  @property
  @abstractmethod
  def test_registers(self) -> List[DeyeRegister]:
    pass

  @property
  @abstractmethod
  def ac_couple_frz_high_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def backup_delay_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_bms_charge_current_limit_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_bms_discharge_current_limit_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_capacity_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_gen_charge_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_grid_charge_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_low_batt_soc_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_max_charge_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_max_discharge_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_restart_soc_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_soc_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_soh_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_shutdown_soc_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_temperature_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def battery_voltage_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def ct_ratio_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def gen_peak_shaving_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def gen_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_charging_start_soc_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_connect_voltage_high_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_connect_voltage_low_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_reconnect_voltage_high_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_reconnect_voltage_low_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_frequency_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_peak_shaving_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_internal_ct_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_external_ct_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_reconnection_time_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_state_code_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_state_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def grid_voltage_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def gen_port_mode_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def inverter_ac_temperature_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def inverter_dc_temperature_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def inverter_system_time_diff_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def inverter_system_time_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def load_frequency_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def load_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def load_voltage_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv1_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv1_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv1_voltage_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv2_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv2_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv2_voltage_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv_total_current_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def pv_total_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def system_work_mode_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def time_of_use_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def time_of_use_power_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def time_of_use_soc_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_battery_charged_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_battery_discharged_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_grid_feed_in_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_grid_purchased_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_gen_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_load_consumption_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_pv_production_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_pv_production_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def today_gen_energy_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_battery_charged_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_battery_discharged_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_grid_feed_in_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_grid_purchased_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_gen_energy_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_load_consumption_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_pv_production_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_pv_production_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def total_gen_energy_cost_register(self) -> DeyeRegister:
    pass

  @property
  @abstractmethod
  def zero_export_power_register(self) -> DeyeRegister:
    pass

  @property
  def prefix(self) -> str:
    return self._prefix
