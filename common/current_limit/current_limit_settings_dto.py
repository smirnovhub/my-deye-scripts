from datetime import date
from dataclasses import dataclass

from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class CurrentLimitSettingsDto(DataClassJSONMixin):
  """
  Data transfer object representing dynamically changing current limit data
  """
  last_max_charge_current: int = 0
  last_full_charge_date: date = date.min
  last_full_charge_notification_date: date = date.min
