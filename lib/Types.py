from collections import namedtuple
from typing import Optional


class TokenDecimals:
    """
    Represents platform-specific decimal places for a token.
    """

    def __init__(self, ethereum: Optional[int] = None, avalanche: Optional[int] = None, solana: Optional[int] = None):
        """
        Initializes a TokenDecimals object.

        Args:
            ethereum (Optional[int], optional): Decimal places for Ethereum. Defaults to None.
            avalanche (Optional[int], optional): Decimal places for Avalanche. Defaults to None.
            solana (Optional[int], optional): Decimal places for Solana. Defaults to None.
        """

        self.ethereum = ethereum
        self.avalanche = avalanche
        self.solana = solana


class TokenInfo:
    """
    Represents detailed information about a token.
    """

    def __init__(self, id: str, symbol: str, decimal: Optional[TokenDecimals] = None):
        """
        Initializes a TokenInfo object.

        Args:
            id (str): The ID of the token.
            symbol (str): The symbol of the token.
            decimal (Optional[TokenDecimals], optional): A TokenDecimals object containing platform-specific decimals. Defaults to None.
        """

        self.id = id
        self.symbol = symbol
        self.decimal = decimal
