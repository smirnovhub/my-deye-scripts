import telebot

from typing import Dict, cast
from cell_align import CellAlign
from telebot_table_cell import TelebotTableCell
from battery_settings_page_type import BatterySettingsPageType

class BatterySettingsHelper:
  @staticmethod
  def get_data_as_rich_message(
    title: str,
    values: Dict[BatterySettingsPageType, int],
  ) -> telebot.types.InputRichMessage:
    rows_data = [[
      TelebotTableCell(value = page.title, align = CellAlign.left),
      TelebotTableCell(value = f"{value}%"),
    ] for page, value in values.items()]

    cells = TelebotTableCell.create_cells(rows_data)

    return telebot.types.InputRichMessage(blocks = [
      telebot.types.InputRichBlockParagraph(telebot.types.RichTextBold(cast(
        telebot.types.RichText,
        title,
      ))),
      telebot.types.InputRichBlockTable(
        cells = cells,
        is_bordered = True,
        is_striped = False,
        is_compact = True,
      ),
    ])
