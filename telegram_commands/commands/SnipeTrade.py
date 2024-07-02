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
from lib.WalletClass import ETHWallet
from models.CoinsModel import Coins, Platform
from models.CopyTradeModel import UserCopyTradesTasks
from models.UserModel import User, UserWallet
from tasks import copytrade_task, snipe_task
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

MINT_ADDRESS = range(1)


async def start_snipe_trade_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Snipe":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What token contract address/mint address would you like to be trading the new tokens against when the bot sells? This can be left empty to trade back to native sol.
                """
            kb = ForceReply(
                selective=True, input_field_placeholder="Mint/Contract Address"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return MINT_ADDRESS
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup=await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_mint_address(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network = [
        network for network in Networks if network.id == wallet.chain_id
    ][0]

    valid = (
        await ETHWallet(network.sn).validate_address(text)
        if network.sn != "SOL"
        else True
    )
    if not valid:
        response_text = (
            "Invalid contract address, Please provide a correct token contract address."
        )
        kb = ForceReply(selective=True, input_field_placeholder="Mint/Contract Address")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return MINT_ADDRESS

    if usr and wallet is not None:
        result = snipe_task.delay(chat_id, text)
        response_text = f"""
SNIPE TRADE ACTIVE
------------------------------
Snipe Trade Transaction ID: {result.id}
Token Minted: {text}
Status: 💚
------------------------------
SNIPE TRADES EXECUTE BUY AND SELL ON THEIR OWN. ONCE THEY FIND A TOKEN THAT IS PERFORMING WELL IN THE MARKET, IT BUYS THE TOKEN FOR YOU AND THEN WATCHES FOR A PROFIT SPIKE OR LOSS SPIKE TO STOP LOSSES OR TAKE PROFITS FOR YOU.
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
