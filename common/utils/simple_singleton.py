from typing import Dict, Type

def singleton(cls):
  instances: Dict[Type, object] = {}

  def get_instance(*args, **kwargs):
    if cls not in instances:
      instances[cls] = cls(*args, **kwargs)
    return instances[cls]

  return get_instance
