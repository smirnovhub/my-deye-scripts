import enum

class DeyeGridState(enum.Enum):
  unknown = -1
  off_grid = 0
  on_grid = 1

  def __str__(self):
    return self.name.replace('_', '-')

  @property
  def pretty(self):
    return self.name.replace('_', '-').title()
