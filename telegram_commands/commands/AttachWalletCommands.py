from datetime import datetime, date
from typing import Optional
from data.Networks import Network, Networks
from data.Queries import PresetsData, UserData, WalletData
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
from lib.WalletClass import ETHWallet, SolanaWallet
from models.Presets import Presets
from models.UserModel import User, UserWallet
from telegram_commands.commands.Messages import profile_msg, wallet_msg
from .Buttons import (
    setWalletKeyboard,
    start_buttons,
    auth_start_buttons,
    agreement_buttons,
    profile_buttons,
    attach_buttons,
    wallet_buttons,
    wallet_button_II,
    setKeyboard,
)


PRIVKEY, SOL_PRIVKEY, PASSPHRASE, SOL_PASSPHRASE = range(4)


async def handle_private_key_wallet_attachment(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    kb = await setKeyboard(attach_buttons)

    if text == "Have Private Key":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is None:
            response_text = """
Paste your EVM (Ethereum, Polygon, Avalanche or Binance Smart Chain) private key to attach your these wallet:
            """
            kb = ForceReply(selective=True, input_field_placeholder="Paste EVM Private key")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return SOL_PRIVKEY
        await context.bot.send_message(
            chat_id=chat_id,
            text="We do not have you on our database. Please type this command '/start'",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return ConversationHandler.END

async def handle_pass_phrase_wallet_attachment(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    kb = await setKeyboard(attach_buttons)

    if text == "Have Pass Phrase":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is None:
            response_text = """
Paste an EVM (Ethereum, Avalanche, Polygon or Binance Smart Chain) pass phrase to attach your these wallets:
            """
            kb = ForceReply(selective=True, input_field_placeholder="Paste EVM Pass Phrase")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return SOL_PASSPHRASE
        await context.bot.send_message(
            chat_id=chat_id,
            text="We do not have you on our database. Please type this command '/start'",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return ConversationHandler.END
    
async def handle_sol_pass_phrase_wallet_attachment(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    kb = await setKeyboard(attach_buttons)
    
    context.user_data['evm_passphrase'] = text if len(text) > 0 else None

    wallet = await WalletData.get_wallet_by_id(chat_id)
    if usr and wallet is None:
        response_text = """
Paste Your SOLANA pass phrase to attach your wallet:
        """
        kb = ForceReply(selective=True, input_field_placeholder="Paste SOL Pass Phrase")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return PASSPHRASE
    await context.bot.send_message(
        chat_id=chat_id,
        text="We do not have you on our database. Please type this command '/start'",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    return ConversationHandler.END    


async def accept_pass_phrase(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]


    if len(text) > 1 and wallet is None:
        eth_wallet = await ETHWallet(network.sn).generate_multi_chain_wallet(mnemonic=context.user_data['evm_passphrase'])
        sol_wallet = await SolanaWallet().generate_multi_chain_wallet(sol_mnemonic=text)
        data: UserWallet = UserWallet(
            user_id=chat_id,
            pub_key=eth_wallet[0],
            sec_key=eth_wallet[1],
            mnemonic=eth_wallet[2],
            sol_pub_key=sol_wallet[0],
            sol_sec_key=sol_wallet[1],
            sol_mnemonic=sol_wallet[2],
            pass_phrase=text,
            chain_name=network.name,
            chain_id=network.id,
        )
        wallet: UserWallet = await WalletData.create_wallet(data)


        data = Presets(
            id=str(chat_id),
            chain_id=str(data.chain_id),
            chain_name=data.chain_name,
            snipe_stop_loss=0.05,
            gas_limit=500,
            max_gas_price=10000,
            min_circulating_supply=50000,
            min_token_supply=10000,
        )
        await PresetsData.create_presets(data)


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

    response_text = wallet_msg(wallet)
    kb = await setKeyboard(wallet_button_II)
    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    return ConversationHandler.END

async def handle_sol_private_key_wallet_attachment(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    kb = await setKeyboard(attach_buttons)
    
    context.user_data['evm_private_key'] = text if len(text) > 0 else None

    wallet = await WalletData.get_wallet_by_id(chat_id)
    if usr and wallet is None:
        response_text = """
Paste your SOLANA private key to attach your sol wallet:
        """
        kb = ForceReply(selective=True, input_field_placeholder="Paste SOL Private key")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return PRIVKEY
    await context.bot.send_message(
        chat_id=chat_id,
        text="We do not have you on our database. Please type this command '/start'",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    return ConversationHandler.END

async def accept_private_key(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    valid = ETHWallet(network.sn).is_valid_private_key(text)

    if not valid and network.name != "solana":
        response_text = "Invalid private key"
        kb = ForceReply(selective=True, input_field_placeholder="Public Address")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return PRIVKEY

    if len(text) > 1 and wallet is None:
        eth_wallet = await ETHWallet(network.sn).generate_multi_chain_wallet(private_key_hex=context.user_data['evm_private_key'])
        sol_wallet = await SolanaWallet().generate_multi_chain_wallet(sol_private_key_hex=text)
        data: UserWallet = UserWallet(
            user_id=chat_id,
            pub_key=eth_wallet[0],
            sec_key=eth_wallet[1],
            mnemonic=eth_wallet[2],
            sol_pub_key=sol_wallet[0],
            sol_sec_key=sol_wallet[1],
            sol_mnemonic=sol_wallet[2],
            pass_phrase=text,
            chain_name=network.name,
            chain_id=network.id,
        )
        wallet: UserWallet = await WalletData.create_wallet(data)


        data = Presets(
            id=str(chat_id),
            chain_id=str(data.chain_id),
            chain_name=data.chain_name,
            snipe_stop_loss=0.05,
            gas_limit=500,
            max_gas_price=10000,
            min_circulating_supply=50000,
            min_token_supply=10000,
        )
        await PresetsData.create_presets(data)


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

    response_text = wallet_msg(wallet)
    kb = await setKeyboard(wallet_button_II)
    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    return ConversationHandler.END
