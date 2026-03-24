from typing import Dict, Tuple

from dataclasses import dataclass
from battery_settings_page import BatterySettingsPage

@dataclass
class BatterySettingsData:
  values: Dict[BatterySettingsPage, int]

  def get_bounds(self, page_type: BatterySettingsPage) -> Tuple[int, int]:
    # Filter: only pages that exist in our values dictionary, in Enum order
    # This ensures we don't try to access missing keys
    pages = [p for p in BatterySettingsPage if p in self.values]

    if page_type not in pages:
      raise ValueError(f"Page {page_type.name} is not present in values")

    idx = pages.index(page_type)

    def get_min_val() -> int:
      # If there's a previous key in our filtered list, use its value
      if idx > 0:
        return self.values[pages[idx - 1]]
      return 0

    def get_max_val() -> int:
      # If there's a next key in our filtered list, use its value
      if idx < len(pages) - 1:
        return self.values[pages[idx + 1]]
      return 100

    return get_min_val(), get_max_val()
