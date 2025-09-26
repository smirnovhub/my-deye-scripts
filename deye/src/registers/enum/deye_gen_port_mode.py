from deye_base_enum import DeyeBaseEnum

class DeyeGenPortMode(DeyeBaseEnum):
  unknown = -1
  generator_input = 0
  smartload_output = 1
  microinverter_input = 2
