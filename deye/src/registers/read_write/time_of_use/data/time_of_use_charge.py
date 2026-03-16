from dataclasses import dataclass

@dataclass
class TimeOfUseCharge:
  """
  Represents a grid and gen charge flags.

  Attributes:
      grid_charge (bool): True if grid charge enabled.
      gen_charge (bool): True if gen charge enabled.
      bit2 (bool): Unknown bit from inverter
  """
  grid_charge: bool
  gen_charge: bool
  # Some unknown 3rd bit from inverter.
  # In my inverter it has 1.
  # All other unused bits have 0.
  # Maybe will be supported in new firmware.
  # Do not change it!
  bit2: bool
  bit3: bool
  bit4: bool
  bit5: bool
  bit6: bool
  bit7: bool
