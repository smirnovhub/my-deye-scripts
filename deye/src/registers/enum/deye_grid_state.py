from deye_base_enum import DeyeBaseEnum

class DeyeGridState(DeyeBaseEnum):
  unknown = -1
  off_grid = 0
  on_grid = 1

  @property
  def pretty(self):
    return self.name.replace('_', '-').title()
