import enum

class DeyeBaseEnum(enum.Enum):
  def __str__(self):
    return self.name.replace('_', '-')

  @property
  def pretty(self):
    return self.name.replace('_', ' ').title()
