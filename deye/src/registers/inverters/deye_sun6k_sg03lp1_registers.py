from typing import List, Dict

from datetime import timedelta
from functools import cached_property

from deye_loggers import DeyeLoggers
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
    self._loggers = DeyeLoggers()
    self._energy_cost = DeyeEnergyCost()

  @cached_property
  def ac_couple_frz_high_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      329,
      50.5,
      52,
      'ac_couple_frz_high',
      'AC Couple Frz High',
      'Hz',
      avg = DeyeRegisterAverageType.only_master,
    ).with_scale(100)

  @cached_property
  def backup_delay_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      311,
      0,
      30000,
      'backup_delay',
      'Backup Delay',
      'ms',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_bms_charge_current_limit_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      314,
      'battery_bms_charge_current_limit',
      'Battery BMS Charge Current Limit',
      'A',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_bms_discharge_current_limit_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      315,
      'battery_bms_discharge_current_limit',
      'Battery BMS Discharge Current Limit',
      'A',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_capacity_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      107,
      'battery_capacity',
      'Battery Capacity',
      'Ah',
      avg = DeyeRegisterAverageType.only_master,
      caching_time = timedelta(hours = 12),
    )

  @cached_property
  def battery_current_register(self) -> DeyeRegister:
    return SignedFloatDeyeRegister(
      191,
      'battery_current',
      'Battery Current',
      'A',
      avg = DeyeRegisterAverageType.accumulate,
    ).with_scale(100)

  @cached_property
  def battery_gen_charge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      227,
      0,
      80,
      'battery_gen_charge_current',
      'Battery Gen Charge Current',
      'A',
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_grid_charge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      230,
      0,
      80,
      'battery_grid_charge_current',
      'Battery Grid Charge Current',
      'A',
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_low_batt_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      219,
      5,
      60,
      'battery_low_batt_soc',
      'Battery Low Batt SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_max_charge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      210,
      0,
      80,
      'battery_max_charge_current',
      'Battery Max Charge Current',
      'A',
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_max_discharge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      211,
      50,
      120,
      'battery_max_discharge_current',
      'Battery Max Discharge Current',
      'A',
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      190,
      'battery_power',
      'Battery Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def battery_restart_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      218,
      5,
      60,
      'battery_restart_soc',
      'Battery Restart SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_soc_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      184,
      'battery_soc',
      'Battery SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_soh_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      10006,
      'battery_soh',
      'Battery SOH',
      '%',
      avg = DeyeRegisterAverageType.only_master,
      caching_time = timedelta(hours = 12),
    )

  @cached_property
  def battery_shutdown_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      217,
      5,
      60,
      'battery_shutdown_soc',
      'Battery Shutdown SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      182,
      'battery_temperature',
      'Battery Temperature',
      'deg',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      183,
      'battery_voltage',
      'Battery Voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def ct_ratio_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      327,
      200,
      2000,
      'ct_ratio',
      'CT Ratio',
      '',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def gen_peak_shaving_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      292,
      500,
      6000,
      'gen_peak_shaving_power',
      'Gen Peak Shaving Power',
      'W',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def gen_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      166,
      'gen_power',
      'Gen Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_charging_start_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      229,
      50,
      90,
      'grid_charging_start_soc',
      'Grid Charging Start SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_connect_voltage_high_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      287,
      231,
      255,
      'grid_connect_voltage_high',
      'Grid Connect Voltage High',
      'V',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_connect_voltage_low_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      288,
      195,
      230,
      'grid_connect_voltage_low',
      'Grid Connect Voltage Low',
      'V',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_reconnect_voltage_high_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      433,
      231,
      255,
      'grid_reconnect_voltage_high',
      'Grid Reconnect Voltage High',
      'V',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_reconnect_voltage_low_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      434,
      195,
      230,
      'grid_reconnect_voltage_low',
      'Grid Reconnect Voltage Low',
      'V',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_frequency_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      79,
      'grid_frequency',
      'Grid Frequency',
      'Hz',
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def grid_peak_shaving_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      293,
      1000,
      6000,
      'grid_peak_shaving_power',
      'Grid Peak Shaving Power',
      'W',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      169,
      'grid_power',
      'Grid Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_internal_ct_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      167,
      'grid_internal_ct_power',
      'Grid Internal CT Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_external_ct_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      170,
      'grid_external_ct_power',
      'Grid External CT Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_reconnection_time_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      282,
      60,
      3600,
      'grid_reconnection_time',
      'Grid Reconnection Time',
      'sec',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_state_code_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      194,
      'grid_state_code',
      'Grid State code',
      '',
    )

  @cached_property
  def grid_state_register(self) -> DeyeRegister:
    return GridStateDeyeRegister(
      194,
      'grid_state',
      'Grid State',
      '',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def grid_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      150,
      'grid_voltage',
      'Grid Voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def gen_port_mode_register(self) -> DeyeRegister:
    return GenPortModeWritableDeyeRegister(
      235,
      'gen_port_mode',
      'Gen Port Mode',
      '',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def inverter_ac_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      91,
      'inverter_ac_temperature',
      'Inverter AC Temperature',
      'deg',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_dc_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      90,
      'inverter_dc_temperature',
      'Inverter DC Temperature',
      'deg',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_system_time_diff_register(self) -> DeyeRegister:
    return SystemTimeDiffDeyeRegister(
      self.inverter_system_time_register,
      'inverter_system_time_diff',
      'Inverter System Time Diff',
      'sec',
      DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_system_time_register(self) -> DeyeRegister:
    return SystemTimeWritableDeyeRegister(
      22,
      'inverter_system_time',
      'Inverter System Time',
      '',
      caching_time = timedelta(seconds = 50),
    )

  @cached_property
  def load_frequency_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      192,
      'load_frequency',
      'Load Frequency',
      'Hz',
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def load_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      178,
      'load_power',
      'Load Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def load_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      157,
      'load_voltage',
      'Load Voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv1_current_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      110,
      'pv1_current',
      'PV1 current',
      'A',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv1_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      186,
      'pv1_power',
      'PV1 Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv1_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      109,
      'pv1_voltage',
      'PV1 voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv2_current_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      112,
      'pv2_current',
      'PV2 current',
      'A',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv2_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      187,
      'pv2_power',
      'PV2 Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv2_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      111,
      'pv2_voltage',
      'PV2 voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv_total_current_register(self) -> DeyeRegister:
    return SumDeyeRegister(
      [
        self.pv1_current_register,
        self.pv2_current_register,
      ],
      'pv_total_current',
      'PV Total current',
      'A',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def pv_total_power_register(self) -> DeyeRegister:
    return SumDeyeRegister(
      [
        self.pv1_power_register,
        self.pv2_power_register,
      ],
      'pv_total_power',
      'PV Total Power',
      'W',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def system_work_mode_register(self) -> DeyeRegister:
    return SystemWorkModeWritableDeyeRegister(
      244,
      'system_work_mode',
      'System Work Mode',
      '',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def time_of_use_register(self) -> DeyeRegister:
    return TimeOfUseWritableDeyeRegister(
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

  @cached_property
  def time_of_use_power_register(self) -> DeyeRegister:
    return TimeOfUseIntWritableDeyeRegister(
      256,
      0,
      6000,
      'time_of_use_power',
      'Time Of Use Power',
      'W',
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def time_of_use_soc_register(self) -> DeyeRegister:
    return TimeOfUseIntWritableDeyeRegister(
      268,
      15,
      100,
      'time_of_use_soc',
      'Time Of Use SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def today_battery_charged_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      70,
      'today_battery_charged_energy',
      'Today Battery Charged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_battery_discharged_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      71,
      'today_battery_discharged_energy',
      'Today Battery Discharged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_grid_feed_in_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      77,
      'today_grid_feed_in_energy',
      'Today Grid Feed-in Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_grid_purchased_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      76,
      'today_grid_purchased_energy',
      'Today Grid Purchased Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_gen_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      62,
      'today_gen_energy',
      'Today Gen Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_load_consumption_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      84,
      'today_load_consumption',
      'Today Load Consumption',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_pv_production_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      108,
      'today_pv_production',
      'Today PV Production',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_pv_production_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_pv_production_register,
      self._energy_cost.pv_energy_costs,
      'today_pv_production_cost',
      'Today PV Production Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_grid_purchased_energy_register,
      self._energy_cost.grid_purchased_energy_costs,
      'today_grid_purchased_energy_cost',
      'Today Grid Purchased Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_grid_feed_in_energy_register,
      self._energy_cost.grid_feed_in_energy_costs,
      'today_grid_feed_in_energy_cost',
      'Today Grid Feed-in Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_gen_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_gen_energy_register,
      self._energy_cost.gen_energy_costs,
      'today_gen_energy_cost',
      'Today Gen Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_battery_charged_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      72,
      'total_battery_charged_energy',
      'Total Battery Charged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_battery_discharged_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      74,
      'total_battery_discharged_energy',
      'Total Battery Discharged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_grid_feed_in_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      81,
      'total_grid_feed_in_energy',
      'Total Grid Feed-in Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_grid_purchased_energy_register(self) -> DeyeRegister:
    return LongFloatSplittedDeyeRegister(
      78,
      2,
      'total_grid_purchased_energy',
      'Total Grid Purchased Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_gen_energy_register(self) -> DeyeRegister:
    return LongFloatSplittedDeyeRegister(
      92,
      3,
      'total_gen_energy',
      'Total Gen Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_load_consumption_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      85,
      'total_load_consumption',
      'Total Load Consumption',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_pv_production_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      96,
      'total_pv_production',
      'Total PV Production',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_pv_production_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_pv_production_register,
      self._energy_cost.pv_energy_costs,
      'total_pv_production_cost',
      'Total PV Production Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_grid_purchased_energy_register,
      self._energy_cost.grid_purchased_energy_costs,
      'total_grid_purchased_energy_cost',
      'Total Grid Purchased Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_grid_feed_in_energy_register,
      self._energy_cost.grid_feed_in_energy_costs,
      'total_grid_feed_in_energy_cost',
      'Total Grid Feed-in Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_gen_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_gen_energy_register,
      self._energy_cost.gen_energy_costs,
      'total_gen_energy_cost',
      'Total Gen Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def zero_export_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      206,
      0,
      100,
      'zero_export_power',
      'Zero Export Power',
      'W',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def test1_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      316,
      'test1',
      'Test1',
      '',
    )

  @cached_property
  def test2_register(self) -> DeyeRegister:
    return TestDeyeRegister(
      50,
      350,
      'test2',
      'Test2',
      '',
    )

  @cached_property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.ac_couple_frz_high_register,
      self.backup_delay_register,
      self.battery_bms_charge_current_limit_register,
      self.battery_bms_discharge_current_limit_register,
      self.battery_capacity_register,
      self.battery_current_register,
      self.battery_gen_charge_current_register,
      self.battery_grid_charge_current_register,
      self.battery_low_batt_soc_register,
      self.battery_max_charge_current_register,
      self.battery_max_discharge_current_register,
      self.battery_power_register,
      self.battery_restart_soc_register,
      self.battery_shutdown_soc_register,
      self.battery_soc_register,
      self.battery_soh_register,
      self.battery_temperature_register,
      self.battery_voltage_register,
      self.ct_ratio_register,
      self.grid_internal_ct_power_register,
      self.grid_external_ct_power_register,
      self.grid_charging_start_soc_register,
      self.grid_connect_voltage_low_register,
      self.grid_connect_voltage_high_register,
      self.grid_reconnect_voltage_low_register,
      self.grid_reconnect_voltage_high_register,
      self.grid_frequency_register,
      self.grid_peak_shaving_power_register,
      self.grid_power_register,
      self.grid_reconnection_time_register,
      self.grid_state_code_register,
      self.grid_state_register,
      self.grid_voltage_register,
      self.gen_peak_shaving_power_register,
      self.gen_port_mode_register,
      self.gen_power_register,
      self.inverter_ac_temperature_register,
      self.inverter_dc_temperature_register,
      self.inverter_system_time_diff_register,
      self.inverter_system_time_register,
      self.load_frequency_register,
      self.load_power_register,
      self.load_voltage_register,
      self.pv1_current_register,
      self.pv1_power_register,
      self.pv1_voltage_register,
      self.pv2_current_register,
      self.pv2_power_register,
      self.pv2_voltage_register,
      self.pv_total_current_register,
      self.pv_total_power_register,
      self.system_work_mode_register,
      self.time_of_use_register,
      self.time_of_use_power_register,
      self.time_of_use_soc_register,
      self.today_battery_charged_energy_register,
      self.today_battery_discharged_energy_register,
      self.today_grid_feed_in_energy_register,
      self.today_grid_purchased_energy_register,
      self.today_gen_energy_register,
      self.today_load_consumption_register,
      self.today_pv_production_register,
      self.today_pv_production_cost_register,
      self.today_grid_purchased_energy_cost_register,
      self.today_grid_feed_in_energy_cost_register,
      self.today_gen_energy_cost_register,
      self.total_battery_charged_energy_register,
      self.total_battery_discharged_energy_register,
      self.total_grid_feed_in_energy_register,
      self.total_grid_purchased_energy_register,
      self.total_gen_energy_register,
      self.total_load_consumption_register,
      self.total_pv_production_register,
      self.total_pv_production_cost_register,
      self.total_grid_purchased_energy_cost_register,
      self.total_grid_feed_in_energy_cost_register,
      self.total_gen_energy_cost_register,
      self.zero_export_power_register,
    ]

  @cached_property
  def all_registers_map(self) -> Dict[str, DeyeRegister]:
    return {reg.name: reg for reg in self.all_registers}

  @cached_property
  def test_registers(self) -> List[DeyeRegister]:
    return [self.test1_register, self.test2_register]

  @cached_property
  def read_only_registers(self) -> List[DeyeRegister]:
    return [register for register in self.all_registers if not register.can_write]

  @cached_property
  def read_write_registers(self) -> List[DeyeRegister]:
    return [register for register in self.all_registers if register.can_write]

  @property
  def prefix(self) -> str:
    return self._prefix
