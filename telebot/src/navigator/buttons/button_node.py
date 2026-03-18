import secrets

from button_style import ButtonStyle

class ButtonNode:
  def __init__(
    self,
    text: str,
    data: str = "",
    style = ButtonStyle.default,
  ):
    self._text = text
    self._data = data
    self._style = style
    self._id = secrets.randbits(32)

  @property
  def text(self) -> str:
    return self._text

  @property
  def data(self) -> str:
    return self._data

  @property
  def style(self) -> ButtonStyle:
    return self._style

  @property
  def id(self) -> int:
    return self._id
