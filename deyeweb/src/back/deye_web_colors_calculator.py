import ast
import os
import tempfile

from typing import Dict, cast

from deye_web_utils import DeyeWebUtils
from key_value_store import KeyValueStore
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_registers_section import DeyeWebRegistersSection
from deye_web_sections_holder import DeyeWebSectionsHolder

class DeyeWebColorsCalculator:
  def __init__(
    self,
    sections_holder: DeyeWebSectionsHolder,
    session_id: str,
  ):
    self.sections_holder = sections_holder
    fname = os.path.join(tempfile.gettempdir(), f'deye_web_{session_id}.json')
    self.store = KeyValueStore(fname)

  def get_sections_colors(
    self,
    colors: Dict[str, DeyeWebColor],
  ) -> Dict[str, str]:
    max_color = DeyeWebColor.gray
    all_colors: Dict[str, DeyeWebColor] = {}
    result: Dict[str, str] = {}

    for section in self.sections_holder.sections:
      color = DeyeWebColor.gray

      if isinstance(section, DeyeWebRegistersSection):
        for register in section.registers:
          next_color = colors.get(register.name, DeyeWebColor.gray)
          if next_color.id > color.id:
            color = next_color

      if color.id > max_color.id:
        max_color = color

      if color == DeyeWebColor.green:
        color = DeyeWebColor.gray

      all_colors[section.section.id] = color

    for section in self.sections_holder.sections:
      color = all_colors[section.section.id]
      id = DeyeWebUtils.short(DeyeWebConstants.tab_color_template.format(section.section.id))
      if color == DeyeWebColor.gray:
        if max_color == DeyeWebColor.yellow:
          result[id] = DeyeWebColor.light_yellow.color
        elif max_color == DeyeWebColor.red:
          result[id] = DeyeWebColor.light_red.color
        else:
          result[id] = color.color
      else:
        result[id] = color.color

    return result

  def save_colors(self, colors: Dict[str, DeyeWebColor]):
    self.store.set('colors', str({k: v.name for k, v in colors.items()}))

  def load_colors(self, ) -> Dict[str, DeyeWebColor]:
    saved_colors_str = self.store.get('colors')
    saved_colors = ast.literal_eval(str(saved_colors_str))
    return self._restore_colors(cast(Dict[str, str], saved_colors))

  def _restore_colors(self, obj: Dict[str, str]) -> Dict[str, DeyeWebColor]:
    return {k: DeyeWebColor[v] for k, v in obj.items()}
