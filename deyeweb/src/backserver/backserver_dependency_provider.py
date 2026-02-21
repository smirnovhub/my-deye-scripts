import threading
import traceback

from typing import Dict, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
  from deye_web_front_content_builder import DeyeWebFrontContentBuilder
  from deye_web_params_processor import DeyeWebParamsProcessor
  from deye_web_constants import DeyeWebConstants
  from deye_web_utils import DeyeWebUtils
  from deye_exceptions import DeyeKnownException

class BackserverDependencyProvider:
  """
  Lazy loader for dependencies that may fail to import at runtime.
  Thread-safe and stores import/initialization errors.
  """
  def __init__(self):
    self._lock = threading.Lock()

    # Front builder
    self._front_builder_instance: Optional[Any] = None
    self._front_builder_error: Optional[str] = None

    # Back params processor
    self._back_params_processor_instance: Optional[Any] = None
    self._back_params_processor_error: Optional[str] = None

    # Constants class
    self._constants_class: Optional[Any] = None
    self._constants_error: Optional[str] = None

    # Utils class
    self._utils_class: Optional[Any] = None
    self._utils_error: Optional[str] = None

    # Known exception class
    self._known_exception_class: Optional[Any] = None
    self._known_exception_error: Optional[str] = None

  @property
  def front_builder(self) -> Optional['DeyeWebFrontContentBuilder']:
    if self._front_builder_instance:
      return self._front_builder_instance

    with self._lock:
      if self._front_builder_instance: # double-checked locking
        return self._front_builder_instance
      try:
        from deye_web_front_content_builder import DeyeWebFrontContentBuilder
        self._front_builder_instance = DeyeWebFrontContentBuilder()
        return self._front_builder_instance
      except Exception as e:
        self._front_builder_error = f"{str(e)}\n{traceback.format_exc()}"
        return None

  @property
  def back_params_processor(self) -> Optional['DeyeWebParamsProcessor']:
    if self._back_params_processor_instance:
      return self._back_params_processor_instance

    with self._lock:
      if self._back_params_processor_instance: # double-checked locking
        return self._back_params_processor_instance
      try:
        from deye_web_params_processor import DeyeWebParamsProcessor
        self._back_params_processor_instance = DeyeWebParamsProcessor()
        return self._back_params_processor_instance
      except Exception as e:
        self._back_params_processor_error = f"{str(e)}\n{traceback.format_exc()}"
        return None

  @property
  def constants(self) -> Optional['DeyeWebConstants']:
    if self._constants_class:
      return self._constants_class

    with self._lock:
      if self._constants_class: # double-checked locking
        return self._constants_class
      try:
        from deye_web_constants import DeyeWebConstants
        self._constants_class = DeyeWebConstants
        return self._constants_class
      except Exception as e:
        self._constants_error = f"{str(e)}\n{traceback.format_exc()}"
        return None

  @property
  def utils(self) -> Optional['DeyeWebUtils']:
    if self._utils_class:
      return self._utils_class

    with self._lock:
      if self._utils_class: # double-checked locking
        return self._utils_class
      try:
        from deye_web_utils import DeyeWebUtils
        self._utils_class = DeyeWebUtils
        return self._utils_class
      except Exception as e:
        self._utils_error = f"{str(e)}\n{traceback.format_exc()}"
        return None

  @property
  def known_exception(self) -> Optional['DeyeKnownException']:
    if self._known_exception_class:
      return self._known_exception_class

    with self._lock:
      if self._known_exception_class: # double-checked locking
        return self._known_exception_class
      try:
        from deye_exceptions import DeyeKnownException
        self._known_exception_class = DeyeKnownException
        return self._known_exception_class
      except Exception as e:
        self._known_exception_error = f"{str(e)}\n{traceback.format_exc()}"
        return None

  def get_all_errors(self) -> Dict[str, Optional[str]]:
    """
    Return a dictionary of all import/initialization errors.
    Keys are dependency names, values are error messages or fallback.
    """
    return {
      "front_builder": self._front_builder_error,
      "params_processor": self._back_params_processor_error,
      "constants": self._constants_error,
      "utils": self._utils_error,
      "known_exception": self._known_exception_error,
    }
