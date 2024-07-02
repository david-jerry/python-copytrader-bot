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
from lib.WalletClass import ETHWallet
from models.CoinsModel import Coins, Platform
from models.Presets import Presets
from models.UserModel import User, UserWallet
from telegram_commands.commands.Messages import preset_msg, profile_msg, wallet_msg
from .Buttons import (
    setWalletKeyboard,
    start_buttons,
    presets_button,
    auth_start_buttons,
    agreement_buttons,
    profile_buttons,
    wallet_buttons,
    wallet_button_II,
    setKeyboard,
)


(
    PROCESS_SLIPPAGE,
) = range(1)


async def slippage_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Slippage":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What is the slippage you would like to set. Value should range from 1 - 100
                """
            kb = ForceReply(selective=True, input_field_placeholder="4")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return PROCESS_SLIPPAGE
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_slippage(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)

    amount = float(text.strip().replace("%", ""))/100 if float(text.strip().replace("%", "")) > 0 else 0.04

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            slippage=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "slippage": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


GAS_DELTA = range(1)
async def gas_delta_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Gas Delta":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
Provide a gas delta, this can be any whole number from 1-1000: default 50
                """
            kb = ForceReply(selective=True, input_field_placeholder="50")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return GAS_DELTA
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_gas_delta(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    amount = await ETHWallet(network.sn).convert_to_wei(float(text.strip()))

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            gas_delta=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "gas_delta": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


TRADABLE = range(1)
async def balance_tradable_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Balance Tradable":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What percentage of your balance should be used to copy trade or snipe. Value should range from 1 - 100
                """
            kb = ForceReply(selective=True, input_field_placeholder="15 %")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return TRADABLE
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_balance_tradable(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    amount = float(text.strip().replace("%", "")) / 100 if float(text.strip().replace("%", "")) <= 0 else 0.15

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            balance_tradable=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "balance_tradable": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


GAS_LIMIT = range(1)
async def gas_limit_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Gas Limit":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What do you want to be your gas limit in ETH:
                """
            kb = ForceReply(selective=True, input_field_placeholder="0.00004 ETH")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return GAS_LIMIT
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_gas_limit(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    amount = await ETHWallet(network.sn).convert_to_wei(float(text.strip().replace("ETH","")))

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            gas_limit=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "gas_limit": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


MAX_GAS_PRICE = range(1)
async def max_gas_price_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Max Gas Price":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What do you want to set for the max gas price in ETH:
                """
            kb = ForceReply(selective=True, input_field_placeholder="0.00004 ETH")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return MAX_GAS_PRICE
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_max_gas_price(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    amount = await ETHWallet(network.sn).convert_to_wei(float(text.strip().replace("ETH","")))

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            max_gas_price=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "max_gas_price": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


MIN_C_SUPPLY = range(1)
async def min_circulating_supply_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Min Circulating Supply":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What do you want to set for the minimum circulating supply for the token in USD:
                """
            kb = ForceReply(selective=True, input_field_placeholder="2000 USD")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return MIN_C_SUPPLY
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_min_circulating_supply(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    amount = float(text.strip().replace("USD",""))

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            min_circulating_supply=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "min_circulating_supply": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END


MIN_T_SUPPLY = range(1)
async def min_total_supply_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Min Total Supply":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
What do you want to set for the minimum total supply for the token in USD:
                """
            kb = ForceReply(selective=True, input_field_placeholder="2000000 USD")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return MIN_T_SUPPLY
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_min_total_supply(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    amount = float(text.strip().replace("USD",""))

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            min_token_supply=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "min_token_supply": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END

SNIPE_PROFIT = range(1)
async def snipe_take_profit_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Snipe Take Profit":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
When should the bot sell to take profit. Value should be in whole number ranging from 1 - 100:
                """
            kb = ForceReply(selective=True, input_field_placeholder="40 %")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return SNIPE_PROFIT
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_snipe_take_profit(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    amount = float(text.strip().replace("%","")) / 100 if float(text.strip().replace("%","")) > 0 else 0.35

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            snipe_take_profit=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "snipe_take_profit": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END

SNIPE_LOSS = range(1)
async def snipe_stop_loss_trigger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)

    if text == "Snipe Stop Loss":
        wallet = await WalletData.get_wallet_by_id(chat_id)
        if usr and wallet is not None:
            response_text = """
When should the bot sell to reduce loss. Value should be in whole number ranging from 1 - 100:
                """
            kb = ForceReply(selective=True, input_field_placeholder="40 %")
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return SNIPE_LOSS
        await context.bot.send_message(
            chat_id=chat_id,
            text="Attach a wallet address first before you can start using the platform",
            parse_mode=ParseMode.HTML,
            reply_markup= await setKeyboard(wallet_buttons),
        )
        return ConversationHandler.END


async def process_snipe_stop_loss(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text  # Get the text from the button pressed
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(chat_id)
    kb = await setKeyboard(presets_button)
    amount = float(text.strip().replace("%","")) / 100 if float(text.strip().replace("%","")) > 0 else 0.35

    preset: Presets = await PresetsData.get_presets_by_id(f"{chat_id}-{wallet.chain_id}")
    if preset is None:
        data = Presets(
            id=f"{chat_id}-{wallet.chain_id}",
            chain_id=str(wallet.chain_id),
            chain_name=wallet.chain_name,
            snipe_stop_loss=amount,
        )
        preset: Presets = await PresetsData.create_presets(data)
    else:
        id=f"{chat_id}-{wallet.chain_id}"
        data = {
            "snipe_stop_loss": amount
        }
        preset: Presets = await PresetsData.update_presets(id, data)

    if usr and wallet is not None:
        response_text = await preset_msg(wallet, preset)

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
        reply_markup= await setKeyboard(wallet_buttons),
    )
    return ConversationHandler.END

