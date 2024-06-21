import asyncio
from lib.CryptoWatcher import CryptoWatcherHttp, CryptoWatcherWs
from lib.Logger import LOGGER
from telegram import ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackContext,
)

from typing import Dict, Any, List

STEP_STACK_KEY = 'step_stack'

def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation."""
    update.message.reply_text('Cancelled!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def start_copytrade(update: Update, context: CallbackContext) -> None:
    """Handle the /start_copytrade command."""
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /start_copytrade <watcher_private_key> <target_wallet_address>")
            return

        watcher_private_key = args[0]
        target_wallet_address = args[1]

        crypto_copy_trader = CryptoWatcherWs
        asyncio.create_task(crypto_copy_trader.copytrade(watcher_private_key, target_wallet_address))

        await update.message.reply_text("Started copy trading for the target wallet address.")
    except Exception as e:
        LOGGER.error(f"Error starting copy trade: {e}")
        await update.message.reply_text("Failed to start copy trading.")
