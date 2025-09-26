from deye_base_enum import DeyeBaseEnum

class DeyeSystemWorkMode(DeyeBaseEnum):
  unknown = -1
  selling_first = 0
  zero_export_to_load = 1
  zero_export_to_ct = 2

  @property
  def pretty(self):
    return super().pretty.replace('Ct', 'CT')
