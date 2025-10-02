import random

from typing import Any, List, Optional

from datetime import datetime, timedelta
from deye_register import DeyeRegister
from int_deye_register import IntDeyeRegister
from signed_int_deye_register import SignedIntDeyeRegister
from deye_base_enum import DeyeBaseEnum
from deye_energy_cost import DeyeEnergyCost
from float_deye_register import FloatDeyeRegister
from signed_float_deye_register import SignedFloatDeyeRegister
from temperature_deye_register import TemperatureDeyeRegister
from long_float_deye_register import LongFloatDeyeRegister
from sum_deye_register import SumDeyeRegister
from long_float_splitted_deye_register import LongFloatSplittedDeyeRegister
from system_time_writable_deye_register import SystemTimeWritableDeyeRegister
from system_time_diff_deye_register import SystemTimeDiffDeyeRegister
from today_energy_cost_base_register import TodayEnergyCostBaseRegister
from total_energy_cost_base_register import TotalEnergyCostBaseRegister
from time_of_use_int_writable_deye_register import TimeOfUseIntWritableDeyeRegister

from deye_utils import (
  to_unsigned,
  custom_round,
  to_inv_time,
  to_long_register_values,
)

class DeyeRegisterRandomValue:
  def __init__(
    self,
    register: DeyeRegister,
    value: Any,
    values: List[int],
  ):
    self.register = register
    self.value = value
    self.values = values

def get_random_by_register_type(
  register: DeyeRegister,
  randoms: List[DeyeRegisterRandomValue] = [],
) -> Optional[DeyeRegisterRandomValue]:
  """
  Generate a random value for a given Deye register, suitable for testing or simulation.

  This function handles various types of Deye registers, including:
    - Enumerations (DeyeBaseEnum)
    - Standard floats (FloatDeyeRegister, SignedFloatDeyeRegister)
    - Long floats (LongFloatDeyeRegister, LongFloatSplittedDeyeRegister)
    - Integers (IntDeyeRegister, SignedIntDeyeRegister)
    - Temperature registers (TemperatureDeyeRegister)
    - System time registers (SystemTimeWritableDeyeRegister)
    - Registers that cannot be written (SystemTimeDiffDeyeRegister returns None)

  The function generates random values within valid ranges for each register type,
  applying scaling factors, register offsets, and value rounding as needed. 

  For example:
    - Float and signed float registers are scaled and rounded according to the register's `scale`.
    - Long float registers are split into two 16-bit registers if needed.
    - System time registers generate a random datetime between 2000-01-01 and the current time,
      returning both a formatted string and the inverter-compatible integer list.

  Args:
      register (DeyeRegister): The register object for which a random value is to be generated.

  Returns:
      Optional[DeyeRegisterRandomValue]:
          - A DeyeRegisterRandomValue object containing:
              * `value`: the generated Python value (int, float, enum, or datetime string)
              * `starting_address`: the register's address in the inverter
              * `values`: a list of integer register values ready to be written
          - None if the register type cannot be written (e.g., SystemTimeDiffDeyeRegister).
  """
  unsigned_max_value = 2**16 - 1
  signed_max_value = 2**15 - 1
  signed_min_value = -signed_max_value
  unsigned_long_max_value = 2**32 - 1

  if isinstance(register.value, DeyeBaseEnum):
    valid_values = [v for v in type(register.value) if v.value >= 0]
    value = random.choice(valid_values)
    return DeyeRegisterRandomValue(register, value, [value.value])
  elif isinstance(register, LongFloatSplittedDeyeRegister):
    # Compute the maximum safe value for 2 registers (32-bit unsigned)
    max_val = unsigned_long_max_value // register.scale

    # Generate a random value within the allowed range
    val = int(random.uniform(0, max_val)) / register.scale

    # Get the two 16-bit registers representing the 32-bit value
    values = to_long_register_values(val, register.scale, register.quantity) # values[0], values[1]

    # Create a list of registers to write
    # The first register is at register.address
    # The second register is at register.address + split_offset
    # Any registers in between are "garbage" and set to 0
    total_registers = register.split_offset + 1 # index of the second register + 1
    regs_to_write = [0] * total_registers
    regs_to_write[0] = values[0] # first data register
    regs_to_write[register.split_offset] = values[1] # second data register at split_offset

    # Round the value for further use
    value = custom_round(val)
    return DeyeRegisterRandomValue(register, value, regs_to_write)
  elif isinstance(register, LongFloatDeyeRegister):
    max_val = unsigned_long_max_value // register.scale
    val = int(random.uniform(0, max_val) * register.scale // register.scale) / register.scale
    values = to_long_register_values(val, register.scale, register.quantity)
    value = custom_round(val)
    return DeyeRegisterRandomValue(register, value, values)
  elif isinstance(register, TemperatureDeyeRegister):
    val = int(random.uniform(0, (unsigned_max_value + register.shift) / register.scale) * register.scale)
    value = custom_round((val + register.shift) / register.scale)
    return DeyeRegisterRandomValue(register, value, [val])
  elif isinstance(register, SignedFloatDeyeRegister):
    val = int(random.uniform(signed_min_value / register.scale, signed_max_value / register.scale) * register.scale)
    value = custom_round(val / register.scale)
    return DeyeRegisterRandomValue(register, value, [to_unsigned(val)])
  elif isinstance(register, FloatDeyeRegister):
    val = int(random.uniform(0, unsigned_max_value / register.scale) * register.scale)
    value = custom_round(val / register.scale)
    return DeyeRegisterRandomValue(register, value, [val])
  elif isinstance(register, SignedIntDeyeRegister):
    value = random.randint(signed_min_value, signed_max_value)
    return DeyeRegisterRandomValue(register, value, [to_unsigned(value)])
  elif isinstance(register, IntDeyeRegister):
    value = random.randint(0, unsigned_max_value)
    return DeyeRegisterRandomValue(register, value, [value])
  elif isinstance(register, TimeOfUseIntWritableDeyeRegister):
    valsss: List[int] = []
    for i in range(register.quantity):
      value = random.randint(0, unsigned_max_value)
      valsss.append(value)
    value = sum(valsss) / len(valsss)
    return DeyeRegisterRandomValue(register, custom_round(value), valsss)
  elif isinstance(register, SystemTimeDiffDeyeRegister):
    return None
  elif isinstance(register, SystemTimeWritableDeyeRegister):
    # Get the current date and time
    now = datetime.now()
    # Define the start date (January 1, 2000)
    start = datetime(2000, 1, 1)

    # Compute total seconds between start and now
    delta_seconds = int((now - start).total_seconds())
    # Pick a random number of seconds within this range
    random_seconds = random.randint(0, delta_seconds)

    # Generate a random datetime by adding the random seconds to the start date
    random_dt = start + timedelta(seconds = random_seconds)

    # Convert datetime to a list of integers [year, month, day, hour, minute, second]
    # Year is offset by 2000 to match your `to_inv_time` format
    as_ints = [
      random_dt.year - 2000,
      random_dt.month,
      random_dt.day,
      random_dt.hour,
      random_dt.minute,
      random_dt.second,
    ]

    # Call your function to convert these integers into inverter-compatible values
    values = to_inv_time(as_ints)

    # Format datetime as a string
    datetime_str = random_dt.strftime("%Y-%m-%d %H:%M:%S")

    return DeyeRegisterRandomValue(register, datetime_str, values)
  elif isinstance(register, TotalEnergyCostBaseRegister):
    energy_cost = DeyeEnergyCost()
    for rnd in randoms:
      if rnd.register.name == register.production_register.name:
        total_cost = 0
        production = float(rnd.value)

        for prod, cost in reversed(list(energy_cost.pv_energy_costs.items())):
          delta = production - prod
          total_cost += delta * cost
          production -= delta

        return DeyeRegisterRandomValue(register, custom_round(total_cost), rnd.values)
  elif isinstance(register, TodayEnergyCostBaseRegister):
    energy_cost = DeyeEnergyCost()
    for rnd in randoms:
      if rnd.register.name == register.production_register.name:
        production = float(rnd.value)
        val = production * energy_cost.current_pv_energy_cost
        return DeyeRegisterRandomValue(register, custom_round(val), rnd.values)
  elif isinstance(register, SumDeyeRegister):
    vals: List[float] = []
    for rnd in randoms:
      for reg in register.registers:
        if rnd.register.name == reg.name:
          vals.append(float(rnd.value))
    return DeyeRegisterRandomValue(register, custom_round(sum(vals)), [])

  return None

def get_random_by_register_value_type(register: DeyeRegister) -> Any:
  if isinstance(register.value, int):
    return round(random.uniform(register.min_value, register.max_value))
  elif isinstance(register.value, float):
    return round(random.uniform(register.min_value, register.max_value), 2)
  elif isinstance(register.value, datetime):
    start = datetime(2000, 1, 1)
    end = datetime.now()
    random_date = start + timedelta(seconds = random.randint(0, int((end - start).total_seconds())))
    return random_date.strftime("%Y-%m-%d %H:%M:%S")
  elif isinstance(register.value, DeyeBaseEnum):
    valid_values = [v for v in type(register.value) if v.value >= 0]
    return random.choice(valid_values)

  return None
