from typing import List

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
      'Backup Delay',
      'ms',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_bms_charge_current_limit_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      314,
      'Battery BMS Charge Current Limit',
      'A',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_bms_discharge_current_limit_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      315,
      'Battery BMS Discharge Current Limit',
      'A',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_capacity_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      107,
      'Battery Capacity',
      'Ah',
      avg = DeyeRegisterAverageType.only_master,
      caching_time = timedelta(hours = 12),
    )

  @cached_property
  def battery_current_register(self) -> DeyeRegister:
    return SignedFloatDeyeRegister(
      191,
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
      'Battery Max Discharge Current',
      'A',
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      190,
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
      'Battery Restart SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_soc_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      184,
      'Battery SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_soh_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      10006,
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
      'Battery Shutdown SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      182,
      'Battery Temperature',
      'deg',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      183,
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
      'Gen Peak Shaving Power',
      'W',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def gen_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      166,
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
      'Grid Reconnect Voltage Low',
      'V',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_frequency_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      79,
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
      'Grid Peak Shaving Power',
      'W',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      169,
      'Grid Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_internal_ct_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      167,
      'Grid Internal CT Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_external_ct_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      170,
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
      'Grid Reconnection Time',
      'sec',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_state_code_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      194,
      'Grid State code',
      '',
    )

  @cached_property
  def grid_state_register(self) -> DeyeRegister:
    return GridStateDeyeRegister(
      194,
      'Grid State',
      '',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def grid_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      150,
      'Grid Voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def gen_port_mode_register(self) -> DeyeRegister:
    return GenPortModeWritableDeyeRegister(
      235,
      'Gen Port Mode',
      '',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def inverter_ac_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      91,
      'Inverter AC Temperature',
      'deg',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_dc_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      90,
      'Inverter DC Temperature',
      'deg',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_system_time_diff_register(self) -> DeyeRegister:
    return SystemTimeDiffDeyeRegister(
      self.inverter_system_time_register,
      'Inverter System Time Diff',
      'sec',
      DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_system_time_register(self) -> DeyeRegister:
    return SystemTimeWritableDeyeRegister(
      22,
      'Inverter System Time',
      '',
      caching_time = timedelta(seconds = 50),
    )

  @cached_property
  def load_frequency_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      192,
      'Load Frequency',
      'Hz',
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def load_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      178,
      'Load Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def load_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      157,
      'Load Voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv1_current_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      110,
      'PV1 current',
      'A',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv1_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      186,
      'PV1 Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv1_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      109,
      'PV1 voltage',
      'V',
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv2_current_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      112,
      'PV2 current',
      'A',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv2_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      187,
      'PV2 Power',
      'W',
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv2_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      111,
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
      'PV Total Power',
      'W',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def system_work_mode_register(self) -> DeyeRegister:
    return SystemWorkModeWritableDeyeRegister(
      244,
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
      'Time Of Use SOC',
      '%',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def today_battery_charged_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      70,
      'Today Battery Charged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_battery_discharged_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      71,
      'Today Battery Discharged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_grid_feed_in_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      77,
      'Today Grid Feed-in Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_grid_purchased_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      76,
      'Today Grid Purchased Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_gen_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      62,
      'Today Gen Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_load_consumption_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      84,
      'Today Load Consumption',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_pv_production_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      108,
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
      'Today PV Production Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_grid_purchased_energy_register,
      self._energy_cost.grid_purchased_energy_costs,
      'Today Grid Purchased Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_grid_feed_in_energy_register,
      self._energy_cost.grid_feed_in_energy_costs,
      'Today Grid Feed-in Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_gen_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      self.today_gen_energy_register,
      self._energy_cost.gen_energy_costs,
      'Today Gen Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_battery_charged_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      72,
      'Total Battery Charged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_battery_discharged_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      74,
      'Total Battery Discharged Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_grid_feed_in_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      81,
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
      'Total Gen Energy',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_load_consumption_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      85,
      'Total Load Consumption',
      'kWh',
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_pv_production_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      96,
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
      'Total PV Production Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_grid_purchased_energy_register,
      self._energy_cost.grid_purchased_energy_costs,
      'Total Grid Purchased Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_grid_feed_in_energy_register,
      self._energy_cost.grid_feed_in_energy_costs,
      'Total Grid Feed-in Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_gen_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      self.total_gen_energy_register,
      self._energy_cost.gen_energy_costs,
      'Total Gen Energy Cost',
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def zero_export_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      206,
      0,
      100,
      'Zero Export Power',
      'W',
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def test1_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      316,
      'Test1',
      '',
    )

  @cached_property
  def test2_register(self) -> DeyeRegister:
    return TestDeyeRegister(
      50,
      350,
      'Test2',
      '',
    )

  @cached_property
  def test_registers(self) -> List[DeyeRegister]:
    return [self.test1_register, self.test2_register]
