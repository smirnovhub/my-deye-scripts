import re
import os

from typing import List

class TelebotTestUtils:
  @staticmethod
  def find_tests(base_path: str = ".") -> List[str]:
    """
    Recursively search for Python test files matching patterns:
      - *_test.py
      - *_test_<number>.py
    Returns their relative paths.
    """
    pattern = re.compile(r".*_test(?:_\d+)?\.py$")
    matched_files = []

    base_path = os.path.normpath(base_path)

    for root, _, files in os.walk(base_path):
      for f in files:
        if pattern.match(f):
          rel_path = os.path.relpath(os.path.join(root, f))
          matched_files.append(rel_path)

    matched_files.sort()
    return matched_files
