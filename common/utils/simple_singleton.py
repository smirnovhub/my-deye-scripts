import threading

from typing import Dict, Type

def singleton(cls):
  lock = threading.Lock()
  instances: Dict[Type, object] = {}

  def get_instance(*args, **kwargs):
    if cls not in instances:
      # Only one thread can enter this block at a time
      with lock:
        # Double-check inside the lock to be 100% sure
        if cls not in instances:
          instances[cls] = cls(*args, **kwargs)
    return instances[cls]

  return get_instance
