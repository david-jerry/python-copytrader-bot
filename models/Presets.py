from datetime import datetime
from typing import Optional
from pydantic_redis import Model

class Presets(Model):
    _primary_key_field: str = "id"
    id: str
    chain_id: str
    chain_name: Optional[str]
    slippage: Optional[float] = None
    gas_limit: Optional[int] = None
    max_gas_price: Optional[int] = None
    min_circulating_supply: Optional[int] = None
    min_token_supply: Optional[int] = None
    gas_delta: Optional[int] = 1
    snipe_take_profit: Optional[float] = 1.25
    snipe_stop_loss: Optional[float] = 0.15
    balance_tradable: Optional[float] = 0.05
