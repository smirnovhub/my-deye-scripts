import telebot

from typing import Dict, cast
from battery_settings_page import BatterySettingsPage

class BatterySettingsHelper:
  @staticmethod
  def get_data_as_rich_message(
    title: str,
    values: Dict[BatterySettingsPage, int],
  ) -> telebot.types.InputRichMessage:
    rows = []
    for page, value in values.items():
      rows.append((page.title, f"{value}%"))

    def create_cell(
      value: str,
      row: int,
      column: int,
    ) -> telebot.types.RichBlockTableCell:
      return telebot.types.RichBlockTableCell(
        text = cast(telebot.types.RichText, value),
        align = "left" if column == 0 else "center",
        valign = "middle",
      )

    cells = [[create_cell(
      value = value,
      row = row_idx,
      column = col_idx,
    ) for col_idx, value in enumerate(row_data)] for row_idx, row_data in enumerate(rows)]

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
