import telebot

from typing import Dict, Callable, cast
from dataclasses import dataclass

from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

# Represents a single button choice with display text and associated data
@dataclass
class AdvancedChoiceButton:
  text: str
  data: str

# Holds all information required to render and track a paginated list of options
@dataclass
class PagedOptions:
  # Available options (label → value)
  options: Dict[str, str]
  # Message text above the buttons
  text: str
  # Callback when user makes a choice
  callback: Callable[[int, AdvancedChoiceButton], None]
  # Current page number
  page: int
  # Number of option rows per page
  max_lines_per_page: int
  # Number of buttons per row
  max_per_row: int
  # Telegram chat ID for this message
  chat_id: int
  # Total number of pages
  total_pages: int
  # Do we need too edit message and add selection
  edit_message_with_user_selection: bool

class AdvancedChoice:
  # Prefix used to identify all callback_data strings for this feature
  _choice_prefix = '_adv_choice_'

  # Constants for navigation / special buttons
  _page_prev = "!prev!_"
  _page_next = "!next!_"
  _noop = "!noop!_"

  # Prevents multiple registrations of the same callback handler
  _is_global_handler_registered = False

  # Stores state of paged option menus by message_id
  _paged_options: Dict[int, PagedOptions] = {}

  @staticmethod
  def ask_advanced_choice(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: Dict[str, str],
    callback: Callable[[int, AdvancedChoiceButton], None],
    max_per_row: int = 5,
    max_lines_per_page: int = 5,
    edit_message_with_user_selection: bool = False,
  ) -> telebot.types.Message:
    """
    Sends a message with paginated inline keyboard choices.
    - Registers global callback handler if not already registered.
    - Saves menu state in _paged_options.
    - Displays the first page.
    """
    # If there are no options, send plain text message
    if not options:
      return bot.send_message(chat_id, text, parse_mode = 'HTML')

    # Validate that option values do not conflict with reserved navigation/noop
    try:
      AdvancedChoice._validate_option_values(options)
    except Exception as e:
      return bot.send_message(chat_id, f'{AdvancedChoice.__name__}: {str(e)}')

    # Ensure the callback handler is registered only once
    AdvancedChoice._register_global_handler(bot)

    # Initialize menu state
    page_data = PagedOptions(
      options = options,
      text = text,
      callback = callback,
      page = 0,
      max_lines_per_page = max_lines_per_page,
      max_per_row = max_per_row,
      chat_id = chat_id,
      total_pages = (len(options) + max_lines_per_page - 1) // max_lines_per_page,
      edit_message_with_user_selection = edit_message_with_user_selection,
    )

    # Save state before sending
    # We'll use message_id as key after sending
    # Create keyboard for first page
    keyboard = AdvancedChoice._build_keyboard_for_page(page_data)

    # Send the message already with first page keyboard
    message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = 'HTML')

    # Save state with actual message_id
    AdvancedChoice._paged_options[message.message_id] = page_data

    # Register a next-step handler (used if user sends new message instead of clicking)
    bot.register_next_step_handler(
      message,
      AdvancedChoice._user_advanced_choice_next_step_handler,
      bot,
      message.message_id,
      text,
      edit_message_with_user_selection,
    )

    return message

  @staticmethod
  def _validate_option_values(options: Dict[str, str]):
    """
    Ensures that none of the option values conflict with reserved navigation
    or noop identifiers. Raises ValueError if a conflict is found.
    """
    reserved_values = [
      AdvancedChoice._page_prev.rstrip("_"),
      AdvancedChoice._page_next.rstrip("_"),
      AdvancedChoice._noop.rstrip("_")
    ]

    for value in options.values():
      if value in reserved_values:
        raise ValueError(f"option value '{value}' is reserved and cannot be used as a button data.")

  @staticmethod
  def _build_keyboard_for_page(page_data: PagedOptions) -> telebot.types.InlineKeyboardMarkup:
    """
    Builds an InlineKeyboardMarkup for a given PagedOptions page.
    Fills empty slots with placeholder buttons to keep last page layout uniform.
    Adds navigation buttons (Prev / Next) and a center page indicator if needed.
    Returns the keyboard ready to use in send_message or edit_message_text.
    """
    # Extract options for current page
    options_list = list(page_data.options.items())
    page = page_data.page
    max_lines = page_data.max_lines_per_page
    max_per_row = page_data.max_per_row

    start = page * max_lines
    end = start + max_lines
    page_options = options_list[start:end] # list of (text, data) tuples

    # Build list of InlineKeyboardButton for actual options
    buttons = []
    for text, data in page_options:
      buttons.append(
        telebot.types.InlineKeyboardButton(
          text,
          callback_data = data if data.startswith('/') else f"{AdvancedChoice._choice_prefix}{data}_",
        ))

    # Calculate total buttons needed to fill exactly max_lines * max_per_row slots
    total_buttons_needed = min(max_lines * max_per_row, len(options_list))

    # Fill remaining slots with non-clickable placeholders (use a callback with prefix)
    while len(buttons) < total_buttons_needed:
      buttons.append(
        telebot.types.InlineKeyboardButton(
          " ",
          callback_data = f"{AdvancedChoice._choice_prefix}{AdvancedChoice._noop}",
        ))

    # Arrange buttons into rows
    keyboard = telebot.types.InlineKeyboardMarkup()
    for i in range(0, len(buttons), max_per_row):
      keyboard.row(*buttons[i:i + max_per_row])

    # Hide navigation if all options fit on one page
    if page_data.total_pages > 1:
      prev_callback = f"{AdvancedChoice._choice_prefix}{AdvancedChoice._page_prev}"
      next_callback = f"{AdvancedChoice._choice_prefix}{AdvancedChoice._page_next}"

      prev_button = telebot.types.InlineKeyboardButton("Prev", callback_data = prev_callback)
      next_button = telebot.types.InlineKeyboardButton("Next", callback_data = next_callback)

      # Add center button showing current page (non-clickable / harmless callback)
      page_label = f"{page + 1}/{page_data.total_pages}"
      page_button = telebot.types.InlineKeyboardButton(
        page_label,
        callback_data = f"{AdvancedChoice._choice_prefix}{AdvancedChoice._page_next}",
      )

      # Put Prev, PageIndicator, Next on the same row
      keyboard.row(prev_button, page_button, next_button)

    return keyboard

  @staticmethod
  def _edit_message_with_page(bot: telebot.TeleBot, message_id: int):
    """
    Updates the message to display a specific page of options with navigation buttons.
    Always adds two navigation buttons ("Prev" and "Next") when there are multiple pages.
    Ensures the last page always contains exactly max_lines_per_page rows by filling
    empty slots with placeholder buttons that have no meaningful callback.
    """
    page_data = AdvancedChoice._paged_options.get(message_id)
    if not page_data:
      return

    keyboard = AdvancedChoice._build_keyboard_for_page(page_data)

    # Try to edit the message text with updated keyboard
    try:
      bot.edit_message_text(
        page_data.text,
        chat_id = page_data.chat_id,
        message_id = message_id,
        reply_markup = keyboard,
        parse_mode = 'HTML',
      )
    except Exception:
      # Ignore exceptions (e.g., message already edited/deleted)
      pass

  @staticmethod
  def _register_global_handler(bot: telebot.TeleBot) -> None:
    """
    Registers a single global callback_query_handler for all advanced choice interactions.
    Handles:
      - Page navigation ("Prev" / "Next")
      - User selections
    """
    if AdvancedChoice._is_global_handler_registered:
      return
    AdvancedChoice._is_global_handler_registered = True

    @bot.callback_query_handler(func = TelebotUtils.make_callback_query_filter(AdvancedChoice._choice_prefix))
    def handle(call: telebot.types.CallbackQuery):
      bot.answer_callback_query(call.id)

      data = call.data
      msg_id = call.message.message_id
      page_data = AdvancedChoice._paged_options.get(msg_id)

      if not page_data:
        return

      # Handle page navigation buttons
      if f"{AdvancedChoice._choice_prefix}{AdvancedChoice._noop}" == data:
        return
      elif f"{AdvancedChoice._choice_prefix}{AdvancedChoice._page_prev}" == data:
        # Navigate to the prev page with circular behavior
        page_data.page = (page_data.page - 1) % page_data.total_pages
        AdvancedChoice._edit_message_with_page(bot, msg_id)
        return
      elif f"{AdvancedChoice._choice_prefix}{AdvancedChoice._page_next}" == data:
        # Navigate to the next page with circular behavior
        page_data.page = (page_data.page + 1) % page_data.total_pages
        AdvancedChoice._edit_message_with_page(bot, msg_id)
        return

      # Handle specific option selection
      TelebotUtils.remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        delay = TelebotConstants.buttons_remove_delay_sec,
      )

      # Extract choice data from callback_data string
      choice_text = data[len(AdvancedChoice._choice_prefix):-1]
      button = TelebotUtils.get_inline_button_by_data(cast(telebot.types.Message, call.message), str(data))
      choice = AdvancedChoiceButton(text = button.text if button else 'unknown', data = choice_text)

      # Update message to reflect user’s selection
      try:
        if page_data.edit_message_with_user_selection:
          bot.edit_message_text(
            f'{call.message.text} {choice.text}',
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            parse_mode = 'HTML',
          )
      except Exception:
        pass

      # Remove saved state
      AdvancedChoice._paged_options.pop(msg_id, None)

      # Execute the callback
      callback = page_data.callback
      callback(call.message.chat.id, choice)

  @staticmethod
  def _user_advanced_choice_next_step_handler(
    message: telebot.types.Message,
    bot: telebot.TeleBot,
    message_id: int,
    text: str,
    edit_message_with_user_selection: bool,
  ):
    """
    Handles user messages after an advanced choice was asked.
    - Removes inline buttons.
    - If the user sends a command (starting with '/'), it forwards it to the bot.
    - If the user sends anything else, marks the question as skipped.
    """
    TelebotUtils.remove_inline_buttons_with_delay(
      bot = bot,
      chat_id = message.chat.id,
      message_id = message_id,
      delay = TelebotConstants.buttons_remove_delay_sec,
    )

    try:
      # Indicate that user skipped the selection
      if edit_message_with_user_selection:
        bot.edit_message_text(
          f'{text} skipped',
          chat_id = message.chat.id,
          message_id = message_id,
          parse_mode = 'HTML',
        )
    except Exception:
      pass

    # Forward new commands to the bot
    TelebotUtils.forward_next(bot, message)
