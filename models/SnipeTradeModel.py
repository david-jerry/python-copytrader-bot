from typing import Optional, List
from pydantic_redis import Model


class SnipeTrade(Model):
    _primary_key_field: str = "id" # user_id + token_address
    id: str
    user_id: int  # Foreign key referencing User.id
    token_address: str  # Unique identifier for the copy trade
    token_name: str  # ID of the user whose trade is being copied
    token_id: str
    chain_name: str  # ID of the user whose trade is being copied
    chain_id: int = 1
    trading_stratus: str = "Trading..."
    completed_trade: bool = False
    decimals: int = 6
    purchased_price_usd: float = 0.00

