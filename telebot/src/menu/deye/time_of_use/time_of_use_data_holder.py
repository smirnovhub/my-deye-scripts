import copy

from dataclasses import asdict
from time_of_use_data import TimeOfUseData

class TimeOfUseDataHolder:
  def __init__(
    self,
    tou_data: TimeOfUseData,
  ):
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)

  @property
  def tou_data(self) -> TimeOfUseData:
    return self._tou_data

  @property
  def tou_original_data(self) -> TimeOfUseData:
    return self._tou_original_data

  @property
  def is_modified(self) -> bool:
    return asdict(self._tou_data) != asdict(self._tou_original_data)

  def actualize(self, tou_data: TimeOfUseData) -> None:
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)

  def swap(self) -> None:
    self._tou_data = self._tou_original_data
    self._tou_original_data = copy.deepcopy(self._tou_data)
