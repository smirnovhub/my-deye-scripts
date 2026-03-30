from pathlib import Path

from typing import Any, List, Dict

from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebInstallIosProfileCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([DeyeWebRemoteCommand.install_ios_profile])

  async def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Dict[str, Any],
  ) -> Dict[str, str]:
    result: Dict[str, str] = {}

    id = DeyeWebUtils.short(DeyeWebSection.service.title)
    result[id] = DeyeWebUtils.clean(self.generate_icons_table(3))

    style_id = DeyeWebConstants.styles_template.format(command.name)
    result[style_id] = self.style_manager.generate_css()

    return result

  def generate_icons_table(self, columns_count: int) -> str:
    names = self.get_image_file_names('icons/ios')

    style_id_table = self.style_manager.register_style('border-collapse: collapse;')
    style_id1 = self.style_manager.register_style('padding: 15px; text-align: center;')
    style_id2 = self.style_manager.register_style('border-radius: 20px; width: 100px; display: block;')

    # Start the table tag with some basic styling
    html = f'<table class="{style_id_table}">'

    icon_counter = 0

    # Iterate through the list in chunks (rows)
    for i in range(0, len(names), columns_count):
      html += '<tr>'

      # Get the current row
      row_items = names[i:i + columns_count]

      for item in row_items:
        icon_counter += 1

        onerror = (f"this.style.display='inline-block'; "
                   f"this.parentNode.innerHTML='<span style=\\'font-size: 25px; "
                   f"font-weight: bold;\\'>icon_{icon_counter:02d}</span>';")

        html += f"""
            <td class="{style_id1}">
              <a href="mobileconfig.php?icon={item}">
                <img class="{style_id2}" src="icons/ios/{item}.png" onerror="{onerror}">
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
    filenames.sort()
    return filenames
