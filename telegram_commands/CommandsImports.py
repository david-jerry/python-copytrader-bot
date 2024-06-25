from .commands.Actions import (
    # start_copytrade,
    # stop_watch_ws,
    cancel,
    about,
    help,
    faq,
    start,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
)

# start_copytrade = CommandHandler("start_copytrade", start_copytrade)
# stop_watch_ws = CommandHandler("stop_copytrade", stop_watch_ws)
cancel = CommandHandler("cancel", cancel)
about = CommandHandler("about", about)
help = CommandHandler("help", help)
faq = CommandHandler("faq", faq)
start = CommandHandler("start", start)


commands = [cancel, about, help, faq, start] # start_copytrade, stop_watch_ws
