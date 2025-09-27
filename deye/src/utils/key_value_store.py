import json

from deye_file_with_lock import DeyeFileWithLock
from deye_utils import ensure_file_exists

class KeyValueStore:
  """
  A simple thread-safe JSON-backed key-value store.

  This class allows storing and retrieving Python objects by key,
  persisting them in a JSON file. File access is synchronized using
  a file lock to prevent race conditions when multiple threads or
  processes access the same file.

  Methods:
      set(key, value): Store a value under the given key.
      get(key): Retrieve the value for the given key, or return
                the default value if the key does not exist.

  Parameters:
      filename (str): Path to the JSON file used for storage.
      default (Any, optional): Default value returned by get() if
                                the key is missing. Defaults to None.
  """
  def __init__(self, filename: str, default = None):
    self._default = default
    self._filename = filename
    self._locker = DeyeFileWithLock()

    ensure_file_exists(filename)

  def set(self, key: str, value):
    """
    Store a value under the given key in the JSON file.

    This method reads the existing JSON data, updates the key
    with the new value, and writes the data back to the file.
    All file operations are protected by a file lock.

    Args:
        key (str): The key under which to store the value.
        value (Any): The Python object to store.
    """
    try:
      f = self._locker.open_file(self._filename, "a+")
      if f is None:
        return
      f.seek(0)
      try:
        data = json.load(f)
      except json.JSONDecodeError:
        data = {}
      data[key] = value
      f.seek(0)
      f.truncate(0)
      json.dump(data, f, ensure_ascii = False, indent = 2)
      f.flush()
    finally:
      self._locker.close_file()

  def get(self, key: str):
    """
    Retrieve the value associated with the given key.

    Reads the JSON file under a file lock. If the key does not exist,
    returns the default value specified at initialization.

    Args:
        key (str): The key to look up.

    Returns:
        Any: The value associated with the key, or the default value
              if the key is missing.
    """
    try:
      f = self._locker.open_file(self._filename, "r")
      if f is None:
        return None
      try:
        data = json.load(f)
      except json.JSONDecodeError:
        data = {}
      return data.get(key, self._default)
    finally:
      self._locker.close_file()
