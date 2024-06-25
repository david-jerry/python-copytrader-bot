from typing import Optional
from datetime import date
from typing import Tuple, List
from pydantic_redis import RedisConfig, Model, Store


class User(Model):
    _primary_key_field: str = "user_id"
    username: Optional[str]  # Optional for users without usernames
    user_id: int  # Unique identifier for Telegram user
    first_name: Optional[str]
    last_name: Optional[str]
    accepted_agreement: bool = False  # Whether the user has accepted the agreement
    accepted_on: Optional[date] = (
        None  # Optional datetime when the agreement was accepted
    )


class UserWallet(Model):
    _primary_key_field: str = "user_id"
    user_id: str
    pub_key: str
    sec_key: str
    enc_key: Optional[dict] = None
    chain_name: Optional[str] = "Ethereum"
    chain_id: Optional[int] = 1


