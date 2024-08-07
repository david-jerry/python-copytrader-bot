from datetime import datetime, date
from typing import Optional
from data.Networks import Network, Networks
from data.Queries import CoinData, PresetsData, UserData, WalletData
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
from lib.TokenMetadata import TokenMetadata
from lib.Types import TokenInfo
from lib.WalletClass import ETHWallet, SolanaWallet
from models import Presets
from models.CoinsModel import Coins, Platform
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


(
    TOKEN_IN,
    TOKEN_OUT,
    AMOUNT_IN,
    DEADLINE,
) = range(4)


async def buy_and_sell_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]

    if text == "Buy/Sell" or text == "Swap":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = f"""
Provide the token name eg: (USDT) or token's contract address you would like to swap for:

This should be a valid {network.name} contract address or token symbol
                """
            kb = ForceReply(selective=True, input_field_placeholder="Token In")
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
            return TOKEN_IN
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_token_in(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]

    if len(text) < 25:
        token_in: Coins = await TokenMetadata().get_token_id(text)
        if token_in is not None and not token_in.platforms.ethereum:
            response_text = "We do not have this token's contract address, Please provide the token address so we can update our data."
            kb = ForceReply(
                selective=True, input_field_placeholder="Token In Contract Address"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            context.user_data["update_symbol"] = token_in.symbol
            return TOKEN_IN
        CoinData
        context.user_data["tokenIn"] = token_in.platforms.ethereum if network.sn != "SOL" else token_in.platforms.solana
    else:
        valid = await ETHWallet(network.sn).validate_address(text)
        if not valid and network.sn != "SOL":
            response_text = "Invalid contract address, Please provide the correct contract address for this token."
            kb = ForceReply(
                selective=True, input_field_placeholder="Token In Contract Address"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return TOKEN_IN
        symbol = context.user_data.get("update_symbol")
        if symbol and network.sn != "SOL":
            Platform.update(_id=symbol, data={"ethereum": text})
        else:
            Platform.update(_id=symbol, data={"solana": text})

        context.user_data["tokenIn"] = text

    wallet = await WalletData.get_wallet_by_id(chat_id)
    if usr and wallet is not None:
        response_text = f"""
Provide the token name eg: (USDT) or token's contract address you would like to get in exchange:

This should be a valid {network.name} contract address or token symbol
            """
        kb = ForceReply(selective=True, input_field_placeholder="Token Out")
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return TOKEN_OUT
    await context.bot.send_message(
        chat_id=chat_id,
        text="Attach a wallet address first before you can start using the platform",
        parse_mode=ParseMode.HTML,
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


async def process_token_out(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]

    if len(text) < 25:
        token_out: Coins = await TokenMetadata().get_token_id(text)
        if token_out is not None and not (token_out.platforms.ethereum or token_out.platforms.solana):
            response_text = "We do not have this token's contract address, Please provide the token address so we can update our data."
            kb = ForceReply(
                selective=True, input_field_placeholder="Token Out Contract Address"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            context.user_data["update_symbol"] = token_out.symbol
            return TOKEN_OUT
        context.user_data["tokenOut"] = token_out.platforms.ethereum if network.sn != "SOL" else token_out.platforms.solana
    else:
        valid = await ETHWallet(network.sn).validate_address(text)
        if not valid:
            response_text = "Invalid contract address, Please provide the correct contract address for this token."
            kb = ForceReply(
                selective=True, input_field_placeholder="Token Out Contract Address"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return TOKEN_OUT
        symbol = context.user_data.get("update_symbol")
        if symbol and network.sn != "SOL":
            Platform.update(_id=symbol, data={"ethereum": text})
        else:
            Platform.update(_id=symbol, data={"solana": text})
        context.user_data["tokenOut"] = text

    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    if usr and wallet is not None:
        response_text = f"""
How much of your token in, would you like to sell (in {'ETH' if wallet.chain_name.lower() != 'solana' else 'SOL'}):
            """
        kb = ForceReply(
            selective=True,
            input_field_placeholder=f"Amount in ({'ETH' if wallet.chain_name.lower() != 'solana' else 'SOL'})",
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return AMOUNT_IN
    await context.bot.send_message(
        chat_id=chat_id,
        text="Attach a wallet address first before you can start using the platform",
        parse_mode=ParseMode.HTML,
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


async def process_amount_in(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    preset: Presets.Presets = await PresetsData.get_presets_by_id(chat_id)

    min_amount = 0.0143 if wallet.chain_name.lower() != "solana" else 5.0

    if not float(text) >= min_amount:
        response_text = f"Insufficient trade amount. Minimum expected amount to swap is: <b>{min_amount} {'ETH' if wallet.chain_name.lower() != 'solana' else 'SOL'}</b>"
        kb = ForceReply(
            selective=True,
            input_field_placeholder=f"Amount in ({'ETH' if wallet.chain_name.lower() != 'solana' else 'SOL'})",
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return AMOUNT_IN

    amountIn = float(text)

    if network.sn != "SOL":
        tokenInContractAddress = await ETHWallet(network.sn).convert_to_checksum(
            context.user_data.get("tokenIn")
        )
        tokenOutContractAddress = await ETHWallet(network.sn).convert_to_checksum(
            context.user_data.get("tokenOut")
        )

        tokenInMetadata: Optional[TokenInfo] = await TokenMetadata.get_token_symbol_by_contract(tokenInContractAddress)
        tokenOutMetadata: Optional[TokenInfo] = await TokenMetadata.get_token_symbol_by_contract(tokenOutContractAddress)

        amountIn_wei = amountIn * 10**tokenInMetadata.decimal.ethereum

        amountOut = await ETHWallet(network.sn).calculate_eth_amount_out(
            amountIn_wei, tokenInContractAddress, tokenOutContractAddress
        )

        amountOut_wei = amountOut * 10**tokenOutMetadata.decimal.ethereum


        transactionHash = await ETHWallet(network.sn).swap_tokens_with_uniswap(
            wallet.sec_key,
            tokenInContractAddress,
            tokenOutContractAddress,
            amountIn_wei,
            amountOut_wei,
        )
    else:
        transactionHash = await SolanaWallet().execute_swap(
            wallet.sol_sec_key,
            tokenInContractAddress,
            tokenOutContractAddress,
            amountIn,
            preset.slippage if preset is not None else 0.24,
        )

    response_text = transactionHash
    kb = await setKeyboard(profile_buttons)
    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode=ParseMode.HTML,
        reply_markup= await setKeyboard(profile_buttons),
    )
    return ConversationHandler.END
