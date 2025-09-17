import enum

class DeyeSystemType(enum.Enum):
  none = -1
  any = 1
  single_inverter = 2
  multi_inverter = 3

  def __str__(self):
    return self.name.replace('_', '-')

  @property
  def pretty(self):
    return self.name.replace('_', ' ').title()
