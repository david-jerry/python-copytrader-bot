from typing import Optional, List
from pydantic_redis import Model


class UserCopyTradesTasks(Model):
    _primary_key_field: str = "id"
    id: str
    user_id: int  # Foreign key referencing User.id
    copy_trade_id: str  # Unique identifier for the copy trade
    watcher_address: str  # ID of the user whose trade is being copied
    status: int = 1

