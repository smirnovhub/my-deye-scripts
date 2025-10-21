from typing import Dict

class DeyeEnergyCost:
  # To add new price just add current total pv production (in kWh)
  # as a key and add a new price for kWh as value
  @property
  def pv_energy_costs(self) -> Dict[int, float]:
    return {
      0: 4.32, # apply price 4.32 from start
      # 200.0: 4.5, # apply price 4.5 after 200 kWh
      # 300.0: 5.7, # apply price 5.7 after 300 kWh
    }

  @property
  def grid_purchased_energy_costs(self) -> Dict[int, float]:
    return {
      0: 4.32, # apply price 4.32 from start
      # 200.0: 4.5, # apply price 4.5 after 200 kWh
      # 300.0: 5.7, # apply price 5.7 after 300 kWh
    }

  @property
  def grid_feed_in_energy_costs(self) -> Dict[int, float]:
    return {
      0: 4.32, # apply price 4.32 from start
      # 200.0: 4.5, # apply price 4.5 after 200 kWh
      # 300.0: 5.7, # apply price 5.7 after 300 kWh
    }

  @property
  def gen_energy_costs(self) -> Dict[int, float]:
    return {
      0: 4.32, # apply price 4.32 from start
      # 200.0: 4.5, # apply price 4.5 after 200 kWh
      # 300.0: 5.7, # apply price 5.7 after 300 kWh
    }

  @property
  def currency_code(self) -> str:
    return 'USD'
