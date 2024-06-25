import asyncio
from typing import Optional
from celery import shared_task
from lib.CryptoWatcher import WsCryptoCopyTrader
from asgiref.sync import async_to_sync

from celery import Celery
from lib.GetDotEnv import REDIS, TOKEN
from lib.Logger import LOGGER

app = Celery("tasks", broker=REDIS, backend=REDIS)
# app.conf.update(
#     task_serializer='json',
#     accept_content=['json'],
#     result_serializer='json',
#     timezone='UTC',
#     enable_utc=True,
# )

@app.task
def copytrade_task(watcher_private_key: str, target_address: str, chat_id: int):
    async_to_sync(run_copytrade_task)(watcher_private_key, target_address, chat_id)

async def run_copytrade_task(watcher_private_key: str, target_address: str, chat_id: int):
    trader = WsCryptoCopyTrader(chat_id)
    await trader.copytrade(watcher_private_key, target_address)
