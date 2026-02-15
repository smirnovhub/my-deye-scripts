from pathlib import Path
from typing import List

from deye_web_base_section import DeyeWebBaseSection
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils

class DeyeWebServiceSection(DeyeWebBaseSection):
  def __init__(self):
    super().__init__(DeyeWebSection.service)

  def build_tab_content(self) -> str:
    id1 = DeyeWebUtils.short(DeyeWebConstants.page_template.format(self.section.id))
    id2 = DeyeWebUtils.short(self.section.title)

    style_id1 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
    style_id2 = self.style_manager.register_style(
      DeyeWebConstants.item_td_style_with_color.format(DeyeWebColor.green.color))
    style_id3 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)
    style_id4 = self.style_manager.register_style(f'font-weight: bold; font-size: {DeyeWebConstants.item_font_size}px;')

    cursor_style_id = self.style_manager.register_style(DeyeWebConstants.cursor_style)

    command = DeyeWebRemoteCommand.update_scripts.name

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <div id="{id1}" class="tabcontent">
        <center>
          <table>
            <tr>
              <td onclick="{command}('{id2}');" class="{style_id1} {style_id2} {cursor_style_id}">
                Update Scripts
              </td>
            </tr>
          </table>
          <br>
          <table class="{style_id3}">
            <tr>
              <td>
                <center>
                  <div id="{id2}" class="{DeyeWebConstants.remote_data_name} {DeyeWebConstants.temporary_data_name}" data-remote_field="{id2}"></div>
                </center>
              </td>
            </tr>
          </table>
          <br><br>
          <div class="{style_id4}">Install iOS Profile:</div>
          {self.generate_icons_table(3)}
          <br>
          <div class="counter {style_id3}">&nbsp;</div>
        </center>
      </div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def generate_icons_table(self, columns_count: int) -> str:
    names = self.get_image_file_names('icons/ios')

    style_id1 = self.style_manager.register_style('padding: 15px;')
    style_id2 = self.style_manager.register_style('border-radius: 20px; width: 100px;')

    # Start the table tag with some basic styling
    html = f'<table>'

    # Iterate through the list in chunks (rows)
    for i in range(0, len(names), columns_count):
      html += '<tr>'

      # Get the current row
      row_items = names[i:i + columns_count]

      for item in row_items:
        html += f"""
            <td class="{style_id1}">
              <a href="mobileconfig.php?icon={item}">
                <img class="{style_id2}" src="icons/ios/{item}.png" alt="iOS Icon">
              </a>
            </td>
          """

      # Fill remaining empty cells if the last row is incomplete
      if len(row_items) < columns_count:
        for _ in range(columns_count - len(row_items)):
          html += '<td></td>'

      html += '</tr>'
    html += '</table>'

    return html

  def get_image_file_names(self, directory_path: str) -> List[str]:
    path = Path(directory_path)
    filenames = [file.stem for file in path.glob('*.png')]
    return filenames
