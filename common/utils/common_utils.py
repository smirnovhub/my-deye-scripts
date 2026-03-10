import socket

from typing import Optional
from urllib.parse import unquote

class CommonUtils:
  large_green_circle_emoji = unquote("%F0%9F%9F%A2")
  large_yellow_circle_emoji = unquote("%F0%9F%9F%A1")
  large_red_circle_emoji = unquote("%F0%9F%94%B4")
  white_circle_emoji = unquote("%E2%9A%AA")
  clock_face_one_oclock = unquote("%F0%9F%95%90")
  clock_face_two_oclock_emoji = unquote("%F0%9F%95%91")
  nbsp = unquote("%C2%A0")

  @staticmethod
  def get_external_ip() -> Optional[str]:
    """
    Retrieves the local IP address of the primary network interface.

    This function attempts to 'connect' a UDP socket to Google's Public DNS 
    (8.8.8.8) on port 53. No actual data is sent over the network; the OS 
    simply identifies the local IP address required to route traffic to 
    the internet.

    Returns:
        The local IP address as a string (e.g., '192.168.1.15'). 
        Returns None if the network is unreachable or an error occurs.
    """
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 53))
        return s.getsockname()[0]
    except Exception:
      return None

  @staticmethod
  def get_original_error(exc: BaseException) -> BaseException:
    """
    Recursively unwraps an exception to find the root cause of the error.

    Traverses the exception chain by checking for '__cause__' (explicit chaining)
    or '__context__' (implicit chaining). This is useful for identifying the 
    original failure in deeply nested try-except blocks.

    Args:
        exc: The exception object to begin unwrapping from.

    Returns:
        The base exception at the end of the chain.
    """
    cause = exc.__cause__ or exc.__context__
    if cause:
      return CommonUtils.get_original_error(cause)
    return exc
