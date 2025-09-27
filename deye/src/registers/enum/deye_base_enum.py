import enum
from typing import Optional

class DeyeBaseEnum(enum.Enum):
  def __str__(self):
    """
    Return a string representation of the enum member where
    underscores are replaced with dashes.
    """
    return self.name.replace('_', '-')

  @property
  def pretty(self):
    """
    Return a human-friendly string representation of the enum member
    where underscores are replaced with spaces and words are title-cased.
    """
    return self.name.replace('_', ' ').title()

  @classmethod
  def parse(cls, value: str) -> Optional["DeyeBaseEnum"]:
    """
    Parse a string and return the corresponding enum member if a match is found.
    The input string is normalized (trimmed and lowercased) and compared against:
      - the original enum name (e.g. "SELLING_FIRST")
      - the string form via __str__ (e.g. "selling-first")
      - the pretty form (e.g. "Selling First")

    If no match is found, None is returned.

    Args:
        value: The input string to parse.

    Returns:
        The matching enum member, or None if no match is found.
    """
    if not value:
      return None

    value = value.strip().lower()

    for member in cls:
      if value in (member.name.lower(), str(member).lower(), member.pretty.lower()):
        return member

    return None
