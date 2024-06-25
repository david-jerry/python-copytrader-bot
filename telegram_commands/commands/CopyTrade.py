from datetime import datetime, date
from typing import Optional
from data.Networks import Network, Networks
from data.Queries import CoinData, UserCopyTradesTasksData, UserData, WalletData
from lib.GetDotEnv import TOKEN
from lib.Logger import LOGGER
from telegram import ForceReply, ReplyKeyboardRemove, Update
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
from data.Constants import (
    help_message,
    about_message,
    faq_messages,
    agreement_message,
    agreement_message_I,
    agreement_message_II,
    agreement_message_III,
)
from lib.WalletClass import CryptoWallet
from models.CoinsModel import Coins, Platform
from models.CopyTradeModel import UserCopyTradesTasks
from models.UserModel import User, UserWallet
from tasks import copytrade_task
from telegram_commands.commands.Messages import profile_msg, wallet_msg
from .Buttons import (
    setWalletKeyboard,
    start_buttons,
    auth_start_buttons,
    agreement_buttons,
    profile_buttons,
    wallet_buttons,
    wallet_button_II,
    setKeyboard,
)

ADDRESS_RECEIVER = range(1)


async def start_copy_trade_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Copy Trade":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What address would you like to copy trade from?
                """
            kb = ForceReply(selective=True, input_field_placeholder="Watched Address")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return ADDRESS_RECEIVER
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup=await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_wallet_address(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network = [
        network for network in Networks if network.id == wallet.chain_id
    ][0]

    valid = await CryptoWallet(network.sn).validate_address(text)
    if not valid:
        response_text = (
            "Invalid wallet address, Please provide a correct wallet address."
        )
        kb = ForceReply(selective=True, input_field_placeholder="Wallet Address")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return ADDRESS_RECEIVER

    token = context.bot.token
    if usr and wallet is not None:
        result = copytrade_task.delay(wallet.sec_key, text, chat_id)
        data = UserCopyTradesTasks(
            id=f"{chat_id}-{result.id}",
            user_id=chat_id,
            copy_trade_id=str(result.id),
            watcher_address=text,
            status=1,
        )
        await UserCopyTradesTasksData.create_copy_trade_tasks(data)
        response_text = f"""
COPY TRADE ACTIVE
------------------------------
Copy Trade Transaction ID: {result.id}
Target Address: {text}
Status: 💚
------------------------------
When you want to end a copy trade actively running, pass the argument like this: /stop_trade {result.id}
            """
        kb = await setKeyboard(auth_start_buttons)
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return ConversationHandler.END
    await context.bot.send_message(
        chat_id=chat_id,
        text="Attach a wallet address first before you can start using the platform",
        parse_mode=ParseMode.HTML,
        reply_markup=await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END
