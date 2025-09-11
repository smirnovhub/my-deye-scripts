class DeyeEnergyCost:
  # to add new price just add current total pv production (in kWh)
  # as key and new price (in UAH) as value
  @property
  def energy_costs(self):
    return {
      0: 4.32, # apply price 4.32 from start
#      200.0: 4.5, # apply price 4.5 after 200 kWh
#      300.0: 5.7, # apply price 5.7 after 300 kWh
    }

  @property
  def current_cost(self):
    return list(self.energy_costs.values())[-1]
