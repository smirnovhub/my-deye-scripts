import telebot

from typing import List, cast
from dataclasses import dataclass
from cell_align import CellAlign

@dataclass
class TableCell:
  value: str
  colspan: int = 1
  align: CellAlign = CellAlign.center
  is_header: bool = False
  is_bold: bool = False
  is_strikethrough: bool = False

  @staticmethod
  def create_cell(cell: "TableCell") -> telebot.types.RichBlockTableCell:
    text = cast(telebot.types.RichText, cell.value)

    if cell.is_bold or cell.is_header:
      text = telebot.types.RichTextBold(text)

    if cell.is_strikethrough:
      text = telebot.types.RichTextStrikethrough(text)

    return telebot.types.RichBlockTableCell(
      text = text,
      align = cell.align.value,
      valign = "middle",
      is_header = True if cell.is_header else None,
      colspan = cell.colspan if cell.colspan > 1 else None,
    )

  @staticmethod
  def create_cells(cells: List[List["TableCell"]]) -> List[List[telebot.types.RichBlockTableCell]]:
    return [[TableCell.create_cell(cell) for cell in row] for row in cells]
