import json

from typing import Dict

from env_utils import EnvUtils
from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection
from deye_web_style_manager import DeyeWebStyleManager

class DeyeWebBaseSection:
  def __init__(self, section: DeyeWebSection):
    self.section: DeyeWebSection = section
    self.style_manager = DeyeWebStyleManager()
    js = EnvUtils.get_deye_web_section_title_corrections_json()
    self.title_corrections: Dict[str, str] = json.loads(js)

  def build_tab_header(self) -> str:
    tab_id = DeyeWebUtils.short(DeyeWebConstants.tab_template.format(self.section.id))
    page_id = DeyeWebUtils.short(DeyeWebConstants.page_template.format(self.section.id))
    color_id = DeyeWebUtils.short(DeyeWebConstants.tab_color_template.format(self.section.id))

    default_open = ''
    if self.section == DeyeWebConstants.default_open_tab:
      default_open = f' {DeyeWebConstants.default_open_tab_id}'.rstrip()

    title = self.title_corrections.get(self.section.name)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <a class="tablink{default_open}" id="{tab_id}" data-remote_color="{color_id}"
        href="#" onclick="openPage('{page_id}', '{tab_id}'); return false;">
        {title if title else self.section.title}
      </a>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def build_tab_content(self) -> str:
    raise NotImplementedError('build_tab_content() is not implemented')
