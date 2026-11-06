import telebot

from typing import List, cast
from dataclasses import dataclass
from cell_align import CellAlign

@dataclass
class TelebotTableCell:
  value: str
  colspan: int = 1
  is_header: bool = False
  align: CellAlign = CellAlign.center
  is_bold: bool = False
  is_strikethrough: bool = False

  @staticmethod
  def create_cell(cell: "TelebotTableCell") -> telebot.types.RichBlockTableCell:
    text_val: telebot.types.RichText = cast(telebot.types.RichText, cell.value)

    if cell.is_bold or cell.is_header:
      text_val = telebot.types.RichTextBold(text_val)

    if cell.is_strikethrough:
      text_val = telebot.types.RichTextStrikethrough(text_val)

    return telebot.types.RichBlockTableCell(
      text = text_val,
      align = cell.align.value,
      valign = "middle",
      is_header = True if cell.is_header else None,
      colspan = cell.colspan if cell.colspan > 1 else None,
    )

  @staticmethod
  def create_cells(cells: List[List["TelebotTableCell"]]) -> List[List[telebot.types.RichBlockTableCell]]:
    return [[TelebotTableCell.create_cell(cell) for cell in row] for row in cells]
