import html
import json
import traceback
from warnings import filterwarnings
from lib.GetDotEnv import DEVELOPER_CHAT_ID, TOKEN, USERNAME
from lib.Logger import LOGGER
from telegram import KeyboardButton, Update
from telegram.constants import ParseMode
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
from data.Constants import help_message, about_message, faq_messages
from telegram_commands.commands.ButtonCallback import handle_button_click
from .CommandsImports import commands
from .ConversationsImports import (
    attach_wallet_handler,
    buy_sell_handler,
    slippage_handler,
    total_supply_handler,
    min_circulating_supply_handler,
    gas_limit_handler,
    max_gas_price_handler,
    copy_trade_handler,
    gas_delta_handler,
    balance_tradable_handler,
    snipe_profit_handler,
    snipe_loss_handler,
    snipe_trade_handler
)

# Suppress specific warnings from the telegram library
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify the developer via Telegram."""
    LOGGER.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors to the console."""
    LOGGER.error(f"Update: {update}\n\ncaused error: {context.error}")


def telegram_setup() -> None:
    """Set up and run the Telegram bot."""
    LOGGER.info("Initializing CopyTraderBot")
    LOGGER.info(f"Bot Name: {USERNAME}")
    app = Application.builder().token(TOKEN).build()
    LOGGER.info("App Initialized and Ready")

    for command in commands:
        app.add_handler(command)

    # Handle messages
    LOGGER.info("Message handler initiated")
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^About$")
            | filters.Regex(r"^Home$")
            | filters.Regex(r"^Cancel$")
            | filters.Regex(r"^Help$")
            | filters.Regex(r"^FAQ$")
            | filters.Regex(r"^✅ Accept$")
            | filters.Regex(r"^Profile$")
            | filters.Regex(r"^Wallets$")
            | filters.Regex(r"^Attach Wallet$")
            | filters.Regex(r"^Create Wallet$")
            | filters.Regex(r"^Detach Wallet$")
            | filters.Regex(r"^Decline ❌$")
            | filters.Regex(r"^Terminate Agreement$")
            | filters.Regex(r"^Accept Agreement$")
            | filters.Regex(r"^Wallet Bal$")
            | filters.Regex(r"^🪙 ETH$")
            | filters.Regex(r"^🪙 POL$")
            | filters.Regex(r"^🪙 SOL$")
            | filters.Regex(r"^🪙 BSC$")
            | filters.Regex(r"^🪙 AVL$")
            | filters.Regex(r"^Presets$"),
            handle_button_click,
        )
    )

    app.add_handler(attach_wallet_handler)
    app.add_handler(min_circulating_supply_handler)
    app.add_handler(slippage_handler)
    app.add_handler(total_supply_handler)
    app.add_handler(gas_limit_handler)
    app.add_handler(max_gas_price_handler)
    app.add_handler(buy_sell_handler)
    app.add_handler(copy_trade_handler)
    app.add_handler(gas_delta_handler)
    app.add_handler(balance_tradable_handler)
    app.add_handler(snipe_profit_handler)
    app.add_handler(snipe_loss_handler)
    app.add_handler(snipe_trade_handler)

    # Error handling
    app.add_error_handler(log_error)
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
