from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler

from telegram_commands.commands.Actions import cancel
from telegram_commands.commands.AttachWalletCommands import (
    accept_pass_phrase,
    accept_private_key,
    handle_pass_phrase_wallet_attachment,
    handle_private_key_wallet_attachment,
    handle_sol_pass_phrase_wallet_attachment,
    handle_sol_private_key_wallet_attachment
)
from telegram_commands.commands.BuyOrSellTokens import (
    buy_and_sell_trigger,
    process_token_in,
    process_token_out,
    process_amount_in,
)
from telegram_commands.commands.CopyTrade import process_wallet_address, start_copy_trade_trigger
from telegram_commands.commands.Presets import (
    balance_tradable_trigger,
    gas_delta_trigger,
    gas_limit_trigger,
    max_gas_price_trigger,
    min_circulating_supply_trigger,
    min_total_supply_trigger,
    process_balance_tradable,
    process_gas_delta,
    process_gas_limit,
    process_max_gas_price,
    process_min_circulating_supply,
    process_min_total_supply,
    process_slippage,
    process_snipe_stop_loss,
    process_snipe_take_profit,
    slippage_trigger,
    snipe_stop_loss_trigger,
    snipe_take_profit_trigger,
)

PRIVKEY, SOL_PRIVKEY, PASSPHRASE, SOL_PASSPHRASE = range(4)
attach_wallet_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Have Pass Phrase$"), handle_pass_phrase_wallet_attachment),
        MessageHandler(filters.Regex(r"^Have Private Key$"), handle_private_key_wallet_attachment)
    ],
    states={
        PASSPHRASE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_pass_phrase)
        ],
        SOL_PASSPHRASE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sol_pass_phrase_wallet_attachment)
        ],
        SOL_PRIVKEY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sol_private_key_wallet_attachment)
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

(GAS_DELTA,) = range(1)
gas_delta_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Gas Delta$"), gas_delta_trigger)],
    states={
        GAS_DELTA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_gas_delta)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

(TRADABLE,) = range(1)
balance_tradable_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Balance Tradable$"), balance_tradable_trigger)],
    states={
        TRADABLE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_balance_tradable)
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

(SNIPE_PROFIT) = range(1)
snipe_profit_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(r"^Snipe Take Profit$"), snipe_take_profit_trigger
        )
    ],
    states={
        SNIPE_PROFIT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, process_snipe_take_profit
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # Handle any message while attaching
)

(SNIPE_LOSS) = range(1)
snipe_loss_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(r"^Snipe Stop Loss$"), snipe_stop_loss_trigger
        )
    ],
    states={
        SNIPE_LOSS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, process_snipe_stop_loss
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




