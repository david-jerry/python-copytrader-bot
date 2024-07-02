from datetime import datetime
from typing import Optional
import requests

from data.Queries import CoinData
from lib.GetDotEnv import ETHERSCAN_API
from lib.Logger import LOGGER
from lib.Types import TokenDecimals, TokenInfo
from models.CoinsModel import Coins, CurrentPrice, MarketCap, Platform


class TokenMetadata:
    def __init__(self) -> None:
        pass

    async def currency_amount(self, token_id: str) -> Optional[float]:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": token_id, "vs_currencies": "usd"}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            LOGGER.info(data)
            price = data[token_id]["usd"]
            LOGGER.info(price)
            return float(price)
        else:
            LOGGER.info(response.json())
            return None

    async def get_token_id(self, symbol: str) -> Optional[Coins]:
        """
        Get the CoinGecko token ID for a given token symbol.

        Args:
            symbol (str): The token symbol to search for.

        Returns:
            Optional[str]: The CoinGecko token ID if found, None otherwise.

        Example:
            token_id = await ETHWallet.get_token_id("xrp")
            print(token_id)  # Output: "ripple"
        """
        api_url = "https://api.coingecko.com/api/v3/search"
        params = {"query": symbol}
        stored_token: Optional[Coins] = await CoinData.get_coin_by_symbol(symbol)

        if stored_token is not None:
            LOGGER.debug(f"Stored: {stored_token}")
            LOGGER.debug(f"Stored Platforms: {stored_token.platforms}")

            if stored_token.platforms.ethereum is not None:
                return stored_token

        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            for coin in data.get("coins", []):
                if coin["symbol"].lower() == symbol.lower():
                    token_id: str = coin["id"]
                    LOGGER.info(f"Found token ID: {token_id} for symbol: {symbol}")
                    return await self.get_token_details(token_id)

            LOGGER.info(f"No token ID found for symbol: {symbol}")
            return None
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"An error occurred: {e}")
            return None

    async def get_token_details(self, token_id: str, symbol: str) -> Optional[Coins]:
        """
        Fetches detailed information about a token from CoinGecko and potentially a database.

        This function retrieves information about a token using the provided `token_id`
        and attempts to fetch additional details by symbol if `token_id` is not found.

        Args:
            token_id (str): The CoinGecko ID of the token (preferred).
            symbol (str): The token symbol (used if token_id is not available).

        Returns:
            Optional[Coins]: A Coins object containing detailed information if found, None otherwise.

            The Coins object may include data like market cap, current price, total supply,
            description, platforms supported, and potentially ABI (if available).
        """
        api_url = f"https://api.coingecko.com/api/v3/coins/{token_id}"

        try:
            coin_data: Optional[Coins] = await CoinData.get_coin_by_symbol(symbol)

            if coin_data is not None:
                return coin_data

            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            total_volume = (
                data.get("market_data", {}).get("total_volume", {}).get("usd")
            )
            description = data.get("description", {}).get("en")
            image_link = data.get("image", {}).get("large")
            coin_id = data.get("id")
            symbol = data.get("symbol")
            name = data.get("name")

            # Extract necessary information
            platforms = Platform(
                symbol=symbol,
                ethereum=data.get("platforms", {}).get("ethereum"),
                polygon=data.get("platforms", {}).get("polygon-pos"),
                binance_smart_chain=data.get("platforms", {}).get(
                    "binance-smart-chain"
                ),
                solana=data.get("platforms", {}).get("solana"),
            )

            if platforms.ethereum:
                # Fetch the ABI using Etherscan API
                contract_address = (
                    platforms.ethereum
                )  # Example: using Ethereum platform
                abi = None
                if contract_address:
                    abi_url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={ETHERSCAN_API}"
                    abi_response = requests.get(abi_url)
                    if abi_response.status_code == 200:
                        abi_data = abi_response.json()
                        if abi_data["status"] == "1":
                            abi = abi_data["result"]
                        else:
                            LOGGER.error(f"Failed to fetch ABI: {abi_data['result']}")

            market_cap = MarketCap(
                symbol=symbol,
                USD=data.get("market_data", {}).get("market_cap", {}).get("usd"),
                AUD=data.get("market_data", {}).get("market_cap", {}).get("aud"),
                GBP=data.get("market_data", {}).get("market_cap", {}).get("gbp"),
                NGN=data.get("market_data", {}).get("market_cap", {}).get("ngn"),
                JPY=data.get("market_data", {}).get("market_cap", {}).get("jpy"),
                CAD=data.get("market_data", {}).get("market_cap", {}).get("cad"),
            )

            current_price = CurrentPrice(
                symbol=symbol,
                USD=data.get("market_data", {}).get("current_price", {}).get("usd"),
                AUD=data.get("market_data", {}).get("current_price", {}).get("aud"),
                GBP=data.get("market_data", {}).get("current_price", {}).get("gbp"),
                NGN=data.get("market_data", {}).get("current_price", {}).get("ngn"),
                JPY=data.get("market_data", {}).get("current_price", {}).get("jpy"),
                CAD=data.get("market_data", {}).get("current_price", {}).get("cad"),
            )

            total_supply = data.get("market_data", {}).get("total_supply", {})

            token_details = Coins(
                id=coin_id,
                symbol=symbol,
                name=name,
                platforms=platforms,
                market_cap=market_cap,
                current_price=current_price,
                total_volume=total_volume,
                description=description,
                total_supply=total_supply,
                abi=abi,
                image_link=image_link,
                last_updated=datetime.now(),
            )

            LOGGER.info(f"Token details for {token_id}: {token_details}")
            await CoinData.create_coin(token_details)
            return token_details
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"An error occurred: {e}")
            return None

    async def get_token_symbol_by_contract(
        self, contract_address: str, platform: str = "ethereum"
    ) -> Optional[TokenInfo]:
        """
            Fetches the symbol of a token on a specific platform using CoinGecko API.

        This function retrieves information about a token on the specified `platform` (e.g., Ethereum)
        using the provided `contract_address`. It utilizes the CoinGecko API and returns a dictionary
        containing details about the token, if successful.

        Args:
            contract_address (str): The contract address of the token on the chosen platform.
            platform (str, optional): The name of the platform where the token resides (defaults to "ethereum").

        Returns:
            Optional[TokenInfo]: A dictionary containing token information (e.g., "id", "symbol") if found, None otherwise.

            The exact structure of the returned dictionary depends on the CoinGecko API response.
            Refer to the CoinGecko API documentation for details: https://www.coingecko.com/en/api
        """
        c_address = self.convert_to_checksum(contract_address)
        api_url = (
            f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{c_address}"
        )

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            id = data.get("id")
            symbol = data.get("symbol")
            eth_decimal = data.get("detail_platforms", {}).get("ethereum")
            sol_decimal = data.get("detail_platforms", {}).get("solana")
            avl_decimal = data.get("detail_platforms", {}).get("avalanche")
            token_details: TokenInfo = TokenInfo(
                id=id,
                symbol=symbol,
                decimal=TokenDecimals(ethereum=eth_decimal, avalanche=sol_decimal, solana=avl_decimal),
            )
            return token_details
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"An error occurred: {e}")
            return None
