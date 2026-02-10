from datetime import timedelta
from typing import List, Dict

from deye_base_registers import DeyeBaseRegisters
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType
from deye_register import DeyeRegister
from float_deye_register import FloatDeyeRegister
from float_writable_deye_register import FloatWritableDeyeRegister
from gen_port_mode_writable_deye_register import GenPortModeWritableDeyeRegister
from grid_state_deye_register import GridStateDeyeRegister
from int_deye_register import IntDeyeRegister
from int_writable_deye_register import IntWritableDeyeRegister
from long_float_deye_register import LongFloatDeyeRegister
from long_float_splitted_deye_register import LongFloatSplittedDeyeRegister
from signed_float_deye_register import SignedFloatDeyeRegister
from signed_int_deye_register import SignedIntDeyeRegister
from sum_deye_register import SumDeyeRegister
from system_time_diff_deye_register import SystemTimeDiffDeyeRegister
from system_time_writable_deye_register import SystemTimeWritableDeyeRegister
from temperature_deye_register import TemperatureDeyeRegister
from test_deye_register import TestDeyeRegister
from time_of_use_int_writable_deye_register import TimeOfUseIntWritableDeyeRegister
from time_of_use_writable_deye_register import TimeOfUseWritableDeyeRegister
from today_energy_cost_register import TodayEnergyCostRegister
from total_energy_cost_register import TotalEnergyCostRegister
from system_work_mode_writable_deye_register import SystemWorkModeWritableDeyeRegister

class DeyeSun6kSg03Lp1Registers(DeyeBaseRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)
    energy_cost = DeyeEnergyCost()
    self._ac_couple_frz_high_register = FloatWritableDeyeRegister(329, 50.5, 52, 'ac_couple_frz_high', 'AC Couple Frz High', 'Hz', avg = DeyeRegisterAverageType.only_master).with_scale(100)
    self._backup_delay_register = IntWritableDeyeRegister(311, 0, 30000, 'backup_delay', 'Backup Delay', 'ms', avg = DeyeRegisterAverageType.only_master)
    self._battery_bms_charge_current_limit_register = IntDeyeRegister(314, 'battery_bms_charge_current_limit', 'Battery BMS Charge Current Limit', 'A', avg = DeyeRegisterAverageType.only_master)
    self._battery_bms_discharge_current_limit_register = IntDeyeRegister(315, 'battery_bms_discharge_current_limit', 'Battery BMS Discharge Current Limit', 'A', avg = DeyeRegisterAverageType.only_master)
    self._battery_capacity_register = IntDeyeRegister(107, 'battery_capacity', 'Battery Capacity', 'Ah', avg = DeyeRegisterAverageType.only_master, caching_time = timedelta(hours = 3))
    self._battery_current_register = SignedFloatDeyeRegister(191, 'battery_current', 'Battery Current', 'A', avg = DeyeRegisterAverageType.accumulate).with_scale(100)
    self._battery_gen_charge_current_register = IntWritableDeyeRegister(227, 0, 80, 'battery_gen_charge_current', 'Battery Gen Charge Current', 'A', avg = DeyeRegisterAverageType.accumulate)
    self._battery_grid_charge_current_register = IntWritableDeyeRegister(230, 0, 80, 'battery_grid_charge_current', 'Battery Grid Charge Current', 'A', avg = DeyeRegisterAverageType.accumulate)
    self._battery_low_batt_soc_register = IntWritableDeyeRegister(219, 5, 60, 'battery_low_batt_soc', 'Battery Low Batt SOC', '%', avg = DeyeRegisterAverageType.only_master)
    self._battery_max_charge_current_register = IntWritableDeyeRegister(210, 0, 80, 'battery_max_charge_current', 'Battery Max Charge Current', 'A', avg = DeyeRegisterAverageType.accumulate)
    self._battery_max_discharge_current_register = IntWritableDeyeRegister(211, 50, 120, 'battery_max_discharge_current', 'Battery Max Discharge Current', 'A', avg = DeyeRegisterAverageType.accumulate)
    self._battery_power_register = SignedIntDeyeRegister(190, 'battery_power', 'Battery Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._battery_restart_soc_register = IntWritableDeyeRegister(218, 5, 60, 'battery_restart_soc', 'Battery Restart SOC', '%', avg = DeyeRegisterAverageType.only_master)
    self._battery_shutdown_soc_register = IntWritableDeyeRegister(217, 5, 60, 'battery_shutdown_soc', 'Battery Shutdown SOC', '%', avg = DeyeRegisterAverageType.only_master)
    self._battery_soc_register = IntDeyeRegister(184, 'battery_soc', 'Battery SOC', '%', avg = DeyeRegisterAverageType.only_master)
    self._battery_soh_register = IntDeyeRegister(10006, 'battery_soh', 'Battery SOH', '%', avg = DeyeRegisterAverageType.only_master, caching_time = timedelta(hours = 3))
    self._battery_temperature_register = TemperatureDeyeRegister(182, 'battery_temperature', 'Battery Temperature', 'deg', avg = DeyeRegisterAverageType.only_master)
    self._battery_voltage_register = FloatDeyeRegister(183, 'battery_voltage', 'Battery Voltage', 'V', avg = DeyeRegisterAverageType.average).with_scale(100)
    self._ct_ratio_register = IntWritableDeyeRegister(327, 200, 2000, 'ct_ratio', 'CT Ratio', '', avg = DeyeRegisterAverageType.only_master)
    self._grid_internal_ct_power_register = SignedIntDeyeRegister(167, 'grid_internal_ct_power', 'Grid Internal CT Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._grid_external_ct_power_register = SignedIntDeyeRegister(170, 'grid_external_ct_power', 'Grid External CT Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._grid_charging_start_soc_register = IntWritableDeyeRegister(229, 50, 90, 'grid_charging_start_soc', 'Grid Charging Start SOC', '%', avg = DeyeRegisterAverageType.only_master)
    self._grid_connect_voltage_low_register = FloatWritableDeyeRegister(288, 195, 230, 'grid_connect_voltage_low', 'Grid Connect Voltage Low', 'V', avg = DeyeRegisterAverageType.only_master)
    self._grid_connect_voltage_high_register = FloatWritableDeyeRegister(287, 231, 255, 'grid_connect_voltage_high', 'Grid Connect Voltage High', 'V', avg = DeyeRegisterAverageType.only_master)
    self._grid_reconnect_voltage_low_register = FloatWritableDeyeRegister(434, 195, 230, 'grid_reconnect_voltage_low', 'Grid Reconnect Voltage Low', 'V', avg = DeyeRegisterAverageType.only_master)
    self._grid_reconnect_voltage_high_register = FloatWritableDeyeRegister(433, 231, 255, 'grid_reconnect_voltage_high', 'Grid Reconnect Voltage High', 'V', avg = DeyeRegisterAverageType.only_master)
    self._grid_reconnection_time_register = IntWritableDeyeRegister(282, 60, 3600, 'grid_reconnection_time', 'Grid Reconnection Time', 'sec', avg = DeyeRegisterAverageType.only_master)
    self._grid_frequency_register = FloatDeyeRegister(79, 'grid_frequency', 'Grid Frequency', 'Hz', avg = DeyeRegisterAverageType.average).with_scale(100)
    self._grid_peak_shaving_power_register = IntWritableDeyeRegister(293, 1000, 6000, 'grid_peak_shaving_power', 'Grid Peak Shaving Power', 'W', avg = DeyeRegisterAverageType.only_master)
    self._grid_power_register = SignedIntDeyeRegister(169, 'grid_power', 'Grid Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._grid_state_code_register = IntDeyeRegister(194, 'grid_state_code', 'Grid State code', '')
    self._grid_state_register = GridStateDeyeRegister(194, 'grid_state', 'Grid State', '', avg = DeyeRegisterAverageType.special)
    self._grid_voltage_register = FloatDeyeRegister(150, 'grid_voltage', 'Grid Voltage', 'V', avg = DeyeRegisterAverageType.average)
    self._gen_peak_shaving_power_register = IntWritableDeyeRegister(292, 500, 6000, 'gen_peak_shaving_power', 'Gen Peak Shaving Power', 'W', avg = DeyeRegisterAverageType.only_master)
    self._gen_port_mode_register = GenPortModeWritableDeyeRegister(235, 'gen_port_mode', 'Gen Port Mode', '', avg = DeyeRegisterAverageType.only_master)
    self._gen_power_register = SignedIntDeyeRegister(166, 'gen_power', 'Gen Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._inverter_ac_temperature_register = TemperatureDeyeRegister(91, 'inverter_ac_temperature', 'Inverter AC Temperature', 'deg', avg = DeyeRegisterAverageType.average)
    self._inverter_dc_temperature_register = TemperatureDeyeRegister(90, 'inverter_dc_temperature', 'Inverter DC Temperature', 'deg', avg = DeyeRegisterAverageType.average)
    self._inverter_system_time_register = SystemTimeWritableDeyeRegister(22, 'inverter_system_time', 'Inverter System Time', '', caching_time = timedelta(minutes = 1))
    self._load_frequency_register = FloatDeyeRegister(192, 'load_frequency', 'Load Frequency', 'Hz', avg = DeyeRegisterAverageType.average).with_scale(100)
    self._load_power_register = IntDeyeRegister(178, 'load_power', 'Load Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._load_voltage_register = FloatDeyeRegister(157, 'load_voltage', 'Load Voltage', 'V', avg = DeyeRegisterAverageType.average)
    self._pv1_current_register = FloatDeyeRegister(110, 'pv1_current', 'PV1 current', 'A', avg = DeyeRegisterAverageType.accumulate)
    self._pv1_power_register = IntDeyeRegister(186, 'pv1_power', 'PV1 Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._pv1_voltage_register = FloatDeyeRegister(109, 'pv1_voltage', 'PV1 voltage', 'V', avg = DeyeRegisterAverageType.average)
    self._pv2_current_register = FloatDeyeRegister(112, 'pv2_current', 'PV2 current', 'A', avg = DeyeRegisterAverageType.accumulate)
    self._pv2_power_register = IntDeyeRegister(187, 'pv2_power', 'PV2 Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._pv2_voltage_register = FloatDeyeRegister(111, 'pv2_voltage', 'PV2 voltage', 'V', avg = DeyeRegisterAverageType.average)
    self._system_work_mode_register = SystemWorkModeWritableDeyeRegister(244, 'system_work_mode', 'System Work Mode', '', avg = DeyeRegisterAverageType.only_master)
    self._time_of_use_power_register = TimeOfUseIntWritableDeyeRegister(256, 0, 6000, 'time_of_use_power', 'Time Of Use Power', 'W', avg = DeyeRegisterAverageType.accumulate)
    self._time_of_use_soc_register = TimeOfUseIntWritableDeyeRegister(268, 15, 100, 'time_of_use_soc', 'Time Of Use SOC', '%', avg = DeyeRegisterAverageType.only_master)
    self._today_battery_charged_energy_register = FloatDeyeRegister(70, 'today_battery_charged_energy', 'Today Battery Charged Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._today_battery_discharged_energy_register = FloatDeyeRegister(71, 'today_battery_discharged_energy', 'Today Battery Discharged Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._today_grid_feed_in_energy_register = FloatDeyeRegister(77, 'today_grid_feed_in_energy', 'Today Grid Feed-in Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._today_grid_purchased_energy_register = FloatDeyeRegister(76, 'today_grid_purchased_energy', 'Today Grid Purchased Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._today_gen_energy_register = FloatDeyeRegister(62, 'today_gen_energy', 'Today Gen Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._today_load_consumption_register = FloatDeyeRegister(84, 'today_load_consumption', 'Today Load Consumption', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._today_pv_production_register = FloatDeyeRegister(108, 'today_pv_production', 'Today PV Production', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 5))
    self._total_battery_charged_energy_register = LongFloatDeyeRegister(72, 'total_battery_charged_energy', 'Total Battery Charged Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._total_battery_discharged_energy_register = LongFloatDeyeRegister(74, 'total_battery_discharged_energy', 'Total Battery Discharged Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._total_grid_feed_in_energy_register = LongFloatDeyeRegister(81, 'total_grid_feed_in_energy', 'Total Grid Feed-in Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._total_grid_purchased_energy_register = LongFloatSplittedDeyeRegister(78, 2, 'total_grid_purchased_energy', 'Total Grid Purchased Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._total_gen_energy_register = LongFloatSplittedDeyeRegister(92, 3, 'total_gen_energy', 'Total Gen Energy', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._total_load_consumption_register = LongFloatDeyeRegister(85, 'total_load_consumption', 'Total Load Consumption', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._total_pv_production_register = LongFloatDeyeRegister(96, 'total_pv_production', 'Total PV Production', 'kWh', avg = DeyeRegisterAverageType.accumulate, caching_time = timedelta(minutes = 15))
    self._zero_export_power_register = IntWritableDeyeRegister(206, 0, 100, 'zero_export_power', 'Zero Export Power', 'W', avg = DeyeRegisterAverageType.only_master)
    self._pv_total_current_register = SumDeyeRegister([self.pv1_current_register, self.pv2_current_register], 'pv_total_current', 'PV Total current', 'A', avg = DeyeRegisterAverageType.special)
    self._pv_total_power_register = SumDeyeRegister([self.pv1_power_register, self.pv2_power_register], 'pv_total_power', 'PV Total Power', 'W', avg = DeyeRegisterAverageType.special)
    self._today_pv_production_cost_register = TodayEnergyCostRegister(self._today_pv_production_register, energy_cost.pv_energy_costs, 'today_pv_production_cost', 'Today PV Production Cost', avg = DeyeRegisterAverageType.special)
    self._today_grid_purchased_energy_cost_register = TodayEnergyCostRegister(self._today_grid_purchased_energy_register, energy_cost.grid_purchased_energy_costs, 'today_grid_purchased_energy_cost', 'Today Grid Purchased Energy Cost', avg = DeyeRegisterAverageType.special)
    self._today_grid_feed_in_energy_cost_register = TodayEnergyCostRegister(self._today_grid_feed_in_energy_register, energy_cost.grid_feed_in_energy_costs, 'today_grid_feed_in_energy_cost', 'Today Grid Feed-in Energy Cost', avg = DeyeRegisterAverageType.special)
    self._today_gen_energy_cost_register = TodayEnergyCostRegister(self._today_gen_energy_register, energy_cost.gen_energy_costs, 'today_gen_energy_cost', 'Today Gen Energy Cost', avg = DeyeRegisterAverageType.special)
    self._total_pv_production_cost_register = TotalEnergyCostRegister(self._total_pv_production_register, energy_cost.pv_energy_costs, 'total_pv_production_cost', 'Total PV Production Cost', avg = DeyeRegisterAverageType.special)
    self._total_grid_purchased_energy_cost_register = TotalEnergyCostRegister(self._total_grid_purchased_energy_register, energy_cost.grid_purchased_energy_costs, 'total_grid_purchased_energy_cost', 'Total Grid Purchased Energy Cost', avg = DeyeRegisterAverageType.special)
    self._total_grid_feed_in_energy_cost_register = TotalEnergyCostRegister(self._total_grid_feed_in_energy_register, energy_cost.grid_feed_in_energy_costs, 'total_grid_feed_in_energy_cost', 'Total Grid Feed-in Energy Cost', avg = DeyeRegisterAverageType.special)
    self._total_gen_energy_cost_register = TotalEnergyCostRegister(self._total_gen_energy_register, energy_cost.gen_energy_costs, 'total_gen_energy_cost', 'Total Gen Energy Cost', avg = DeyeRegisterAverageType.special)

    self._time_of_use_register = TimeOfUseWritableDeyeRegister(
      weekly_address = 248,
      charge_address = 274,
      time_address = 250,
      power_address = 256,
      soc_address = 268,
      min_soc = 15,
      max_power = 6000,
      name = 'time_of_use',
      description = 'Time Of Use',
      suffix = '',
      avg = DeyeRegisterAverageType.only_master,
    )

    self._inverter_system_time_diff_register = SystemTimeDiffDeyeRegister(
      self._inverter_system_time_register,
      'inverter_system_time_diff',
      'Inverter System Time Diff',
      'sec',
      DeyeRegisterAverageType.average,
    )

    self._test1_register = IntDeyeRegister(316, 'test1', 'Test1', '')
    self._test2_register = TestDeyeRegister(50, 350, 'test2', 'Test2', '')

    self._all_registers: List[DeyeRegister] = [
      self._ac_couple_frz_high_register,
      self._backup_delay_register,
      self._battery_bms_charge_current_limit_register,
      self._battery_bms_discharge_current_limit_register,
      self._battery_capacity_register,
      self._battery_current_register,
      self._battery_gen_charge_current_register,
      self._battery_grid_charge_current_register,
      self._battery_low_batt_soc_register,
      self._battery_max_charge_current_register,
      self._battery_max_discharge_current_register,
      self._battery_power_register,
      self._battery_restart_soc_register,
      self._battery_shutdown_soc_register,
      self._battery_soc_register,
      self._battery_soh_register,
      self._battery_temperature_register,
      self._battery_voltage_register,
      self._ct_ratio_register,
      self._grid_internal_ct_power_register,
      self._grid_external_ct_power_register,
      self._grid_charging_start_soc_register,
      self._grid_connect_voltage_low_register,
      self._grid_connect_voltage_high_register,
      self._grid_reconnect_voltage_low_register,
      self._grid_reconnect_voltage_high_register,
      self._grid_frequency_register,
      self._grid_peak_shaving_power_register,
      self._grid_power_register,
      self._grid_reconnection_time_register,
      self._grid_state_code_register,
      self._grid_state_register,
      self._grid_voltage_register,
      self._gen_peak_shaving_power_register,
      self._gen_port_mode_register,
      self._gen_power_register,
      self._inverter_ac_temperature_register,
      self._inverter_dc_temperature_register,
      self._inverter_system_time_diff_register,
      self._inverter_system_time_register,
      self._load_frequency_register,
      self._load_power_register,
      self._load_voltage_register,
      self._pv1_current_register,
      self._pv1_power_register,
      self._pv1_voltage_register,
      self._pv2_current_register,
      self._pv2_power_register,
      self._pv2_voltage_register,
      self._pv_total_current_register,
      self._pv_total_power_register,
      self._system_work_mode_register,
      self._time_of_use_register,
      self._time_of_use_power_register,
      self._time_of_use_soc_register,
      self._today_battery_charged_energy_register,
      self._today_battery_discharged_energy_register,
      self._today_grid_feed_in_energy_register,
      self._today_grid_purchased_energy_register,
      self._today_gen_energy_register,
      self._today_load_consumption_register,
      self._today_pv_production_register,
      self._today_pv_production_cost_register,
      self._today_grid_purchased_energy_cost_register,
      self._today_grid_feed_in_energy_cost_register,
      self._today_gen_energy_cost_register,
      self._total_battery_charged_energy_register,
      self._total_battery_discharged_energy_register,
      self._total_grid_feed_in_energy_register,
      self._total_grid_purchased_energy_register,
      self._total_gen_energy_register,
      self._total_load_consumption_register,
      self._total_pv_production_register,
      self._total_pv_production_cost_register,
      self._total_grid_purchased_energy_cost_register,
      self._total_grid_feed_in_energy_cost_register,
      self._total_gen_energy_cost_register,
      self._zero_export_power_register,
    ]

    self._all_registers_map: Dict[str, DeyeRegister] = {reg.name: reg for reg in self._all_registers}

    self._test_registers: List[DeyeRegister] = [
      self._test1_register,
      self._test2_register,
    ]

  @property
  def prefix(self) -> str:
    return self._prefix

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return self._all_registers

  @property
  def all_registers_map(self) -> Dict[str, DeyeRegister]:
    return self._all_registers_map

  @property
  def test_registers(self) -> List[DeyeRegister]:
    return self._test_registers

  @property
  def read_only_registers(self) -> List[DeyeRegister]:
    return [register for register in self._all_registers if register.can_write == False]

  @property
  def read_write_registers(self) -> List[DeyeRegister]:
    return [register for register in self._all_registers if register.can_write == True]

  @property
  def ac_couple_frz_high_register(self) -> DeyeRegister:
    return self._ac_couple_frz_high_register

  @property
  def backup_delay_register(self) -> DeyeRegister:
    return self._backup_delay_register

  @property
  def battery_bms_charge_current_limit_register(self) -> DeyeRegister:
    return self._battery_bms_charge_current_limit_register

  @property
  def battery_bms_discharge_current_limit_register(self) -> DeyeRegister:
    return self._battery_bms_discharge_current_limit_register

  @property
  def battery_capacity_register(self) -> DeyeRegister:
    return self._battery_capacity_register

  @property
  def battery_current_register(self) -> DeyeRegister:
    return self._battery_current_register

  @property
  def battery_gen_charge_current_register(self) -> DeyeRegister:
    return self._battery_gen_charge_current_register

  @property
  def battery_grid_charge_current_register(self) -> DeyeRegister:
    return self._battery_grid_charge_current_register

  @property
  def battery_low_batt_soc_register(self) -> DeyeRegister:
    return self._battery_low_batt_soc_register

  @property
  def battery_max_charge_current_register(self) -> DeyeRegister:
    return self._battery_max_charge_current_register

  @property
  def battery_max_discharge_current_register(self) -> DeyeRegister:
    return self._battery_max_discharge_current_register

  @property
  def battery_power_register(self) -> DeyeRegister:
    return self._battery_power_register

  @property
  def battery_restart_soc_register(self) -> DeyeRegister:
    return self._battery_restart_soc_register

  @property
  def battery_soc_register(self) -> DeyeRegister:
    return self._battery_soc_register

  @property
  def battery_soh_register(self) -> DeyeRegister:
    return self._battery_soh_register

  @property
  def battery_shutdown_soc_register(self) -> DeyeRegister:
    return self._battery_shutdown_soc_register

  @property
  def battery_temperature_register(self) -> DeyeRegister:
    return self._battery_temperature_register

  @property
  def battery_voltage_register(self) -> DeyeRegister:
    return self._battery_voltage_register

  @property
  def ct_ratio_register(self) -> DeyeRegister:
    return self._ct_ratio_register

  @property
  def gen_peak_shaving_power_register(self) -> DeyeRegister:
    return self._gen_peak_shaving_power_register

  @property
  def gen_power_register(self) -> DeyeRegister:
    return self._gen_power_register

  @property
  def grid_charging_start_soc_register(self) -> DeyeRegister:
    return self._grid_charging_start_soc_register

  @property
  def grid_connect_voltage_high_register(self) -> DeyeRegister:
    return self._grid_connect_voltage_high_register

  @property
  def grid_connect_voltage_low_register(self) -> DeyeRegister:
    return self._grid_connect_voltage_low_register

  @property
  def grid_reconnect_voltage_high_register(self) -> DeyeRegister:
    return self._grid_reconnect_voltage_high_register

  @property
  def grid_reconnect_voltage_low_register(self) -> DeyeRegister:
    return self._grid_reconnect_voltage_low_register

  @property
  def grid_frequency_register(self) -> DeyeRegister:
    return self._grid_frequency_register

  @property
  def grid_peak_shaving_power_register(self) -> DeyeRegister:
    return self._grid_peak_shaving_power_register

  @property
  def grid_power_register(self) -> DeyeRegister:
    return self._grid_power_register

  @property
  def grid_internal_ct_power_register(self) -> DeyeRegister:
    return self._grid_internal_ct_power_register

  @property
  def grid_external_ct_power_register(self) -> DeyeRegister:
    return self._grid_external_ct_power_register

  @property
  def grid_reconnection_time_register(self) -> DeyeRegister:
    return self._grid_reconnection_time_register

  @property
  def grid_state_code_register(self) -> DeyeRegister:
    return self._grid_state_code_register

  @property
  def grid_state_register(self) -> DeyeRegister:
    return self._grid_state_register

  @property
  def grid_voltage_register(self) -> DeyeRegister:
    return self._grid_voltage_register

  @property
  def gen_port_mode_register(self) -> DeyeRegister:
    return self._gen_port_mode_register

  @property
  def inverter_ac_temperature_register(self) -> DeyeRegister:
    return self._inverter_ac_temperature_register

  @property
  def inverter_dc_temperature_register(self) -> DeyeRegister:
    return self._inverter_dc_temperature_register

  @property
  def inverter_system_time_diff_register(self) -> DeyeRegister:
    return self._inverter_system_time_diff_register

  @property
  def inverter_system_time_register(self) -> DeyeRegister:
    return self._inverter_system_time_register

  @property
  def load_frequency_register(self) -> DeyeRegister:
    return self._load_frequency_register

  @property
  def load_power_register(self) -> DeyeRegister:
    return self._load_power_register

  @property
  def load_voltage_register(self) -> DeyeRegister:
    return self._load_voltage_register

  @property
  def pv1_current_register(self) -> DeyeRegister:
    return self._pv1_current_register

  @property
  def pv1_power_register(self) -> DeyeRegister:
    return self._pv1_power_register

  @property
  def pv1_voltage_register(self) -> DeyeRegister:
    return self._pv1_voltage_register

  @property
  def pv2_current_register(self) -> DeyeRegister:
    return self._pv2_current_register

  @property
  def pv2_power_register(self) -> DeyeRegister:
    return self._pv2_power_register

  @property
  def pv2_voltage_register(self) -> DeyeRegister:
    return self._pv2_voltage_register

  @property
  def pv_total_current_register(self) -> DeyeRegister:
    return self._pv_total_current_register

  @property
  def pv_total_power_register(self) -> DeyeRegister:
    return self._pv_total_power_register

  @property
  def system_work_mode_register(self) -> DeyeRegister:
    return self._system_work_mode_register

  @property
  def time_of_use_register(self) -> DeyeRegister:
    return self._time_of_use_register

  @property
  def time_of_use_power_register(self) -> DeyeRegister:
    return self._time_of_use_power_register

  @property
  def time_of_use_soc_register(self) -> DeyeRegister:
    return self._time_of_use_soc_register

  @property
  def today_battery_charged_energy_register(self) -> DeyeRegister:
    return self._today_battery_charged_energy_register

  @property
  def today_battery_discharged_energy_register(self) -> DeyeRegister:
    return self._today_battery_discharged_energy_register

  @property
  def today_grid_feed_in_energy_register(self) -> DeyeRegister:
    return self._today_grid_feed_in_energy_register

  @property
  def today_grid_purchased_energy_register(self) -> DeyeRegister:
    return self._today_grid_purchased_energy_register

  @property
  def today_gen_energy_register(self) -> DeyeRegister:
    return self._today_gen_energy_register

  @property
  def today_load_consumption_register(self) -> DeyeRegister:
    return self._today_load_consumption_register

  @property
  def today_pv_production_register(self) -> DeyeRegister:
    return self._today_pv_production_register

  @property
  def today_pv_production_cost_register(self) -> DeyeRegister:
    return self._today_pv_production_cost_register

  @property
  def today_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return self._today_grid_purchased_energy_cost_register

  @property
  def today_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return self._today_grid_feed_in_energy_cost_register

  @property
  def today_gen_energy_cost_register(self) -> DeyeRegister:
    return self._today_gen_energy_cost_register

  @property
  def total_battery_charged_energy_register(self) -> DeyeRegister:
    return self._total_battery_charged_energy_register

  @property
  def total_battery_discharged_energy_register(self) -> DeyeRegister:
    return self._total_battery_discharged_energy_register

  @property
  def total_grid_feed_in_energy_register(self) -> DeyeRegister:
    return self._total_grid_feed_in_energy_register

  @property
  def total_grid_purchased_energy_register(self) -> DeyeRegister:
    return self._total_grid_purchased_energy_register

  @property
  def total_gen_energy_register(self) -> DeyeRegister:
    return self._total_gen_energy_register

  @property
  def total_load_consumption_register(self) -> DeyeRegister:
    return self._total_load_consumption_register

  @property
  def total_pv_production_register(self) -> DeyeRegister:
    return self._total_pv_production_register

  @property
  def total_pv_production_cost_register(self) -> DeyeRegister:
    return self._total_pv_production_cost_register

  @property
  def total_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return self._total_grid_purchased_energy_cost_register

  @property
  def total_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return self._total_grid_feed_in_energy_cost_register

  @property
  def total_gen_energy_cost_register(self) -> DeyeRegister:
    return self._total_gen_energy_cost_register

  @property
  def zero_export_power_register(self) -> DeyeRegister:
    return self._zero_export_power_register
