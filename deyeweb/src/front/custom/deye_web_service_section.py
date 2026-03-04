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

    style_id1 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <div id="{id1}" class="tabcontent">
        <center>
          {self.get_command_html('Reset Cache', DeyeWebRemoteCommand.reset_cache)}
          <br>
          {self.get_command_html('Update Scripts', DeyeWebRemoteCommand.update_scripts)}
          <br>
          {self.get_command_html('Install iOS Profile', DeyeWebRemoteCommand.install_ios_profile)}
          <br>
          <table class="{style_id1}">
            <tr>
              <td>
                <center>
                  <div id="{id2}" class="{DeyeWebConstants.remote_data_name} {DeyeWebConstants.temporary_data_name}" data-remote_field="{id2}"></div>
                </center>
              </td>
            </tr>
          </table>
          <br><br>
          <div class="counter {style_id1}">&nbsp;</div>
        </center>
      </div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def get_command_html(self, title: str, command: DeyeWebRemoteCommand) -> str:
    id = DeyeWebUtils.short(self.section.title)
    command = DeyeWebUtils.get_remote_command(command, id)

    style_id1 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
    style_id2 = self.style_manager.register_style(
      DeyeWebConstants.item_td_style_with_color.format(DeyeWebColor.green.color))
    cursor_style_id = self.style_manager.register_style(DeyeWebConstants.cursor_style)

    return f"""
      <table>
        <tr>
          <td onclick="{command}" class="{style_id1} {style_id2} {cursor_style_id}">
            {title}
          </td>
        </tr>
      </table>
    """
