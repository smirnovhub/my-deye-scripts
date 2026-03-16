import secrets

class ButtonNode:
  def __init__(
    self,
    text: str,
    data: str = "",
  ):
    self._text: str = text
    self._data: str = data
    self._id = secrets.randbits(32)

  @property
  def text(self) -> str:
    return self._text

  @property
  def data(self) -> str:
    return self._data

  @property
  def id(self) -> int:
    return self._id
