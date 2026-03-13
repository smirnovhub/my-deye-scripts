import threading

class ButtonNode:
  _counter: int = 100
  _lock = threading.Lock()

  def __init__(
    self,
    text: str,
    data: str = "",
  ):
    ButtonNode._counter += 1
    self._text: str = text

    if not data:
      with ButtonNode._lock:
        ButtonNode._counter += 1
        self._data = str(ButtonNode._counter)
    else:
      self._data = data

  @property
  def text(self) -> str:
    return self._text

  @property
  def data(self) -> str:
    return self._data

  def set_text(self, text: str) -> None:
    self._text = text
