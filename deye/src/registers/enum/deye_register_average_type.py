from enum import Enum, auto

class DeyeRegisterAverageType(Enum):
  none = auto()
  # Only master means that the value of the register is read only from the master logger.
  only_master = auto()
  # Accumulate means that the value of the register
  # isthe sum of the values from all loggers.
  accumulate = auto()
  # Fake accumulate means that the value of the register is the
  # value from the master logger multiplied by the number of loggers.
  fake_accumulate = auto()
  # Average means that the value of the register is the average of the values from all loggers.
  average = auto()
  # Special means that the register has a special way of calculating the value.
  # As usual do not make any accumulation or averaging
  special = auto()
