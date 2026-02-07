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
          <table>
            <tr>
              <td onclick="window.location.href='mobileconfig.php';" class="{style_id1} {style_id2} {cursor_style_id}">
                Install iOS Profile
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
          <div class="counter {style_id3}">&nbsp;</div>
        </center>
      </div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()
