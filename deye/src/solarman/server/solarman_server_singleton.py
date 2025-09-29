from typing import Type, Any, Dict

class Singleton(type):
  _instances: Dict[Type[Any], Any] = {}

  def __call__(cls, *args, **kwargs):
    if cls not in cls._instances:
      cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    return cls._instances[cls]
