from datetime import datetime, date, timedelta
import json
from typing import List, Optional

from lib.GetDotEnv import REDIS, REDIS_DB, REDIS_HOST, REDIS_POST, REDIS_PASSWORD
from models.CoinsModel import Coins, CurrentPrice, MarketCap, Platform
from models.CopyTradeModel import UserCopyTradesTasks as UserCopyTrades, UserCopyTradesTasks
from models.TransactionsModel import UserTransactions
from models.UserModel import User, UserWallet
from models.Presets import Presets

from pydantic_redis import RedisConfig, Store
from lib.DefinedFICalls import DefinedFiCalls
from lib.Logger import LOGGER

from redis_om.model import NotFoundError

UserDataType = dict[str, Optional[int | str | bool | float | datetime]]
DataType = dict[str, Optional[int | str | bool | float | datetime | dict]]


class UserData:
    def __init__(self) -> None:
        store = Store(
            name="users",
            redis_config=RedisConfig(host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB, password=REDIS_PASSWORD),
            life_span_in_seconds=None,
        )
        store.register_model(User)

    async def get_user_by_id(self, user_id: str) -> User | None:
        data = User.select(ids=[user_id])
        return data[0] if data is not None else None

    async def create_user(self, data: UserDataType) -> User | None:
        try:
            user = User(**data)
            User.insert(data=user)
            return await self.get_user_by_id(user.user_id)
        except Exception as e:
            LOGGER.error(f"Create Error: {e}")
            return None

    async def update_user(self, user_id: str, data: UserDataType) -> User | None:
        try:
            User.update(_id=user_id, data=data)
            return await self.get_user_by_id(user_id)
        except Exception as e:
            LOGGER.error(f"Update Error: {e}")
            return None

    async def delete_user(self, user_id: str):
        try:
            User.delete(ids=[user_id])
            return None
        except Exception as e:
            LOGGER.error(f"Delete Error: {e}")
            return None


class WalletData:
    def __init__(self) -> None:
        store = Store(
            name="wallets",
            redis_config=RedisConfig(host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB, password=REDIS_PASSWORD),
            life_span_in_seconds=None,
        )
        store.register_model(UserWallet)

    async def get_wallet_by_id(self, user_id: str) -> UserWallet | None:
        data = UserWallet.select(ids=[user_id])
        return data[0] if data is not None else None

    async def create_wallet(self, data: UserDataType) -> UserWallet | None:
        try:
            wal = await self.get_wallet_by_id(data.get("user_id"))
            if wal is None:
                wallet = UserWallet(**data)
                UserWallet.insert(data=wallet)
                return await self.get_wallet_by_id(wallet.user_id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Error: {e}")
            return None

    async def update_wallet(
        self, user_id: str, data: UserDataType
    ) -> UserWallet | None:
        try:
            UserWallet.update(_id=user_id, data=data)
            return await self.get_wallet_by_id(user_id)
        except Exception as e:
            LOGGER.error(f"Update Error: {e}")
            return None

    async def delete_wallet(self, user_id: str):
        try:
            UserWallet.delete(ids=[user_id])
            return None
        except Exception as e:
            LOGGER.error(f"Delete Error: {e}")
            return None


class CoinData:
    def __init__(self) -> None:
        store = Store(
            name="coins",
            redis_config=RedisConfig(host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB, password=REDIS_PASSWORD),
            life_span_in_seconds=60 * 60 * 24 * 2,
        )
        store.register_model(Coins)
        store.register_model(Platform)
        store.register_model(MarketCap)
        store.register_model(CurrentPrice)

    async def get_coin_by_symbol(self, symbol: str) -> Coins | None:
        data = Coins.select(ids=[symbol])
        return data[0] if data is not None else None

    async def get_all_coins(self) -> Coins | None:
        data = Coins.select()
        return data if data is not None else []

    async def create_coin(self, data: Coins) -> Coins | None:
        try:
            coin = await self.get_coin_by_symbol(data.symbol)
            if coin is None:
                Coins.insert(data=data)
                return await self.get_coin_by_symbol(data.symbol)
            return None
        except Exception as e:
            LOGGER.error(f"Create Error: {e}")
            return None

    async def update_coin(self, symbol: str, data: DataType) -> Coins | None:
        try:
            Coins.update(_id=symbol, data={**data})
            return await self.get_coin_by_symbol(symbol)
        except Exception as e:
            LOGGER.error(f"Update Error: {e}")
            return None

class PresetsData:
    def __init__(self) -> None:
        store = Store(
            name="presets",
            redis_config=RedisConfig(host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB, password=REDIS_PASSWORD),
            # life_span_in_seconds=60 * 60 * 24 * 2,
        )
        store.register_model(Presets)


    async def get_presets_by_id(self, id: str) -> Presets | None:
        data = Presets.select(ids=[id])
        return data[0] if data is not None else None

    async def get_all_presets(self) -> Presets | None:
        data = Presets.select()
        return data if data is not None else []

    async def create_presets(self, data: Presets) -> Presets | None:
        try:
            preset = await self.get_presets_by_id(data.id)
            if preset is None:
                Presets.insert(data=data)
                return await self.get_presets_by_id(data.id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Error: {e}")
            return None

    async def update_presets(self, id: str, data: DataType) -> Presets | None:
        try:
            Presets.update(_id=id, data={**data})
            return await self.get_presets_by_id(id)
        except Exception as e:
            LOGGER.error(f"Update Error: {e}")
            return None


class UserCopyTradesTasksData:
    def __init__(self) -> None:
        store = Store(
            name="copy_trades",
            redis_config=RedisConfig(host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB, password=REDIS_PASSWORD),
        )
        store.register_model(UserCopyTradesTasks)


    async def get_copy_trade_tasks_by_id(self, id: str) -> UserCopyTradesTasks | None:
        data = UserCopyTradesTasks.select(ids=[id])
        return data[0] if data is not None else None

    async def get_all_copy_trade_tasks(self) -> UserCopyTradesTasks | None:
        data = UserCopyTradesTasks.select()
        return data if data is not None else []

    async def create_copy_trade_tasks(self, data: UserCopyTradesTasks) -> UserCopyTradesTasks | None:
        try:
            preset = await self.get_copy_trade_tasks_by_id(data.id)
            if preset is None:
                UserCopyTradesTasks.insert(data=data)
                return await self.get_copy_trade_tasks_by_id(data.id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Error: {e}")
            return None

    async def update_copy_trade_tasks(self, id: str, data: DataType) -> UserCopyTradesTasks | None:
        try:
            UserCopyTradesTasks.update(_id=id, data={**data})
            return await self.get_copy_trade_tasks_by_id(id)
        except Exception as e:
            LOGGER.error(f"Update Error: {e}")
            return None

UserData = UserData()
CoinData = CoinData()
WalletData = WalletData()
PresetsData = PresetsData()
UserCopyTradesTasksData = UserCopyTradesTasksData()
