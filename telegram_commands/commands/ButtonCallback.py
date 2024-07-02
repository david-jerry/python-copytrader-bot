from datetime import datetime, date
from typing import Optional
from data.Networks import Networks, Network
from data.Queries import PresetsData, UserData, WalletData
from solders.keypair import Keypair
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
from telegram_commands.commands.Messages import preset_msg, profile_msg, wallet_msg
from .Buttons import (
    setWalletKeyboard,
    start_buttons,
    presets_button,
    auth_start_buttons,
    agreement_buttons,
    profile_buttons,
    wallet_buttons,
    attach_buttons,
    wallet_button_II,
    setKeyboard,
)

# def get_network_index(networks, target_id):
#   """
#   Finds the index of a network with the specified ID in the list of networks.

#   Args:
#       networks (list): A list of Network objects.
#       target_id (int): The ID of the network to find the index for.

#   Returns:
#       int: The index of the network with the target ID, or -1 if not found.
#   """
#   for index, network in enumerate(networks):
#     if network.id == target_id:
#       return index
#   return -1

# def get_adjacent_networks(networks, target_id):
#   """
#   Finds the network objects for the previous and next network based on the target ID.

#   Args:
#       networks (list): A list of Network objects.
#       target_id (int): The ID of the network used as a reference point.

#   Returns:
#       tuple: A tuple containing two Network objects:
#           - The network object with the ID before the target (if found).
#           - The network object with the ID after the target (if found).
#   """
#   target_index = get_network_index(networks, target_id)

#   # Handle potential out-of-bounds scenarios
#   previous_network = None
#   next_network = None

#   if target_index > 0:
#     previous_network = networks[target_index - 1]
#   if target_index != -1 and target_index < len(networks) - 1:
#     next_network = networks[target_index + 1]

#   return previous_network, next_network


async def handle_response(text: str) -> str:
    """Process the incoming text and return a response."""
    processed_text = text.lower()
    if any(
        word in processed_text for word in ["assist me", "support", "commands", "help"]
    ):
        return handle_button_click
    return text


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages."""
    chat_type = update.message.chat.type  # Determine the chat type (private or group)
    chat_id = update.message.chat.id
    text = update.message.text  # The message text to be processed
    LOGGER.debug(f"user: {chat_id} in {chat_type}: '{text}'")

    if chat_type == "private":
        response = await handle_response(text)
        await context.bot.send_message(
            chat_id=chat_id, text=response, parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, I cannot be in a group and would do nothing for you here.",
        )


async def handle_button_click(update: Update, context: CallbackContext):
    chat_type = update.message.chat.type  # Determine the chat type (private or group)
    chat_id = update.effective_chat.id
    user = update.message.from_user
    text = update.message.text  # Get the text from the button pressed

    kb = await setKeyboard(start_buttons)
    LOGGER.debug(f"user: {chat_id} in {chat_type}: '{text}'")
    # Implement logic based on the button text
    usr: User | None = await UserData.get_user_by_id(chat_id)
    wallet: UserWallet = await WalletData.get_wallet_by_id(chat_id)
    presets = await PresetsData.get_presets_by_id(chat_id)

    if usr is not None and usr.accepted_agreement:
        kb = await setKeyboard(auth_start_buttons) if wallet is not None else await setKeyboard(wallet_buttons)
    elif usr is None:
        user_json = User(
            user_id = chat_id,
            first_name = user.first_name or None,
            last_name = user.last_name or None,
            username = user.username or None,
        )
        usr = await UserData.create_user(user_json)

    if chat_type == "private":
        if text == "About":
            response_text = about_message
        elif text == "Home":
            response_text = None
        elif text == "Help":
            response_text = help_message
        elif text == "FAQ":
            response_text = faq_messages
        elif text == "✅ Accept":
            data = {
                "accepted_agreement": True,
                "accepted_on": date.today(),
            }
            user: User = await UserData.update_user(chat_id, data)
            if user and user.accepted_agreement:
                kb = await setKeyboard(auth_start_buttons) if wallet is not None else await setKeyboard(wallet_buttons)
            response_text = "You accepted CopiTradaBot Usage Agreement. We are happy to have you onboard. You should take the time to click the help to get a list of available commands you can execute"
        elif text == "🪙 ETH":
            if wallet is not None:
                network: Network  = [network for network in Networks if network.sn == "ETH"][0]
                data = {"chain_id": network.id, "chain_name": network.name}
                wallet = await WalletData.update_wallet(chat_id, data)
                kb = await setWalletKeyboard()
            response_text = await wallet_msg(wallet)
        elif text == "🪙 POL":
            if wallet is not None:
                network: Network = [network for network in Networks if network.sn == "POL"][0]
                data = {"chain_id": network.id, "chain_name": network.name}
                wallet = await WalletData.update_wallet(chat_id, data)
                kb = await setWalletKeyboard()
            response_text = await wallet_msg(wallet)
        elif text == "🪙 SOL":
            if wallet is not None:
                network: Network = [network for network in Networks if network.sn == "SOL"][0]
                data = {"chain_id": network.id, "chain_name": network.name}
                wallet = await WalletData.update_wallet(chat_id, data)
                kb = await setWalletKeyboard()
            response_text = await wallet_msg(wallet)
        elif text == "🪙 BSC":
            if wallet is not None:
                network: Network = [network for network in Networks if network.sn == "BSC"][0]
                data = {"chain_id": network.id, "chain_name": network.name}
                wallet = await WalletData.update_wallet(chat_id, data)
                kb = await setWalletKeyboard()
            response_text = await wallet_msg(wallet)
        elif text == "🪙 AVL":
            if wallet is not None:
                network: Network = [network for network in Networks if network.sn == "AVL"][0]
                data = {"chain_id": network.id, "chain_name": network.name}
                wallet = await WalletData.update_wallet(chat_id, data)
                kb = await setWalletKeyboard()
            response_text = await wallet_msg(wallet)
        elif text == "Profile":
            response_text = profile_msg(usr)
            if usr and wallet is not None:
                kb = await setKeyboard(profile_buttons)
        elif text == "Wallets":
            response_text = await wallet_msg(wallet)
            if usr:
                if wallet is not None:
                    kb = await setWalletKeyboard()
                else:
                    kb = await setKeyboard(wallet_buttons)
        elif text == "Attach Wallet":
            if usr and wallet is None:
                response_text = await wallet_msg(wallet)
                kb = await setKeyboard(attach_buttons)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb,
                )
            await context.bot.send_message(
                chat_id=chat_id,
                text="We do not have you on our database. Please type this command '/start'",
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        elif text == "Create Wallet":
            network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]

            eth_wallet = await ETHWallet(network.sn).generate_multi_chain_wallet()
            sol_wallet = await SolanaWallet().generate_multi_chain_wallet()
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
            response_text = await wallet_msg(wallet)
            if usr:
                kb = await setKeyboard(wallet_button_II)
        elif text == "Presets":
            response_text = await preset_msg(wallet, presets)
            kb = await setKeyboard(presets_button)
        elif text == "Detach Wallet":
            wallet = await WalletData.delete_wallet(chat_id)
            response_text = await wallet_msg(wallet)
            if usr:
                kb = await setKeyboard(wallet_buttons)
        elif text == "Wallet Bal":
            wallet = await WalletData.get_wallet_by_id(chat_id)
            response_text = await wallet_msg(wallet)
            if usr:
                kb = await setWalletKeyboard()
        elif text == "Cancel":
            await context.bot.send_message(
                chat_id=chat_id,
                text="Cancelled ✖",
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            return ConversationHandler.END
        elif text == "Decline ❌" or text == "Terminate Agreement":
            data = {
                "accepted_agreement": False,
                "accepted_on": None,
            }
            await UserData.update_user(chat_id, data)
            if user:
                kb = await setKeyboard(start_buttons)
            response_text = "You declined CopiTradaBot Usage Agreement. Most features will be unavailable to use until you have accepted our terms for use to prevent any loss"
        elif text == "Accept Agreement":
            response_text = agreement_message_III
            kb = await setKeyboard(agreement_buttons)
            await context.bot.send_message(
                chat_id=chat_id,
                text=agreement_message,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=agreement_message_I,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=agreement_message_II,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        else:
            response_text = await handle_response(text)

        if response_text is not None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        else:
            await context.bot.send_message(chat_id=chat_id, text="...", reply_markup=kb)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, I cannot be in a group and would do nothing for you here.",
        )
