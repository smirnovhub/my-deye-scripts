class DeyeLogger:
  def __init__(self, name: str, address: str, serial: int, port: int = 8899):
    self._name = name.lower()
    self._address = address
    self._serial = serial
    self._port = port

  @property
  def name(self) -> str:
    return self._name

  @property
  def address(self) -> str:
    return self._address

  @property
  def serial(self) -> int:
    return self._serial

  @property
  def port(self) -> int:
    return self._port
