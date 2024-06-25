from datetime import datetime
from typing import Optional
from typing import List
from pydantic_redis import Model


class Platform(Model):
    _primary_key_field: str = "symbol"
    symbol: str
    ethereum: Optional[str]
    polygon: Optional[str]
    binance_smart_chain: Optional[str]
    solana: Optional[str]


class MarketCap(Model):
    _primary_key_field: str = "symbol"
    symbol: str
    USD: Optional[float]
    AUD: Optional[float]
    GBP: Optional[float]
    NGN: Optional[float]
    JPY: Optional[float]
    CAD: Optional[float]


class CurrentPrice(Model):
    _primary_key_field: str = "symbol"
    symbol: str
    USD: Optional[float]
    AUD: Optional[float]
    GBP: Optional[float]
    NGN: Optional[float]
    JPY: Optional[float]
    CAD: Optional[float]


class Coins(Model):
    _primary_key_field: str = "symbol"
    id: str
    symbol: str
    name: str
    platforms: Platform
    market_cap: MarketCap
    current_price: CurrentPrice
    total_volume: Optional[float]
    total_supply: Optional[float]
    description: Optional[str]
    image_link: Optional[str]
    abi: Optional[str]
    last_updated: datetime = datetime.now()

    class Config:
        arbitrary_types_allowed = True
