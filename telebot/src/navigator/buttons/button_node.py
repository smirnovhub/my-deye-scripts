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

    # Generate a stable ID based on text, data, style and key to persist across page updates
    raw_id = f"{text}:{data}:{style}:{key}".encode("utf-8")
    self._id = hashlib.md5(raw_id).hexdigest()[:10]

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
