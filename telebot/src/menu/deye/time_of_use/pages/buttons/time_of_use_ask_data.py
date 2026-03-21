from dataclasses import dataclass

@dataclass
class TimeOfUseAskData:
  ask_for_fix_times: bool = False
  ask_for_reset_times: bool = False
