import gc
import re
import zlib
import random
import inspect

from typing import Any, List
from collections import Counter

from deye_web_constants import DeyeWebConstants

class DeyeWebUtils:
  _id_stack: List[int] = []

  @staticmethod
  def _generate_id() -> int:
    """Generate a unique 7-digit integer."""
    return random.randint(1_000_000, 9_999_999)

  @staticmethod
  def get_comment(obj: Any, method: str, text: str) -> str:
    if not DeyeWebConstants.add_html_comments:
      return ''

    class_name = f'{obj.__class__.__name__}' if obj is not None else 'Unknown'
    return f'<!-- {text} {class_name}: {method} -->'

  @staticmethod
  def begin_comment(obj: Any) -> str:
    if not DeyeWebConstants.add_html_comments:
      return ''

    # Should be called from here and can't be nested!
    method = 'Unknown'
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
      method = frame.f_back.f_code.co_name

    id = DeyeWebUtils._generate_id()
    DeyeWebUtils._id_stack.append(id)
    return DeyeWebUtils.get_comment(obj, method, f'{id} BEGIN')

  @staticmethod
  def end_comment(obj: Any) -> str:
    if not DeyeWebConstants.add_html_comments:
      return ''

    # Should be called from here and can't be nested!
    method = 'Unknown'
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
      method = frame.f_back.f_code.co_name

    if not DeyeWebUtils._id_stack:
      raise RuntimeError("No matching BEGIN for END")

    id = DeyeWebUtils._id_stack.pop()
    return DeyeWebUtils.get_comment(obj, method, f'{id} END')

  @staticmethod
  def short(string: str) -> str:
    if DeyeWebConstants.user_short_html_ids:
      return DeyeWebUtils.get_shortened_string(string)
    return string

  @staticmethod
  def clean(string: str) -> str:
    if DeyeWebConstants.clean_html_code:
      string = re.sub(r'\s{2,}', ' ', string)
      string = string.replace('> ', '>')
      string = string.replace(' <', '<')
    elif DeyeWebConstants.add_html_comments:
      string = string.replace('--><!--', '-->\n<!--')
    return string.strip()

  @staticmethod
  def get_shortened_string(string: str) -> str:
    """
    Generate a shortened unique string for a given name using crc32.

    Args:
        name (str): The original string (e.g., register name).

    Returns:
        str: Shortened unique string in hexadecimal.

    Example:
        >>> get_shortened_string("master_battery_soc")
        '1a2b3c4d'
    """
    # Compute CRC32
    crc = zlib.crc32(string.encode('utf-8'))
    # Convert to hex, remove '0x' and pad zeros
    return f"{crc:08x}"

  @staticmethod
  def get_json_field(json_data: Any, field_name: str) -> str:
    if field_name not in json_data:
      raise KeyError(f"Missing '{field_name}' field in JSON")

    value = json_data[field_name]

    if not isinstance(value, str):
      raise TypeError(f"Field '{field_name}' must be a string")

    return value

  @staticmethod
  def get_deye_class_objects_count() -> str:
    # Get all live objects
    all_objects = gc.get_objects()

    # Count objects of classes containing "deye" (case-insensitive)
    deye_counter = Counter(type(obj).__name__ for obj in all_objects if "deye" in type(obj).__name__.lower())

    # Sort classes by descending count
    sorted_deye = sorted(deye_counter.items(), key = lambda x: x[1], reverse = True)

    # Form string to write to file (each class name and count on a new line)
    output_lines = [f"{cls_name}: {count}" for cls_name, count in sorted_deye]
    return "\n".join(output_lines)

  @staticmethod
  def get_tail(string: str, separator: str) -> str:
    """
    Return the substring after the last occurrence of a given separator.

    Args:
        string (str): The input string.
        separator (str): The separator to search for.

    Returns:
        str: The substring from the character after the last occurrence
              of the separator to the end of the string. If the separator
              is not found, the entire original string is returned.
    """
    # Find the position of the last occurrence of the separator
    pos = string.rfind(separator)

    # If separator is not found, return the whole string
    if pos == -1:
      return string

    # Return the substring after the last separator
    return string[pos + 1:]
