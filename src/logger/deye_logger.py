class DeyeLogger:
  def __init__(self, name: str, ip: str, serial: int, port: int = 8899):
    self._name = name
    self._ip = ip
    self._port = port
    self._serial = serial

  @property
  def name(self) -> str:
    return self._name

  @property
  def ip(self) -> str:
    return self._ip

  @property
  def port(self) -> int:
    return self._port

  @property
  def serial(self) -> int:
    return self._serial
