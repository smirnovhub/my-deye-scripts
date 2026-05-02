from typing import List

from datetime import timedelta
from functools import cached_property

from deye_base_registers import DeyeBaseRegisters
from deye_energy_cost import DeyeEnergyCost
from deye_register_group import DeyeRegisterGroup
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
    self._energy_cost = DeyeEnergyCost()

  @cached_property
  def ac_couple_frz_high_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      address = 329,
      min_value = 50.5,
      max_value = 52,
      description = 'AC Couple Frz High',
      suffix = 'Hz',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.only_master,
    ).with_scale(100)

  @cached_property
  def backup_delay_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 311,
      min_value = 0,
      max_value = 30000,
      description = 'Backup Delay',
      suffix = 'ms',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_bms_charge_current_limit_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 314,
      description = 'Battery BMS Charge Current Limit',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_bms_discharge_current_limit_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 315,
      description = 'Battery BMS Discharge Current Limit',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_capacity_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 107,
      description = 'Battery Capacity',
      suffix = 'Ah',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
      caching_time = timedelta(hours = 12),
    )

  @cached_property
  def battery_current_register(self) -> DeyeRegister:
    return SignedFloatDeyeRegister(
      address = 191,
      description = 'Battery Current',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.accumulate,
    ).with_scale(100)

  @cached_property
  def battery_gen_charge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 227,
      min_value = 0,
      max_value = 80,
      description = 'Battery Gen Charge Current',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_grid_charge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 230,
      min_value = 0,
      max_value = 80,
      description = 'Battery Grid Charge Current',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_low_batt_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 219,
      min_value = 0,
      max_value = 100,
      description = 'Battery Low Batt SOC',
      suffix = '%',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_max_charge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 210,
      min_value = 0,
      max_value = 80,
      description = 'Battery Max Charge Current',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_max_discharge_current_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 211,
      min_value = 50,
      max_value = 120,
      description = 'Battery Max Discharge Current',
      suffix = 'A',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def battery_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      address = 190,
      description = 'Battery Power',
      suffix = 'W',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def battery_restart_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 218,
      min_value = 0,
      max_value = 100,
      description = 'Battery Restart SOC',
      suffix = '%',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_soc_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 184,
      description = 'Battery SOC',
      suffix = '%',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_soh_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 197,
      description = 'Battery SOH',
      suffix = '%',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
      caching_time = timedelta(hours = 12),
    )

  @cached_property
  def battery_shutdown_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 217,
      min_value = 0,
      max_value = 100,
      description = 'Battery Shutdown SOC',
      suffix = '%',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      address = 182,
      description = 'Battery Temperature',
      suffix = 'deg',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def battery_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 183,
      description = 'Battery Voltage',
      suffix = 'V',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def ct_ratio_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 327,
      min_value = 200,
      max_value = 2000,
      description = 'CT Ratio',
      suffix = '',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def gen_peak_shaving_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 292,
      min_value = 500,
      max_value = 6000,
      description = 'Gen Peak Shaving Power',
      suffix = 'W',
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def gen_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      address = 166,
      description = 'Gen Power',
      suffix = 'W',
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_charging_start_soc_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 229,
      min_value = 50,
      max_value = 90,
      description = 'Grid Charging Start SOC',
      suffix = '%',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_connect_voltage_high_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      address = 287,
      min_value = 231,
      max_value = 255,
      description = 'Grid Connect Voltage High',
      suffix = 'V',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_connect_voltage_low_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      address = 288,
      min_value = 195,
      max_value = 230,
      description = 'Grid Connect Voltage Low',
      suffix = 'V',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_reconnect_voltage_high_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      address = 433,
      min_value = 231,
      max_value = 255,
      description = 'Grid Reconnect Voltage High',
      suffix = 'V',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_reconnect_voltage_low_register(self) -> DeyeRegister:
    return FloatWritableDeyeRegister(
      address = 434,
      min_value = 195,
      max_value = 230,
      description = 'Grid Reconnect Voltage Low',
      suffix = 'V',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_frequency_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 79,
      description = 'Grid Frequency',
      suffix = 'Hz',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def grid_peak_shaving_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 293,
      min_value = 1000,
      max_value = 6000,
      description = 'Grid Peak Shaving Power',
      suffix = 'W',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      address = 169,
      description = 'Grid Power',
      suffix = 'W',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_internal_ct_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      address = 167,
      description = 'Grid Internal CT Power',
      suffix = 'W',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_external_ct_power_register(self) -> DeyeRegister:
    return SignedIntDeyeRegister(
      address = 170,
      description = 'Grid External CT Power',
      suffix = 'W',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def grid_reconnection_time_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 282,
      min_value = 60,
      max_value = 3600,
      description = 'Grid Reconnection Time',
      suffix = 'sec',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def grid_state_code_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 194,
      description = 'Grid State code',
      suffix = '',
      group = DeyeRegisterGroup.grid,
    )

  @cached_property
  def grid_state_register(self) -> DeyeRegister:
    return GridStateDeyeRegister(
      address = 194,
      description = 'Grid State',
      suffix = '',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def grid_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 150,
      description = 'Grid Voltage',
      suffix = 'V',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def gen_port_mode_register(self) -> DeyeRegister:
    return GenPortModeWritableDeyeRegister(
      address = 235,
      description = 'Gen Port Mode',
      suffix = '',
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def inverter_ac_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      address = 91,
      description = 'Inverter AC Temperature',
      suffix = 'deg',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_dc_temperature_register(self) -> DeyeRegister:
    return TemperatureDeyeRegister(
      address = 90,
      description = 'Inverter DC Temperature',
      suffix = 'deg',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_system_time_diff_register(self) -> DeyeRegister:
    return SystemTimeDiffDeyeRegister(
      system_time_register = self.inverter_system_time_register,
      description = 'Inverter System Time Diff',
      suffix = 'sec',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def inverter_system_time_register(self) -> DeyeRegister:
    return SystemTimeWritableDeyeRegister(
      address = 22,
      description = 'Inverter System Time',
      suffix = '',
      group = DeyeRegisterGroup.inverter,
      caching_time = timedelta(seconds = 50),
    )

  @cached_property
  def load_frequency_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 192,
      description = 'Load Frequency',
      suffix = 'Hz',
      group = DeyeRegisterGroup.load,
      avg = DeyeRegisterAverageType.average,
    ).with_scale(100)

  @cached_property
  def load_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 178,
      description = 'Load Power',
      suffix = 'W',
      group = DeyeRegisterGroup.load,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def load_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 157,
      description = 'Load Voltage',
      suffix = 'V',
      group = DeyeRegisterGroup.load,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv1_current_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 110,
      description = 'PV1 current',
      suffix = 'A',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv1_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 186,
      description = 'PV1 Power',
      suffix = 'W',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv1_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 109,
      description = 'PV1 voltage',
      suffix = 'V',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv2_current_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 112,
      description = 'PV2 current',
      suffix = 'A',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv2_power_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 187,
      description = 'PV2 Power',
      suffix = 'W',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.accumulate,
    )

  @cached_property
  def pv2_voltage_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 111,
      description = 'PV2 voltage',
      suffix = 'V',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.average,
    )

  @cached_property
  def pv_total_current_register(self) -> DeyeRegister:
    return SumDeyeRegister(
      registers = [
        self.pv1_current_register,
        self.pv2_current_register,
      ],
      description = 'PV Total current',
      suffix = 'A',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def pv_total_power_register(self) -> DeyeRegister:
    return SumDeyeRegister(
      registers = [
        self.pv1_power_register,
        self.pv2_power_register,
      ],
      description = 'PV Total Power',
      suffix = 'W',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def system_work_mode_register(self) -> DeyeRegister:
    return SystemWorkModeWritableDeyeRegister(
      address = 244,
      description = 'System Work Mode',
      suffix = '',
      group = DeyeRegisterGroup.inverter,
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
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def time_of_use_power_register(self) -> DeyeRegister:
    return TimeOfUseIntWritableDeyeRegister(
      address = 256,
      min_value = 0,
      max_value = 6000,
      description = 'Time Of Use Power',
      suffix = 'W',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.fake_accumulate,
    )

  @cached_property
  def time_of_use_soc_register(self) -> DeyeRegister:
    return TimeOfUseIntWritableDeyeRegister(
      address = 268,
      min_value = 15,
      max_value = 100,
      description = 'Time Of Use SOC',
      suffix = '%',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def today_battery_charged_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 70,
      description = 'Today Battery Charged Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_battery_discharged_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 71,
      description = 'Today Battery Discharged Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_grid_feed_in_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 77,
      description = 'Today Grid Feed-in Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_grid_purchased_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 76,
      description = 'Today Grid Purchased Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_gen_energy_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 62,
      description = 'Today Gen Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_load_consumption_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 84,
      description = 'Today Load Consumption',
      suffix = 'kWh',
      group = DeyeRegisterGroup.load,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_pv_production_register(self) -> DeyeRegister:
    return FloatDeyeRegister(
      address = 108,
      description = 'Today PV Production',
      suffix = 'kWh',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 5),
    )

  @cached_property
  def today_pv_production_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      energy_register = self.today_pv_production_register,
      energy_costs = self._energy_cost.pv_energy_costs,
      description = 'Today PV Production Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      energy_register = self.today_grid_purchased_energy_register,
      energy_costs = self._energy_cost.grid_purchased_energy_costs,
      description = 'Today Grid Purchased Energy Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      energy_register = self.today_grid_feed_in_energy_register,
      energy_costs = self._energy_cost.grid_feed_in_energy_costs,
      description = 'Today Grid Feed-in Energy Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def today_gen_energy_cost_register(self) -> DeyeRegister:
    return TodayEnergyCostRegister(
      energy_register = self.today_gen_energy_register,
      energy_costs = self._energy_cost.gen_energy_costs,
      description = 'Today Gen Energy Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_battery_charged_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      address = 72,
      description = 'Total Battery Charged Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_battery_discharged_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      address = 74,
      description = 'Total Battery Discharged Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.battery,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_grid_feed_in_energy_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      address = 81,
      description = 'Total Grid Feed-in Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_grid_purchased_energy_register(self) -> DeyeRegister:
    return LongFloatSplittedDeyeRegister(
      address = 78,
      split_offset = 2,
      description = 'Total Grid Purchased Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_gen_energy_register(self) -> DeyeRegister:
    return LongFloatSplittedDeyeRegister(
      address = 92,
      split_offset = 3,
      description = 'Total Gen Energy',
      suffix = 'kWh',
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_load_consumption_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      address = 85,
      description = 'Total Load Consumption',
      suffix = 'kWh',
      group = DeyeRegisterGroup.load,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_pv_production_register(self) -> DeyeRegister:
    return LongFloatDeyeRegister(
      address = 96,
      description = 'Total PV Production',
      suffix = 'kWh',
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.accumulate,
      caching_time = timedelta(minutes = 15),
    )

  @cached_property
  def total_pv_production_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      energy_register = self.total_pv_production_register,
      energy_costs = self._energy_cost.pv_energy_costs,
      description = 'Total PV Production Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.pv,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_grid_purchased_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      energy_register = self.total_grid_purchased_energy_register,
      energy_costs = self._energy_cost.grid_purchased_energy_costs,
      description = 'Total Grid Purchased Energy Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_grid_feed_in_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      energy_register = self.total_grid_feed_in_energy_register,
      energy_costs = self._energy_cost.grid_feed_in_energy_costs,
      description = 'Total Grid Feed-in Energy Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.grid,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def total_gen_energy_cost_register(self) -> DeyeRegister:
    return TotalEnergyCostRegister(
      energy_register = self.total_gen_energy_register,
      energy_costs = self._energy_cost.gen_energy_costs,
      description = 'Total Gen Energy Cost',
      suffix = DeyeEnergyCost().currency_code,
      group = DeyeRegisterGroup.gen,
      avg = DeyeRegisterAverageType.special,
    )

  @cached_property
  def zero_export_power_register(self) -> DeyeRegister:
    return IntWritableDeyeRegister(
      address = 206,
      min_value = 0,
      max_value = 100,
      description = 'Zero Export Power',
      suffix = 'W',
      group = DeyeRegisterGroup.inverter,
      avg = DeyeRegisterAverageType.only_master,
    )

  @cached_property
  def test1_register(self) -> DeyeRegister:
    return IntDeyeRegister(
      address = 316,
      description = 'Test1',
      suffix = '',
      group = DeyeRegisterGroup.test,
      caching_time = timedelta(seconds = 0),
    )

  @cached_property
  def test2_register(self) -> DeyeRegister:
    return TestDeyeRegister(
      address = 50,
      quantity = 350,
      description = 'Test2',
      suffix = '',
      group = DeyeRegisterGroup.test,
      caching_time = timedelta(seconds = 0),
    )

  @cached_property
  def test_registers(self) -> List[DeyeRegister]:
    return [self.test1_register, self.test2_register]
