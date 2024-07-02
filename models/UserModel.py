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
    user_id: int
    pub_key: Optional[str]
    sec_key: Optional[str]
    mnemonic: Optional[str] = None
    sol_pub_key: Optional[str]
    sol_sec_key: Optional[str]
    sol_mnemonic: Optional[str] = None
    pass_phrase: Optional[str]
    chain_name: Optional[str] = "Ethereum"
    chain_id: Optional[int] = 1


