from typing import Dict

from simple_singleton import singleton
from deye_web_utils import DeyeWebUtils

@singleton
class DeyeWebStyleManager:
  def __init__(self):
    self.styles: Dict[str, str] = {}

  def register_style(self, style_str: str) -> str:
    style_str = DeyeWebUtils.clean(style_str)
    if not style_str:
      return ''

    id = DeyeWebUtils.get_shortened_string(style_str)

    if not id[0].isalpha():
      id = f's{id}'

    self.styles[id] = style_str
    return id

  def generate_css(self) -> str:
    """Generate CSS from a dict where keys are class names and values are style strings.

      Example:
        {
            "center-flex": "display: flex; justify-content: center; align-items: center;",
            "red-text": "color: red;"
        }
    """
    if not self.styles:
      return ''

    parts = []

    for class_name, style in self.styles.items():
      parts.append(f".{class_name} {{ {style} }}")
    styles = " ".join(parts)

    return f"<style> {styles} </style>"
