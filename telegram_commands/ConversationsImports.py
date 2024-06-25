from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler

from telegram_commands.commands.Actions import cancel
from telegram_commands.commands.AttachWalletCommands import (
    accept_private_key,
    accept_public_address,
    handle_wallet_attachment,
)
from telegram_commands.commands.BuyOrSellTokens import (
    buy_and_sell_trigger,
    process_token_in,
    process_token_out,
    process_amount_in,
)
from telegram_commands.commands.CopyTrade import process_wallet_address, start_copy_trade_trigger
from telegram_commands.commands.Presets import (
    gas_limit_trigger,
    max_gas_price_trigger,
    min_circulating_supply_trigger,
    min_total_supply_trigger,
    process_gas_limit,
    process_max_gas_price,
    process_min_circulating_supply,
    process_min_total_supply,
    process_slippage,
    slippage_trigger,
)

PUBKEY, PRIVKEY = range(2)
attach_wallet_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Attach Wallet$"), handle_wallet_attachment)
    ],
    states={
        PUBKEY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_public_address)
        ],
        PRIVKEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_private_key)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)


(
    TOKEN_IN,
    TOKEN_OUT,
    AMOUNT_IN,
) = range(3)
buy_sell_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(r"^Buy/Sell$") | filters.Regex(r"^Swap$"),
            buy_and_sell_trigger,
        )
    ],
    states={
        TOKEN_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_token_in)],
        TOKEN_OUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_token_out)],
        AMOUNT_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount_in)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

(PROCESS_SLIPPAGE,) = range(1)
slippage_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Slippage$"), slippage_trigger)],
    states={
        PROCESS_SLIPPAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_slippage)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

(MIN_T_SUPPLY) = range(1)
total_supply_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Min Total Supply$"), min_total_supply_trigger)
    ],
    states={
        MIN_T_SUPPLY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_min_total_supply)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

(MIN_C_SUPPLY) = range(1)
min_circulating_supply_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(r"^Min Circulating Supply$"), min_circulating_supply_trigger
        )
    ],
    states={
        MIN_C_SUPPLY: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, process_min_circulating_supply
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

(GAS_LIMIT) = range(1)
gas_limit_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Gas Limit$"), gas_limit_trigger)],
    states={
        GAS_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_gas_limit)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)


(MAX_GAS_PRICE) = range(1)
max_gas_price_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Max Gas Price$"), max_gas_price_trigger)
    ],
    states={
        MAX_GAS_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_max_gas_price)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

ADDRESS_RECEIVER = range(1)
copy_trade_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Copy Trade$"), start_copy_trade_trigger)
    ],
    states={
        ADDRESS_RECEIVER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_wallet_address)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)




