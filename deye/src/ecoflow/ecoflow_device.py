class EcoflowDevice:
  """
  WARNING: Fields in this class are serialized to JSON and stored in environment variables.
  Do not rename or remove fields without updating the corresponding ENV configurations.
  """
  def __init__(
    self,
    name: str,
    serial: str,
    device_type: str,
    max_power: int,
    max_real_power: int,
  ):
    self._name = name
    self._serial = serial
    self._device_type = device_type
    self._max_power = max_power
    self._max_real_power = max_real_power

  @property
  def name(self) -> str:
    return self._name

  @property
  def serial(self) -> str:
    return self._serial

  @property
  def device_type(self) -> str:
    return self._device_type

  @property
  def max_power(self) -> int:
    return self._max_power

  @property
  def max_real_power(self) -> int:
    return self._max_real_power
