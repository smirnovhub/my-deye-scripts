import telebot

from typing import Dict, List

row_break_str = '!break!'

def get_keyboard_for_choices(
  options: Dict[str, str],
  max_per_row: int,
  data_prefix: str = '',
) -> telebot.types.InlineKeyboardMarkup:
  """
  Build an inline keyboard where:
    - keys of the dict are button texts,
    - values of the dict are callback_data strings.
  Buttons are arranged in rows with up to max_per_row buttons each.
  An empty string as a key forces a line break (starts a new row).
  """
  keyboard = telebot.types.InlineKeyboardMarkup()
  row: List[telebot.types.InlineKeyboardButton] = []

  for text, data in options.items():
    if row_break_str in (text, data):
      # Commit the current row (if not empty) and start a new one
      if row:
        keyboard.row(*row)
        row = []
      continue

    btn = telebot.types.InlineKeyboardButton(text, callback_data = data_prefix + data)
    row.append(btn)

    # Commit row if it's full
    if len(row) == max_per_row:
      keyboard.row(*row)
      row = []

  # Add remaining buttons in the last row
  if row:
    keyboard.row(*row)

  return keyboard
