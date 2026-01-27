from dataclasses import dataclass

from deye_utils import DeyeUtils
from deye_register import DeyeRegister
from deye_web_constants import DeyeWebConstants

@dataclass
class FormattedValue:
  value: str
  unit: str

class DeyeWebValueFormatter:
  @staticmethod
  def get_formatted_value(register: DeyeRegister) -> FormattedValue:
    registers = DeyeWebConstants.registers
    if isinstance(register.value, float):
      value = DeyeWebValueFormatter.get_corrected_value(register)
      if register.name == registers.battery_current_register.name:
        return DeyeWebValueFormatter.get_formatted_current_value(value, register.suffix)
      elif register.suffix == registers.grid_voltage_register.suffix:
        return DeyeWebValueFormatter.get_formatted_voltage_value(value, register.suffix)
      elif register.suffix == registers.today_pv_production_cost_register.suffix:
        return DeyeWebValueFormatter.get_formatted_cost_value(value, register.suffix)
      elif register.suffix == registers.today_pv_production_register.suffix:
        return DeyeWebValueFormatter.get_formatted_energy_value(value, register.suffix)
      return FormattedValue(str(DeyeUtils.custom_round(value)), register.suffix)

    if isinstance(register.value, int):
      val = round(DeyeWebValueFormatter.get_corrected_value(register))
      if register.suffix == registers.load_power_register.suffix:
        return DeyeWebValueFormatter.get_formatted_power_value(val, register.suffix)
      return FormattedValue(str(val), register.suffix)

    return FormattedValue(register.pretty_value, register.suffix)

  @staticmethod
  def get_corrected_value(register: DeyeRegister) -> float:
    if not isinstance(register.value, float) and not isinstance(register.value, int):
      raise ValueError(f"Type of register value '{register.name}' should be float or int")

    for reg, correction in DeyeWebConstants.register_value_corrections.items():
      if reg.name == register.name:
        return register.value + correction

    return register.value

  @staticmethod
  def get_formatted_voltage_value(value: float, suffix: str) -> FormattedValue:
    val = '0' if value < 15 else str(round(value))
    return FormattedValue(value = val, unit = suffix)

  @staticmethod
  def get_formatted_cost_value(value: float, suffix: str) -> FormattedValue:
    val = str(round(value))
    return FormattedValue(value = val, unit = suffix)

  @staticmethod
  def get_formatted_energy_value(value: float, suffix: str) -> FormattedValue:
    if value < 9.5:
      val = DeyeUtils.custom_round(value, 1)
      return FormattedValue(val, suffix)
    elif value < 999.5:
      val = DeyeUtils.custom_round(value, 0)
      return FormattedValue(val, suffix)
    else:
      val = DeyeUtils.custom_round(value / 1000, 2)
      return FormattedValue(val, 'MWh')

  @staticmethod
  def get_formatted_power_value(value: int, suffix: str) -> FormattedValue:
    if abs(value) < 1000:
      return FormattedValue(str(value), suffix)

    val = DeyeUtils.custom_round(value / 1000, 1)
    return FormattedValue(val, 'kW')

  @staticmethod
  def get_formatted_current_value(value: float, suffix: str) -> FormattedValue:
    if abs(value) >= 5:
      return FormattedValue(str(round(value)), suffix)
    return FormattedValue(str(DeyeUtils.custom_round(value)), suffix)
