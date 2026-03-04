import traceback

from typing import List

from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_base_section import DeyeWebBaseSection
from deye_web_sections_holder import DeyeWebSectionsHolder
from deye_web_style_manager import DeyeWebStyleManager
from deye_web_remote_command import DeyeWebRemoteCommand

class DeyeWebFrontContentBuilder:
  def __init__(self):
    self.sections_holder = DeyeWebSectionsHolder()
    self.style_manager = DeyeWebStyleManager()

  def get_front_html(self) -> str:
    result = """
          <!DOCTYPE html>
          <html>

          <head>
            <title>Deye Web</title>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <link href="css/style.css" rel="stylesheet" type="text/css">
            <link href="css/spinner.css" rel="stylesheet" type="text/css">
          </head>

          <body style="background-color: #ffffff;">
            <script src="js/script.js"></script>
            <script src="js/JsHttpRequest.js"></script>
      """.strip()

    try:
      style_id = self.style_manager.register_style("background-color: red; color: white; text-align: center;")

      result += self.build_tab_header(self.sections_holder.sections)
      result += f"""
          <div class="remote_data {style_id}" id="error_field"
            data-remote_field="{DeyeWebConstants.result_error_field}">
          </div>
        """

      result += self.build_tab_content(self.sections_holder.sections, self.style_manager)
      result += self.style_manager.generate_css()
    except Exception as e:
      result += f'{str(e)}\n{traceback.format_exc()}'

    for command in DeyeWebRemoteCommand:
      style_id = DeyeWebConstants.styles_template.format(command.name)
      result += f"""
          <div class="remote_data" id="{style_id}"
            data-remote_field="{style_id}">
          </div>
        """

    result += f"""
          <div class="remote_data" id="callstack_field"
            data-remote_field="{DeyeWebConstants.result_callstack_field}">
          </div>

        </body>
      </html>
    """

    return DeyeWebUtils.clean(result)

  def build_tab_header(self, sections: List[DeyeWebBaseSection]) -> str:
    menu = ''
    for section in sections:
      menu += section.build_tab_header()

    arrow_size = 50

    style_id = self.style_manager.register_style(f"padding-bottom: 5px;")

    return f"""
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

  def build_tab_content(
    self,
    sections: List[DeyeWebBaseSection],
    style_manager: DeyeWebStyleManager,
  ) -> str:
    content = ''
    for section in sections:
      content += section.build_tab_content()

    style_id = style_manager.register_style(DeyeWebConstants.flex_center_style)

    return f"""
      <div class="{style_id}">
        {content}
      </div>
    """
