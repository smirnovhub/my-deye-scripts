import enum

class DeyeGenPortMode(enum.Enum):
  unknown = -1
  generator_input = 0
  smartload_output = 1
  microinverter_input = 2

  def __str__(self):
    return self.name.replace('_', '-')

  @property
  def pretty(self):
    return self.name.replace('_', ' ').title()
