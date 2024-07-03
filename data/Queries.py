from datetime import datetime, date, timedelta
import json
from typing import List, Optional

from lib.GetDotEnv import DEBUG, REDIS, REDIS_DB, REDIS_HOST, REDIS_POST, REDIS_PASSWORD
from models.CoinsModel import Coins, CurrentPrice, MarketCap, Platform
from models.CopyTradeModel import (
    UserCopyTradesTasks as UserCopyTrades,
    UserCopyTradesTasks,
)
from models.SnipeTradeModel import SnipeTrade
from models.TransactionsModel import UserTransactions
from models.UserModel import User, UserWallet
from models.Presets import Presets

from pydantic_redis import RedisConfig, Store
from lib.DefinedFICalls import DefinedFiCalls
from lib.Logger import LOGGER

from redis_om.model import NotFoundError

UserDataType = dict[str, Optional[int | str | bool | float | datetime]]
DataType = dict[str, Optional[int | str | bool | float | datetime | dict]]

rConfigProduction = RedisConfig(
    host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB, password=REDIS_PASSWORD
)

rConfigLocal = RedisConfig(
    host=REDIS_HOST, port=REDIS_POST, db=REDIS_DB
)

class UserData:
    """
    This class handles user data access and manipulation in Redis.

    It uses pydantic-redis to interact with the 'users' Redis store
    configured with connection details and model registration.
    """

    def __init__(self) -> None:
        self.store = Store(
            name="users",
            redis_config=rConfigProduction,
            life_span_in_seconds=None,
        )
        self.store.register_model(User)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """
        Retrieves a user object from Redis based on the provided user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            User | None: A User object if found, otherwise None.

        Raises:
            Exception: Any exceptions encountered during retrieval.
        """

        try:
            data = User.select(ids=[user_id])
            return data[0] if data is not None else None
        except Exception as e:
            LOGGER.error(f"Get User Error: user_id={user_id}, Error: {e}")
            return None

    async def create_user(self, data: User) -> User | None:
        """
        Creates a new user in Redis using the provided User data.

        Args:
            data (User): A User object containing user information.

        Returns:
            User | None: The newly created User object if successful, otherwise None.

        Raises:
            Exception: Any exceptions encountered during creation.
        """

        try:
            User.insert(data=data)
            return await self.get_user_by_id(data.user_id)
        except Exception as e:
            LOGGER.error(f"Create User Error: {e}")
            return None

    async def update_user(self, user_id: str, data: UserDataType) -> User | None:
        """
        Updates an existing user in Redis based on the user ID and provided data.

        Args:
            user_id (str): The unique identifier of the user.
            data (UserDataType): A dictionary containing user data to update.

        Returns:
            User | None: The updated User object if successful, otherwise None.

        Raises:
            Exception: Any exceptions encountered during update.
        """

        try:
            User.update(_id=user_id, data=data)
            return await self.get_user_by_id(user_id)
        except Exception as e:
            LOGGER.error(f"Update User Error: user_id={user_id}, Error: {e}")
            return None

    async def delete_user(self, user_id: str):
        """
        Deletes a user from Redis based on the provided user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Raises:
            Exception: Any exceptions encountered during deletion.
        """

        try:
            User.delete(ids=[user_id])
        except Exception as e:
            LOGGER.error(f"Delete User Error: user_id={user_id}, Error: {e}")


class WalletData:
    """
    This class handles wallet data access and manipulation in Redis.

    It uses pydantic-redis to interact with the 'wallets' Redis store
    configured with connection details and model registration.
    """

    def __init__(self) -> None:
        self.store = Store(
            name="wallets",
            redis_config=rConfigProduction,
            life_span_in_seconds=None,
        )
        self.store.register_model(UserWallet)

    async def get_wallet_by_id(self, user_id: str) -> UserWallet:
        """
        Retrieves a user's wallet data object from Redis based on the user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            UserWallet: A UserWallet object containing the user's wallet data.

        Raises:
            Exception: Any exceptions encountered during retrieval.
        """

        try:
            data = UserWallet.select(ids=[user_id])
            return data[0] if data is not None else None
        except Exception as e:
            LOGGER.error(f"Get Wallet Error: user_id={user_id}, Error: {e}")
            raise

    async def create_wallet(self, data: UserWallet) -> UserWallet | None:
        """
        Creates a new wallet in Redis for a user using the provided UserWallet data.

        If a wallet already exists for the user, it won't be recreated.

        Args:
            data (UserWallet): A UserWallet object containing wallet information.

        Returns:
            UserWallet | None:
                - The newly created UserWallet object if successful, otherwise None.
                - None if a wallet already exists for the user.

        Raises:
            Exception: Any exceptions encountered during creation.
        """

        try:
            existing_wallet = await self.get_wallet_by_id(data.user_id)
            if existing_wallet is None:
                UserWallet.insert(data=data)
                return await self.get_wallet_by_id(data.user_id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Wallet Error: {e}")
            return None

    async def update_wallet(
        self, user_id: str, data: UserDataType
    ) -> UserWallet | None:
        """
        Updates an existing user's wallet data in Redis based on the user ID and provided data.

        Args:
            user_id (str): The unique identifier of the user.
            data (UserDataType): A dictionary containing wallet data to update.

        Returns:
            UserWallet | None:
                - The updated UserWallet object if successful, otherwise None.
                - None if the update fails.

        Raises:
            Exception: Any exceptions encountered during update.
        """

        try:
            UserWallet.update(_id=user_id, data=data)
            return await self.get_wallet_by_id(user_id)
        except Exception as e:
            LOGGER.error(f"Update Wallet Error: user_id={user_id}, Error: {e}")
            return None

    async def delete_wallet(self, user_id: str):
        """
        Deletes a user's wallet data from Redis based on the provided user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Raises:
            Exception: Any exceptions encountered during deletion.
        """

        try:
            UserWallet.delete(ids=[user_id])
        except Exception as e:
            LOGGER.error(f"Delete Wallet Error: user_id={user_id}, Error: {e}")


class CoinData:
    """
    This class handles coin data access and manipulation in Redis.

    It uses pydantic-redis to interact with the 'coins' Redis store
    configured with connection details and model registration.
    The store holds information about various cryptocurrencies
    including their symbol, platform, market cap, and current price.

    Coin data is cached for 2 days (48 hours) to improve performance
    by reducing frequent calls to external APIs.
    """

    def __init__(self) -> None:
        self.store = Store(
            name="coins",
            redis_config=rConfigProduction,
            life_span_in_seconds=60 * 60 * 24 * 2,  # Cache data for 2 days
        )
        self.store.register_model(Coins)
        self.store.register_model(Platform)
        self.store.register_model(MarketCap)
        self.store.register_model(CurrentPrice)

    async def get_coin_by_symbol(self, symbol: str) -> Coins | None:
        """
        Retrieves a coin object from Redis based on the provided coin symbol.

        Args:
            symbol (str): The unique symbol of the cryptocurrency (e.g., BTC, ETH).

        Returns:
            Coins | None:
                - A Coins object containing coin information if found, otherwise None.
                - None if the coin data is not found in Redis.
        """

        try:
            data = Coins.select(ids=[symbol])
            return data[0] if data is not None else None
        except Exception as e:
            LOGGER.error(f"Get Coin Error: symbol={symbol}, Error: {e}")
            return None

    async def get_all_coins(self) -> Coins | None:
        """
        Retrieves all coin objects currently stored in Redis.

        Returns:
            Coins | None:
                - A list of Coins objects representing all coins,
                  otherwise an empty list if no coins are found.
        """

        try:
            data = Coins.select()
            return data if data is not None else []
        except Exception as e:
            LOGGER.error(f"Get All Coins Error: Error: {e}")
            return None

    async def create_coin(self, data: Coins) -> Coins | None:
        """
        Creates a new coin entry in Redis using the provided Coins data.

        If a coin with the same symbol already exists, it won't be recreated.

        Args:
            data (Coins): A Coins object containing coin information.

        Returns:
            Coins | None:
                - The newly created Coins object if successful, otherwise None.
                - None if a coin with the same symbol already exists.

        Raises:
            Exception: Any exceptions encountered during creation.
        """

        try:
            existing_coin = await self.get_coin_by_symbol(data.symbol)
            if existing_coin is None:
                Coins.insert(data=data)
                return await self.get_coin_by_symbol(data.symbol)
            return existing_coin
        except Exception as e:
            LOGGER.error(f"Create Coin Error: {e}")
            return None

    async def update_coin(self, symbol: str, data: DataType) -> Coins | None:
        """
        Updates an existing coin's data in Redis based on the symbol and provided data.

        Args:
            symbol (str): The unique symbol of the cryptocurrency.
            data (DataType): A dictionary containing coin data to update.

        Returns:
            Coins | None:
                - The updated Coins object if successful, otherwise None.
                - None if the update fails.

        Raises:
            Exception: Any exceptions encountered during update.
        """

        try:
            Coins.update(_id=symbol, data={**data})
            return await self.get_coin_by_symbol(symbol)
        except Exception as e:
            LOGGER.error(f"Update Coin Error: symbol={symbol}, Error: {e}")
            return None


class PresetsData:
    """
    This class handles preset data access and manipulation in Redis.

    It uses pydantic-redis to interact with the 'presets' Redis store
    configured with connection details and model registration.
    Presets likely represent configurations or settings for something
    within the system.

    There is currently no set cache expiration for presets.
    """

    def __init__(self) -> None:
        self.store = Store(
            name="presets",
            redis_config=rConfigProduction,
            # life_span_in_seconds=None,  # No cache expiration set
        )
        self.store.register_model(Presets)

    async def get_presets_by_id(self, id: str) -> Presets | None:
        """
        Retrieves a preset object from Redis based on the provided preset ID.

        Args:
            id (str): The unique identifier of the preset.

        Returns:
            Presets | None:
                - A Presets object containing preset information if found, otherwise None.
                - None if the preset data is not found in Redis.
        """

        try:
            data = Presets.select(ids=[id])
            return data[0] if data is not None else None
        except Exception as e:
            LOGGER.error(f"Get Preset Error: id={id}, Error: {e}")
            return None

    async def get_all_presets(self) -> Presets | None:
        """
        Retrieves all preset objects currently stored in Redis.

        Returns:
            Presets | None:
                - A list of Presets objects representing all presets,
                  otherwise an empty list if no presets are found.
        """

        try:
            data = Presets.select()
            return data if data is not None else []
        except Exception as e:
            LOGGER.error(f"Get All Presets Error: Error: {e}")
            return None

    async def create_presets(self, data: Presets) -> Presets | None:
        """
        Creates a new preset entry in Redis using the provided Presets data.

        If a preset with the same ID already exists, it won't be recreated.

        Args:
            data (Presets): A Presets object containing preset information.

        Returns:
            Presets | None:
                - The newly created Presets object if successful, otherwise None.
                - None if a preset with the same ID already exists.

        Raises:
            Exception: Any exceptions encountered during creation.
        """

        try:
            existing_preset = await self.get_presets_by_id(data.id)
            if existing_preset is None:
                Presets.insert(data=data)
                return await self.get_presets_by_id(data.id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Preset Error: {e}")
            return None

    async def update_presets(self, id: str, data: DataType) -> Presets | None:
        """
        Updates an existing preset's data in Redis based on the ID and provided data.

        Args:
            id (str): The unique identifier of the preset.
            data (DataType): A dictionary containing preset data to update.

        Returns:
            Presets | None:
                - The updated Presets object if successful, otherwise None.
                - None if the update fails.

        Raises:
            Exception: Any exceptions encountered during update.
        """

        try:
            Presets.update(_id=id, data={**data})
            return await self.get_presets_by_id(id)
        except Exception as e:
            LOGGER.error(f"Update Preset Error: id={id}, Error: {e}")
            return None


class UserCopyTradesTasksData:
    """
    This class handles user copy trade tasks data access and manipulation in Redis.

    It uses pydantic-redis to interact with the 'copy_trades' Redis store
    configured with connection details and model registration.
    This store likely holds information about user-defined tasks
    related to copy trading functionalities.

    The model used for storing this data is `UserCopyTradesTasks`.
    """

    def __init__(self) -> None:
        self.store = Store(
            name="copy_trades",
            redis_config=rConfigProduction,
        )
        self.store.register_model(UserCopyTradesTasks)

    async def get_copy_trade_tasks_by_id(self, id: str) -> UserCopyTradesTasks | None:
        """
        Retrieves a user copy trade task object from Redis based on the provided ID.

        Args:
            id (str): The unique identifier of the copy trade task.

        Returns:
            UserCopyTradesTasks | None:
                - A UserCopyTradesTasks object containing task information if found,
                  otherwise None.
                - None if the task data is not found in Redis.
        """

        try:
            data = UserCopyTradesTasks.select(ids=[id])
            return data[0] if data is not None else None
        except Exception as e:
            LOGGER.error(f"Get Copy Trade Task Error: id={id}, Error: {e}")
            return None

    async def get_all_copy_trade_tasks(self) -> UserCopyTradesTasks | None:
        """
        Retrieves all user copy trade task objects currently stored in Redis.

        Returns:
            UserCopyTradesTasks | None:
                - A list of UserCopyTradesTasks objects representing all tasks,
                  otherwise an empty list if no tasks are found.
        """

        try:
            data = UserCopyTradesTasks.select()
            return data if data is not None else []
        except Exception as e:
            LOGGER.error(f"Get All Copy Trade Tasks Error: Error: {e}")
            return None

    async def create_copy_trade_tasks(
        self, data: UserCopyTradesTasks
    ) -> UserCopyTradesTasks | None:
        """
        Creates a new user copy trade task entry in Redis using the provided data.

        If a task with the same ID already exists, it won't be recreated.

        Args:
            data (UserCopyTradesTasks): A UserCopyTradesTasks object containing task data.

        Returns:
            UserCopyTradesTasks | None:
                - The newly created UserCopyTradesTasks object if successful, otherwise None.
                - None if a task with the same ID already exists.

        Raises:
            Exception: Any exceptions encountered during creation.
        """

        try:
            existing_task = await self.get_copy_trade_tasks_by_id(data.id)
            if existing_task is None:
                UserCopyTradesTasks.insert(data=data)
                return await self.get_copy_trade_tasks_by_id(data.id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Copy Trade Task Error: {e}")
            return None

    async def update_copy_trade_tasks(
        self, id: str, data: DataType
    ) -> UserCopyTradesTasks | None:
        """
        Updates an existing user copy trade task's data in Redis based on the ID and provided data.

        Args:
            id (str): The unique identifier of the copy trade task.
            data (DataType): A dictionary containing task data to update.

        Returns:
            UserCopyTradesTasks | None:
                - The updated UserCopyTradesTasks object if successful, otherwise None.
                - None if the update fails.

        Raises:
            Exception: Any exceptions encountered during update.
        """

        try:
            UserCopyTradesTasks.update(_id=id, data={**data})
            return await self.get_copy_trade_tasks_by_id(id)
        except Exception as e:
            LOGGER.error(f"Update Copy Trade Task Error: id={id}, Error: {e}")


class SnipeTradeData:
    """
    This class handles user copy trade tasks data access and manipulation in Redis.

    It uses pydantic-redis to interact with the 'copy_trades' Redis store
    configured with connection details and model registration.
    This store likely holds information about user-defined tasks
    related to copy trading functionalities.

    The model used for storing this data is `UserCopyTradesTasks`.
    """

    def __init__(self) -> None:
        self.store = Store(
            name="snipe_trades",
            redis_config=rConfigProduction,
        )
        self.store.register_model(SnipeTrade)

    async def get_sniped_token_by_id(self, id: str) -> SnipeTrade | None:
        """
        Retrieves a user copy trade task object from Redis based on the provided ID.

        Args:
            id (str): The unique identifier of the copy trade task.

        Returns:
            UserCopyTradesTasks | None:
                - A UserCopyTradesTasks object containing task information if found,
                  otherwise None.
                - None if the task data is not found in Redis.
        """

        try:
            data = SnipeTrade.select(ids=[id])
            return data[0] if data is not None else None
        except Exception as e:
            LOGGER.error(f"Get Snipe Trade Error: id={id}, Error: {e}")
            return None

    async def get_all_sniped_tokens(self) -> List[SnipeTrade] | None:
        """
        Retrieves all user copy trade task objects currently stored in Redis.

        Returns:
            UserCopyTradesTasks | None:
                - A list of UserCopyTradesTasks objects representing all tasks,
                  otherwise an empty list if no tasks are found.
        """

        try:
            data = SnipeTrade.select()
            return data if data is not None else []
        except Exception as e:
            LOGGER.error(f"Get All Snipped tokens Error: Error: {e}")
            return None

    async def create_snipped_token(
        self, data: SnipeTrade
    ) -> SnipeTrade | None:
        """
        Creates a new user copy trade task entry in Redis using the provided data.

        If a task with the same ID already exists, it won't be recreated.

        Args:
            data (UserCopyTradesTasks): A UserCopyTradesTasks object containing task data.

        Returns:
            UserCopyTradesTasks | None:
                - The newly created UserCopyTradesTasks object if successful, otherwise None.
                - None if a task with the same ID already exists.

        Raises:
            Exception: Any exceptions encountered during creation.
        """

        try:
            existing_task = await self.get_copy_trade_tasks_by_id(data.id)
            if existing_task is None:
                SnipeTrade.insert(data=data)
                return await self.get_copy_trade_tasks_by_id(data.id)
            return None
        except Exception as e:
            LOGGER.error(f"Create Copy Trade Task Error: {e}")
            return None

    async def update_snipped_token(
        self, id: str, data: DataType
    ) -> SnipeTrade | None:
        """
        Updates an existing user copy trade task's data in Redis based on the ID and provided data.

        Args:
            id (str): The unique identifier of the copy trade task.
            data (DataType): A dictionary containing task data to update.

        Returns:
            UserCopyTradesTasks | None:
                - The updated UserCopyTradesTasks object if successful, otherwise None.
                - None if the update fails.

        Raises:
            Exception: Any exceptions encountered during update.
        """

        try:
            SnipeTrade.update(_id=id, data={**data})
            return await self.get_sniped_token_by_id(id)
        except Exception as e:
            LOGGER.error(f"Update Copy Trade Task Error: id={id}, Error: {e}")


UserData = UserData()
CoinData = CoinData()
WalletData = WalletData()
PresetsData = PresetsData()
UserCopyTradesTasksData = UserCopyTradesTasksData()
SnipeTradeData = SnipeTradeData()
