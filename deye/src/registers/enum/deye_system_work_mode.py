import enum

class DeyeSystemWorkMode(enum.Enum):
  unknown = -1
  selling_first = 0
  zero_export_to_load = 1
  zero_export_to_ct = 2

  def __str__(self):
    return self.name.replace("_", "-")

  @property
  def pretty(self):
    return self.name.replace('_', ' ').title().replace('Ct', 'CT')
