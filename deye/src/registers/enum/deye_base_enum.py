import enum
from typing import Optional

from deye_exceptions import DeyeValueException

class DeyeBaseEnum(enum.Enum):
  def __str__(self) -> str:
    """
    Return a string representation of the enum member where
    underscores are replaced with dashes.
    """
    return self.name.replace('_', '-')

  @property
  def pretty(self) -> str:
    """
    Return a human-friendly string representation of the enum member
    where underscores are replaced with spaces and words are title-cased.
    """
    return self.name.replace('_', ' ').title()

  @property
  def is_unknown(self) -> bool:
    return self.value == -1

  @classmethod
  def parse(cls, value: str) -> "DeyeBaseEnum":
    """
    Parse a string and return the corresponding enum member.

    The input string is normalized (trimmed and lowercased) and compared against:
      - the original enum name (e.g. "SELLING_FIRST")
      - the string form via __str__ (e.g. "selling-first")
      - the pretty form (e.g. "Selling First")

    If no match is found, returns the member with `value == -1`.
    Raises DeyeValueException if the enum does not have a member with `value == -1`.

    Args:
        value: The input string to parse.

    Returns:
        The matching enum member, or the member with `value == -1` if no match is found.

    Raises:
        DeyeValueException: If the enum does not have a member with `value == -1`.
    """
    unknown_member: Optional[DeyeBaseEnum] = None

    for member in cls:
      if member.value == -1:
        unknown_member = member
        break

    if unknown_member is None:
      raise DeyeValueException(f"{cls.__name__}: enum doesn't have 'unknown' member with value -1")

    if not value:
      return unknown_member

    value = value.strip().lower()

    for member in cls:
      if value in (member.name.lower(), str(member).lower(), member.pretty.lower()):
        return member

    return unknown_member
