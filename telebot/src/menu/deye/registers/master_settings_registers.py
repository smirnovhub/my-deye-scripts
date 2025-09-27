from typing import List
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory

class MasterSettingsRegisters(DeyeRegistersFactory.get_registers_class()): # type: ignore
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.backup_delay_register,
      self.grid_charging_start_soc_register,
      self.time_of_use_soc_register,
      self.time_of_use_power_register,
      self.battery_max_charge_current_register,
      self.battery_max_discharge_current_register,
      self.battery_grid_charge_current_register,
      self.battery_gen_charge_current_register,
      self.battery_low_batt_soc_register,
      self.battery_shutdown_soc_register,
      self.battery_restart_soc_register,
      self.grid_connect_voltage_high_register,
      self.grid_connect_voltage_low_register,
      self.grid_reconnect_voltage_high_register,
      self.grid_reconnect_voltage_low_register,
      self.grid_reconnection_time_register,
      self.grid_peak_shaving_power_register,
      self.gen_peak_shaving_power_register,
      self.gen_port_mode_register,
      self.system_work_mode_register,
      self.zero_export_power_register,
      self.ct_ratio_register,
    ]
