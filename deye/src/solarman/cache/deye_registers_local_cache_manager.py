import os

from typing import IO, Any, Optional
from contextlib import contextmanager

from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock
from deye_registers_base_cache_manager import DeyeRegistersBaseCacheManager
from lock_exceptions import DeyeLockNotHeldException

# -----------------------------------------------------
# Class for caching register data locally in JSON files
# -----------------------------------------------------
class DeyeRegistersLocalCacheManager(DeyeRegistersBaseCacheManager):
  def __init__(
    self,
    name: str,
    serial: int,
    verbose = False,
  ):
    super().__init__(
      name = name,
      serial = serial,
      verbose = verbose,
    )

    cache_path = DeyeFileLock.lock_path
    self._cache_filename = os.path.join(cache_path, f"registers-cache-{self._name}-{self._serial}.json")
    self._active_file: Optional[IO[Any]] = None

    # Ensure cache directory exists
    DeyeUtils.ensure_dir_exists(cache_path, mode = 0o777)
    # Ensure cache file exists
    DeyeUtils.ensure_file_exists(self._cache_filename, mode = 0o666)

    if self._verbose:
      print(f"{self._name} {self.__class__.__name__} initialized")
      print(f"Local cache file name: {self._cache_filename}")

  @contextmanager
  def _shared_lock_context(self):
    with self._lock_internal("r", DeyeFileLock.LOCK_SH):
      yield

  @contextmanager
  def _exclusive_lock_context(self):
    with self._lock_internal("a+", DeyeFileLock.LOCK_EX):
      yield

  @contextmanager
  def _lock_internal(self, mode: str, lock_type: int):
    with open(self._cache_filename, mode, encoding = "utf-8") as f:
      try:
        DeyeFileLock.flock(f, lock_type)
        self._active_file = f
        yield
      finally:
        self._active_file = None
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

  def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    f = self._active_file
    if not f:
      raise DeyeLockNotHeldException(f"{type(self).__name__}: "
                                     "read_json() must be called within a lock context")

    f.seek(0)
    return f.read()

  def _read_json(self) -> str:
    """
    Used specifically for the read-before-write cycle.
    Fetches existing data to merge with new updates. Can be overridden to return 
    an empty string if the storage backend (e.g., a smart server) handles merging automatically.
    In this case _get_json() and _read_json() have the same implementation because local file storage requires read-modify-write cycle.
    """
    return self._get_json()

  def _save_json(self, json_string: str) -> None:
    f = self._active_file
    if not f:
      raise DeyeLockNotHeldException(f"{type(self).__name__}: "
                                     "save_json() must be called within a lock context")

    # Clear file and save updated structure
    f.seek(0)
    f.truncate(0)

    # Write the new JSON string to the file
    f.write(json_string)

    # Flush to physical storage
    f.flush()

  def _reset(self) -> None:
    f = self._active_file
    if not f:
      raise DeyeLockNotHeldException(f"{type(self).__name__}: "
                                     "save_json() must be called within a lock context")
    # Clear file
    f.seek(0)
    f.truncate(0)

    # Flush to physical storage
    f.flush()

  def _is_cache_available(self) -> bool:
    """
    Check if the cache is available.

    This method verifies whether the cache is currently available for use.

    Returns:
      bool: True if cache is available for use or False if not available
    """
    return True
