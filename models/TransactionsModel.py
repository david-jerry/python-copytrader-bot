from datetime import date
from typing import Optional, Union
from pydantic_redis import Model

class UserTransactions(Model):
    _primary_key_field: str = "user_id"
    user_id: int  # Foreign key referencing User.id
    transaction_id: str  # Unique identifier for the transaction
    transaction_type: str
    token: str  # Token symbol (e.g., BTC, ETH)
    chain: str  # Blockchain name (e.g., Ethereum, Binance Smart Chain)
    chain_id: int  # Blockchain ID (optional)
    amount: Optional[float]  # Transaction amount (can be decimal or float)
    amount_usd: Optional[float]  # Transaction amount in USD (optional)
    gas_fee: Optional[float]  # Gas fee for the transaction (optional)
    tx_hash: Optional[str]  # Transaction hash on the blockchain (optional)
    created: date = date.today()
