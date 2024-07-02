import asyncio
from typing import Optional
from celery import shared_task
from data.Networks import Network, Networks
from data.Queries import WalletData
from lib.CryptoWatcher import WsCryptoCopyTrader
from asgiref.sync import async_to_sync

from celery import Celery
from lib.GetDotEnv import REDIS, TOKEN
from lib.Logger import LOGGER
from lib.Snipper import CryptoArbitrageBot
from models.UserModel import UserWallet

app = Celery("tasks", broker=REDIS, backend=REDIS)
# app.conf.update(
#     task_serializer='json',
#     accept_content=['json'],
#     result_serializer='json',
#     timezone='America/New_York',
#     enable_utc=True,
# )

@app.task
def copytrade_task(watcher_private_key: str, target_address: str, chat_id: int):
    async_to_sync(run_copytrade_task)(watcher_private_key, target_address, chat_id)

async def run_copytrade_task(watcher_private_key: str, target_address: str, chat_id: int):
    wallet: UserWallet = await WalletData.get_wallet_by_id(chat_id)
    network: Network = [
            network
            for network in Networks
            if network.name.lower() == wallet.chain_name.lower()
    ][0]
    trader = WsCryptoCopyTrader(chat_id, network.sn)
    await trader.copytrade(watcher_private_key, target_address, network.id)

@app.task
def snipe_task(chat_id: int, token_mint: str = None):
    async_to_sync(run_sniper)(chat_id, token_mint)

async def run_sniper(chat_id: int, token_mint: str = None):
    sniper = CryptoArbitrageBot(chat_id, token_mint)
    await sniper.run()
