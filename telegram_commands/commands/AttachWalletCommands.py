from datetime import datetime, date
from typing import Optional
from data.Networks import Network, Networks
from data.Queries import UserData, WalletData
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
from models.UserModel import User, UserWallet
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


PUBKEY, PRIVKEY = range(2)


async def handle_wallet_attachment(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Attach Wallet":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr:
            if wallet is None:
                response_text = """
Provide your wallet address:
                """
            kb = ForceReply(selective=True, input_field_placeholder="Public Address")
            await context.bot.send_message(
                chat_id=chat_id,
                text="...",
                reply_markup=ReplyKeyboardRemove(),  # Remove existing keyboard
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return PUBKEY
        return ConversationHandler.END


async def accept_public_address(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0]
    valid = await CryptoWallet(network.sn).validate_address(text)

    if not valid:
        response_text = "Invalid wallet address"
        kb = ForceReply(selective=True, input_field_placeholder="Public Address")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return PUBKEY
    context.user_data["pubKey"] = text

    wallet = await WalletData.get_wallet_by_id(chat_id)
    if usr:
        if wallet is None:
            response_text = """
Provide your private key to approve transactions with:
            """
        kb = ForceReply(selective=True, input_field_placeholder="Private key")
        await context.bot.send_message(
            chat_id=chat_id,
            text="...",
            reply_markup=ReplyKeyboardRemove(),  # Remove existing keyboard
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return PRIVKEY
    return ConversationHandler.END


async def accept_private_key(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0]
    valid = CryptoWallet(network.sn).is_valid_private_key(text)
    pubKey = context.user_data.get("pubKey")

    if not valid:
        response_text = "Invalid wallet address"
        kb = ForceReply(selective=True, input_field_placeholder="Public Address")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return PRIVKEY

    wallet = await WalletData.get_wallet_by_id(chat_id)
    if usr:
        if wallet is None:
            data = {"user_id": str(chat_id), "pub_key": pubKey, "sec_key": text}
            wallet = await WalletData.create_wallet(data)
            response_text = wallet_msg(wallet)
            if usr:
                kb = await setKeyboard(wallet_button_II)
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return ConversationHandler.END
    return ConversationHandler.END
