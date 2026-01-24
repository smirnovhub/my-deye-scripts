from deye_web_base_section import DeyeWebBaseSection
from deye_web_constants import DeyeWebConstants
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils

class DeyeWebForecastSection(DeyeWebBaseSection):
  def __init__(self):
    super().__init__(DeyeWebSection.forecast)

  def build_tab_content(self) -> str:
    id1 = DeyeWebUtils.short(DeyeWebConstants.page_template.format(self.section.id))
    id2 = DeyeWebUtils.short(DeyeWebConstants.forecast_id)

    style_id1 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)

    command = DeyeWebRemoteCommand.get_forecast_by_percent.name

    on_click = f"""onclick="{command}('{id2}')" """

    cursor_style_id = self.style_manager.register_style(DeyeWebConstants.cursor_style)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <div id="{id1}" class="tabcontent">
        <table class="{style_id1}">
          <tr>
            <td {on_click} class="{cursor_style_id}">
              Get forecast
            </td>
          </tr>
        </table>
        <br>
        <table class="{style_id1}">
          <tr>
            <td>
              <div id="{id2}" class="{DeyeWebConstants.remote_data_name}" data-remote_field="{id2}"></div>
            </td>
          </tr>
        </table>
        <br><br>
        <div class="counter {style_id1}">&nbsp;</div>
      </div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()
