import json

from typing import List

from env_utils import EnvUtils
from ecoflow_device import EcoflowDevice
from simple_singleton import singleton

@singleton
class EcoflowDevices:
  def __init__(self):
    devices: List[EcoflowDevice] = []

    # Iterate to find all configured devices
    for i in range(1, 16):
      device_json = EnvUtils.get_ecoflow_device(i)

      # Stop the loop if the current devices is empty or not set
      if not device_json:
        break

      # Parse string back to dictionary
      device_dict = json.loads(device_json)

      # Append the devices if validation passes
      devices.append(EcoflowDevice(**device_dict))

    self.__devices = devices

  @property
  def devices(self) -> List[EcoflowDevice]:
    return self.__devices.copy()
