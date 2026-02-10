#!/usr/bin/python3 -u

import os
import sys
import traceback

from pathlib import Path
from typing import List

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_base_section import DeyeWebBaseSection
from deye_web_sections_holder import DeyeWebSectionsHolder
from deye_web_style_manager import DeyeWebStyleManager
from deye_web_remote_command import DeyeWebRemoteCommand

def build_tab_header(sections: List[DeyeWebBaseSection]):
  menu = ''
  for section in sections:
    menu += section.build_tab_header()

  arrow_size = 50

  style_id = style_manager.register_style(f"padding-bottom: 5px;")

  result = f"""
    <div class="scroll-wrapper">
      <div id="scroll-left" class="fixed {style_id}"><img width="{arrow_size}"
        src="images/left_arrow.svg"></div>
      <div id="menu" class="scrollmenu">
        {menu}
      </div>
      <div id="scroll-right" class="fixed {style_id}"><img width="{arrow_size}"
        src="images/right_arrow.svg"></div>
    </div>
  """

  print(DeyeWebUtils.clean(result))

def build_tab_content(sections: List[DeyeWebBaseSection], style_manager: DeyeWebStyleManager):
  content = ''
  for section in sections:
    content += section.build_tab_content()

  style_id = style_manager.register_style(DeyeWebConstants.flex_center_style)

  result = f"""
    <div class="{style_id}">
      {content}
    </div>
  """

  print(DeyeWebUtils.clean(result))

try:
  sections_holder = DeyeWebSectionsHolder()
  style_manager = DeyeWebStyleManager()

  build_tab_header(sections_holder.sections)

  style_id = style_manager.register_style("background-color: red; color: white; text-align: center;")

  print(f"""
      <div class="remote_data {style_id}" id="error_field"
        data-remote_field="{DeyeWebConstants.result_error_field}">
      </div>
    """)

  build_tab_content(sections_holder.sections, style_manager)

  print(style_manager.generate_css())
except Exception as e:
  print(f'{str(e)}\n{traceback.format_exc()}')

for command in DeyeWebRemoteCommand:
  style_id = DeyeWebConstants.styles_template.format(command.name)
  print(f"""
      <div class="remote_data" id="{style_id}"
        data-remote_field="{style_id}">
      </div>
    """)

print(f"""
  <div class="remote_data" id="callstack_field"
    data-remote_field="{DeyeWebConstants.result_callstack_field}">
  </div>
""")

#from deye_web_utils import DeyeWebUtils
#with open("/tmp/front_classes_count.txt", "w", encoding = "utf-8") as f:
#  f.write(DeyeWebUtils.get_deye_class_objects_count())
