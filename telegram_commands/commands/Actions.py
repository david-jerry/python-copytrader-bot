import asyncio
from datetime import datetime

# from lib.CryptoWatcher import CryptoWatcherHttp, CryptoWatcherWs
from lib.Logger import LOGGER
from telegram import ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackContext,
)
from data.Constants import help_message, about_message, faq_messages
from data.Queries import CoinData, PresetsData, UserData, WalletData
from lib.WalletClass import ETHWallet
from models.CoinsModel import Coins
from models.Presets import Presets
from models.UserModel import User, UserWallet
from .Buttons import start_buttons, auth_start_buttons, wallet_buttons, setKeyboard
from typing import Dict, Any, List, Optional

STACK_KEY = "keyboard_key"


async def start(update: Update, context: CallbackContext):
    context.user_data.clear()
    chat_id = update.effective_chat.id
    user = update.message.from_user

    # initialize a message stack to store keyboard states
    context.user_data[STACK_KEY] = []

    # Fetch the bot's profile photo
    bot_profile_photos = await context.bot.get_user_profile_photos(
        context.bot.id, limit=1
    )
    bot_profile_photo = bot_profile_photos.photos[0][0] if bot_profile_photos else None

    kb = await setKeyboard(start_buttons)
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: UserWallet = await WalletData.get_wallet_by_id(chat_id)
    if usr is not None and usr.accepted_agreement:
        kb = await setKeyboard(auth_start_buttons) if wallet is not None else await setKeyboard(wallet_buttons)
    elif usr is None:
        data: User = User(
            user_id = chat_id,
            first_name = user.first_name or None,
            last_name = user.last_name or None,
            username = user.username or None,
        )
        user: User = await UserData.create_user(data)

    if bot_profile_photo:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=bot_profile_photo,
            caption=faq_messages,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id, text=faq_messages, parse_mode="HTML", reply_markup=kb
        )


async def about(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id, text=about_message, parse_mode="HTML"
    )


async def faq(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id, text=faq_messages, parse_mode="HTML"
    )


async def help(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id, text=help_message, parse_mode="HTML"
    )


async def cancel(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    kb = await setKeyboard(start_buttons)
    usr: User | None = await UserData.get_user_by_id(chat_id)
    if usr is not None and usr.accepted_agreement:
        kb = await setKeyboard(auth_start_buttons)
    await context.bot.send_message(chat_id=chat_id, text="Cancelled", reply_markup=kb)
    return ConversationHandler.END


# async def start_copytrade(update: Update, context: CallbackContext) -> None:
#     """Handle the /start_copytrade command."""
#     try:
#         args = context.args
#         if len(args) != 2:
#             await update.message.reply_text(
#                 "Usage: /start_copytrade <watcher_private_key> <target_wallet_address>"
#             )
#             return

#         watcher_private_key = args[0]
#         target_wallet_address = args[1]

#         crypto_copy_trader = CryptoWatcherWs
#         context.bot_data["ws_task"] = asyncio.create_task(
#             crypto_copy_trader.copytrade(watcher_private_key, target_wallet_address)
#         )
#         await update.message.reply_text(
#             "Started copy trading for the target wallet address."
#         )
#     except Exception as e:
#         LOGGER.error(f"Error starting copy trade: {e}")
#         await update.message.reply_text("Failed to start copy trading.")


async def stop_trade(update: Update, context: CallbackContext) -> None:
    from celery.result import AsyncResult

    args = context.args
    LOGGER.debug(f"Stop Trade Args: {args}")
    chat_id = update.effective_chat.id

    if args:
        task_id = args[0]  # Assuming the task ID is the first argument
        LOGGER.info(f"Attempting to stop task with ID: {task_id}")

        result = AsyncResult(task_id)
        LOGGER.info(f"Task state: {result.state}")

        kb = setKeyboard(auth_start_buttons)

        if result.state in ["PENDING", "STARTED"]:
            result.revoke(terminate=True)
            LOGGER.info(f"Revoked task: {task_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Stopped trade with task ID: {task_id}.",
                reply_markup=kb,
            )
        else:
            LOGGER.info(f"Task {task_id} is not active. Current state: {result.state}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Task {task_id} is not active. Current state: {result.state}.",
                reply_markup=kb,
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id, text="No task ID provided in the command.", reply_markup=kb
        )
