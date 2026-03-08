import json

from typing import Dict

from env_utils import EnvUtils
from simple_singleton import singleton

@singleton
class DeyeEnergyCost:
  # To add new price just add current total pv production (in kWh)
  # as a key and add a new price for kWh as value
  @property
  def pv_energy_costs(self) -> Dict[int, float]:
    # JSON example:
    # {
    #   "0": 4.32, # apply price 4.32 from start
    #   "200": 4.5, # apply price 4.5 after 200 kWh
    #   "300": 5.7 # apply price 5.7 after 300 kWh
    # }
    costs_json = EnvUtils.get_deye_pv_energy_costs_json()
    costs = json.loads(costs_json)
    return {int(k): float(v) for k, v in costs.items()}

  @property
  def grid_purchased_energy_costs(self) -> Dict[int, float]:
    # JSON example:
    # {
    #   "0": 4.32, # apply price 4.32 from start
    #   "200": 4.5, # apply price 4.5 after 200 kWh
    #   "300": 5.7 # apply price 5.7 after 300 kWh
    # }
    costs_json = EnvUtils.get_deye_grid_purchased_energy_costs_json()
    costs = json.loads(costs_json)
    return {int(k): float(v) for k, v in costs.items()}

  @property
  def grid_feed_in_energy_costs(self) -> Dict[int, float]:
    # JSON example:
    # {
    #   "0": 4.32, # apply price 4.32 from start
    #   "200": 4.5, # apply price 4.5 after 200 kWh
    #   "300": 5.7 # apply price 5.7 after 300 kWh
    # }
    costs_json = EnvUtils.get_deye_grid_feed_in_energy_costs_json()
    costs = json.loads(costs_json)
    return {int(k): float(v) for k, v in costs.items()}

  @property
  def gen_energy_costs(self) -> Dict[int, float]:
    # JSON example:
    # {
    #   "0": 4.32, # apply price 4.32 from start
    #   "200": 4.5, # apply price 4.5 after 200 kWh
    #   "300": 5.7 # apply price 5.7 after 300 kWh
    # }
    costs_json = EnvUtils.get_deye_gen_energy_costs_json()
    costs = json.loads(costs_json)
    return {int(k): float(v) for k, v in costs.items()}

  @property
  def currency_code(self) -> str:
    # As example: USD or something else
    return EnvUtils.get_deye_energy_cost_currency_code()
