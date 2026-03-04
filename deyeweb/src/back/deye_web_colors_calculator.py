import os
import json
import tempfile

from typing import Dict, cast

from deye_web_utils import DeyeWebUtils
from deye_web_color import DeyeWebColor
from deye_file_with_lock import DeyeFileWithLock
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
    self.fname = os.path.join(tempfile.gettempdir(), f'deye_web_colors_{session_id}.json')

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

  def save_colors(self, colors: Dict[str, DeyeWebColor]) -> None:
    locker = DeyeFileWithLock()
    try:
      f = locker.open_file(self.fname, 'w')
      data_to_save = {k: v.name for k, v in colors.items()}

      json.dump(
        data_to_save,
        f,
        ensure_ascii = False,
      )

      # Flush to physical storage
      f.flush()
    except Exception:
      pass
    finally:
      locker.close_file()

  def load_colors(self) -> Dict[str, DeyeWebColor]:
    locker = DeyeFileWithLock()
    try:
      f = locker.open_file(self.fname, 'r')
      content = f.read()
      if not content:
        return {}

      js = json.loads(content)
      saved_colors = cast(Dict[str, str], js)
      return self._restore_colors(saved_colors)
    except Exception:
      return {}
    finally:
      locker.close_file()

  def _restore_colors(self, obj: Dict[str, str]) -> Dict[str, DeyeWebColor]:
    # Mapping string names back to Enum members
    return {k: DeyeWebColor[v] for k, v in obj.items() if v in DeyeWebColor.__members__}
