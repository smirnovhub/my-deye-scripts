import hashlib

from button_style import ButtonStyle

class ButtonNode:
  def __init__(
    self,
    text: str,
    data: str = "",
    key: str = "",
    style = ButtonStyle.default,
  ):
    self._text = text
    self._data = data
    self._style = style
    self._key = key
    self._id = self._get_id()

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
  def key(self) -> str:
    return self._key

  @property
  def id(self) -> str:
    return self._id

  def set_key(self, key: str) -> None:
    self._key = key
    self._id = self._get_id()

  def _get_id(self) -> str:
    # Generate a stable ID based on text, data, style and key to persist across page updates
    raw_id = f"{self._text}:{self._data}:{self._style}:{self._key}".encode("utf-8")
    return hashlib.md5(raw_id).hexdigest()[:10]
