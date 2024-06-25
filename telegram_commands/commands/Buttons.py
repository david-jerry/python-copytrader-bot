from telegram import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from data.Networks import Networks


start_buttons = [
    [KeyboardButton("Accept Agreement")],
    [KeyboardButton("About"), KeyboardButton("FAQ")],
    [KeyboardButton("Help")],
]

auth_start_buttons = [
    [KeyboardButton("Profile")],
    [KeyboardButton("About"), KeyboardButton("Help"), KeyboardButton("FAQ")],
    [KeyboardButton("Swap"), KeyboardButton("Snipe"), KeyboardButton("Copy Trade")],
    [KeyboardButton("Terminate Agreement")],
]

profile_buttons = [
    [KeyboardButton("Wallets"), KeyboardButton("Presets")],
    [KeyboardButton("Buy/Sell"), KeyboardButton("Transactions")],
    [KeyboardButton("Home")],
]

agreement_buttons = [
    [KeyboardButton("Accept"), KeyboardButton("Decline")],
    [KeyboardButton("Home")],
]

wallet_buttons = [
    [KeyboardButton("Create Wallet"), KeyboardButton("Attach Wallet")],
    [KeyboardButton("Profile")],
]

wallet_button_II = [
    [KeyboardButton("Detach Wallet"), KeyboardButton("Wallet Bal")],
    [KeyboardButton("Profile")],
]

confirm_detach_wallet = [
    [KeyboardButton("Cancel Detach"), KeyboardButton("Confirm Detached")],
    [KeyboardButton("Wallets")],
]

presets_button = [
    [KeyboardButton("Slippage")],
    [KeyboardButton("Gas Limit"), KeyboardButton("Max Gas Price")],
    [KeyboardButton("Min Circulating Supply"), KeyboardButton("Min Total Supply")],
    [KeyboardButton("Wallets")],
]


async def setWalletKeyboard():
    wb2 = [
        [KeyboardButton(f"🪙 {chain.sn}") for chain in Networks],
        [KeyboardButton("Detach Wallet"), KeyboardButton("Wallet Bal")],
        [KeyboardButton("Profile")],
    ]
    return ReplyKeyboardMarkup(wb2, resize_keyboard=True, one_time_keyboard=False)


async def setKeyboard(buttons):
    keyboard = ReplyKeyboardMarkup(
        buttons, resize_keyboard=True, one_time_keyboard=False
    )
    return keyboard
