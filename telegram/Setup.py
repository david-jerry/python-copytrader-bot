import html
import json
import traceback
from warnings import filterwarnings
from lib.GetDotEnv import DEVELOPER_CHAT_ID, TOKEN, USERNAME
from lib.Logger import LOGGER
from telegram import Update, ParseMode
from telegram.ext import (
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
)
from telegram.warnings import PTBUserWarning
from data.Constants import help_message
from .CommandsImports import commands

# Suppress specific warnings from the telegram library
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

def handle_response(text: str) -> str:
    """Process the incoming text and return a response."""
    processed_text = text.lower()
    if any(word in processed_text for word in ["assist me", "support", "commands", "help"]):
        return help_message
    return text

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages."""
    chat_type = update.message.chat.type  # Determine the chat type (private or group)
    chat_id = update.message.chat.id
    text = update.message.text  # The message text to be processed
    LOGGER.debug(f"user: {chat_id} in {chat_type}: '{text}'")

    if chat_type == "private":
        response = handle_response(text)
        await context.bot.send_message(chat_id=chat_id, text=response, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, I cannot be in a group and would do nothing for you here.",
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify the developer via Telegram."""
    LOGGER.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)

async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors to the console."""
    LOGGER.error(f"Update: {update}\n\ncaused error: {context.error}")

def telegram_setup() -> None:
    """Set up and run the Telegram bot."""
    LOGGER.info("Initializing CopyTraderBot")
    LOGGER.info(f"Bot Name: {USERNAME}")
    app = Application.builder().token(TOKEN).build()
    LOGGER.info("App Initialized and Ready")

    # Handle messages
    LOGGER.info("Message handler initiated")
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    for command in commands:
        app.add_handler(command)


    # Error handling
    app.add_error_handler(log_error)
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
