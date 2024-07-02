import asyncio
import time
from typing import Optional
import base58
import pandas as pd
import aiohttp
import json

from eth_account import Account
from data.Networks import Network, Networks
from data.Queries import PresetsData, SnipeTradeData, WalletData
from lib.GetDotEnv import COINMARKETCAP_API, TOKEN
from lib.Logger import LOGGER
from lib.TokenMetadata import TokenMetadata
from lib.WalletClass import ETHWallet, SolanaWallet
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair  # type: ignore

from models.Presets import Presets
from models.SnipeTradeModel import SnipeTrade
from models.UserModel import UserWallet  # type: ignore

from telegram import Bot
from telegram_commands.commands.Buttons import setKeyboard, auth_start_buttons

bot = Bot(TOKEN)

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
SOL = "So11111111111111111111111111111111111111112"


class CryptoArbitrageBot:
    """
    A class used to interact with the CoinMarketCap API to fetch and analyze cryptocurrency tokens.

    Attributes:
        cmc_headers (dict): Headers for CoinMarketCap API authentication.
        cmc_url (str): URL endpoint for fetching cryptocurrency listings from CoinMarketCap.
    """

    def __init__(self, user_id: str, token_mint: Optional[str] = None):
        """
        Initializes the CryptoArbitrageBot with the necessary headers and URL for the CoinMarketCap API.
        """
        self.user_id = user_id
        self.bot = bot
        self.token_mint = token_mint
        self.cmc_headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API}
        self.cmc_url = (
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        )

    async def fetch_listings(self):
        """
        Fetches the latest cryptocurrency token listings from CoinMarketCap.

        Makes an API call to fetch data on the latest cryptocurrency token listings, converts the data to a pandas DataFrame,
        identifies the platform for each token, filters tokens based on specific platforms, and determines the best token on each platform.

        Returns:
            dict: A dictionary containing the best tokens on each platform, with their details including platform name,
                  network ID, contract address, price in USD, token name, and token ID.
        """
        params = {
            "start": 1,
            "limit": 200,
            "sort": "date_added",
            "cryptocurrency_type": "tokens",
            "convert": "USD",
            "aux": "circulating_supply,total_supply,market_cap_by_total_supply,volume_24h_reported,volume_7d,volume_7d_reported,volume_30d,volume_30d_reported,is_market_cap_included_in_calc,date_added,tags,platform",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.cmc_url, headers=self.cmc_headers, params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()

        # Convert data to a pandas DataFrame
        df = pd.DataFrame(data["data"])

        def identify_platform(platform_data):
            """
            Identifies the platform name from platform data.

            Args:
                platform_data (dict): The platform data containing the platform name.

            Returns:
                str: The platform name in a readable format. If the platform is not recognized, returns 'Other'.
            """
            if platform_data and platform_data.get("name"):
                platform_name = platform_data["name"].lower()
                if platform_name == "solana":
                    return "Solana"
                elif platform_name == "ethereum":
                    return "Ethereum"
                elif platform_name == "binance smart chain":
                    return "Binance Smart Chain"
                elif platform_name == "polygon":
                    return "Polygon"
                elif platform_name == "avalanche":
                    return "Avalanche"
            return "Other"

        # Add a new 'platform' column based on platform identification logic
        df["platform"] = df["platform"].apply(identify_platform)

        # Filter tokens based on specific platforms
        platforms = [
            "Solana",
            "Ethereum",
            "Binance Smart Chain",
            "Polygon",
            "Avalanche",
        ]
        filtered_df = df[df["platform"].isin(platforms)]

        def determine_best_token(df: pd.DataFrame, platform: str):
            """
            Determines the best token on a specific platform based on various metrics.

            Args:
                df (pd.DataFrame): DataFrame containing the filtered tokens.
                platform (str): The name of the platform to filter tokens by.

            Returns:
                dict: A dictionary containing details of the best token on the platform, including platform name,
                      network ID, contract address, price in USD, token name, and token ID. If no tokens are found,
                      returns None.
            """
            platform_df = df[df["platform"] == platform]
            if platform_df.empty:
                return None

            # Add a new column for the score
            platform_df["score"] = (
                (1 - platform_df["circulating_supply"] / platform_df["total_supply"])
                * 0.4
                + (platform_df["volume_7d"] / platform_df["volume_7d"].max()) * 0.3
                + (
                    platform_df["market_cap_by_total_supply"]
                    / platform_df["circulating_supply"]
                )
                * 0.3
            )

            best_token = platform_df.loc[platform_df["score"].idxmax()]

            return {
                "platform_name": platform,
                "platform_network_id": (
                    best_token["platform"]["id"] if best_token["platform"] else None
                ),
                "platform_contract_address": (
                    best_token["platform"]["token_address"]
                    if best_token["platform"]
                    else None
                ),
                "price_usd": best_token["quote"]["USD"]["price"],
                "token_name": best_token["name"],
                "token_id": best_token["id"],
                "market_cap": best_token["market_cap_by_total_supply"],
                "volume_7d": best_token["volume_7d"],
                "symbol": best_token["symbol"],
            }

        best_tokens = {}
        for platform in platforms:
            best_token = determine_best_token(filtered_df, platform)
            if best_token is not None:
                best_tokens[platform] = best_token

        return best_tokens

    async def buy_token(self, tokens: dict):
        """
        Buys the best token on a given platform using Uniswap V2 or Jupiter API.

        Args:
            platform_name (str): The name of the platform to buy the token from.
            buy_token_symbol (str): The symbol of the token to use for the purchase.
            percentage (float): The percentage of the user's token balance to use for the purchase.
            slippage (float): The slippage tolerance for the swap.
            gas_delta (int): The gas delta value to ensure the transaction is successful.

        Returns:
            dict: A dictionary containing details of the purchase transaction.
        """
        wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(self.user_id)
        presets: Optional[Presets] = await PresetsData.get_presets_by_id(self.user_id)

        if wallet is None:
            return "You have to generate or attach an existing wallet address"

        if presets is None:
            return "you have to configure your presets before executing the trading bot"

        if wallet.chain_name not in tokens:
            return f"No new token found for the {wallet.chain_name} network."

        network: Network = [
            network
            for network in Networks
            if network.name.lower() == wallet.chain_name.lower()
        ][0]

        best_token = tokens[wallet.chain_name]
        price_in_usd = best_token["price_usd"]
        contract_address = best_token["platform_contract_address"]
        token_metadata = await TokenMetadata().get_token_symbol_by_contract(
            contract_address, wallet.chain_name.lower()
        )
        token_id = best_token["token_id"]

        sniped_token: Optional[SnipeTrade] = (
            await SnipeTradeData.get_sniped_token_by_id(
                f"{self.user_id}-{contract_address}"
            )
        )

        if sniped_token is not None:
            return f"You have already purchased {sniped_token.token_name}", sniped_token
        else:
            if wallet.chain_name.lower() == "solana":
                private_key = wallet.sol_sec_key
                pk = Keypair.from_bytes(base58.b58decode(private_key))
                bal = await SolanaWallet().get_balance(pk.pubkey)
                amount_in = bal * presets.balance_tradable  # lamports

                # swapping sol for the token of choice
                transaction_detail = await SolanaWallet().execute_swap(
                    private_key,
                    str(SOL),
                    contract_address,
                    amount_in,
                    (presets.slippage * 100),
                )

                # swapping any other token for the new token, probably USDT for NEWCOIN
                if self.token_mint is not None:
                    pk = Pubkey(self.token_mint)
                    bal = await SolanaWallet().get_token_balance(pk)
                    amount_in = bal * presets.balance_tradable

                    transaction_detail = await SolanaWallet().execute_swap(
                        private_key,
                        self.token_mint,
                        contract_address,
                        amount_in,
                        (presets.slippage * 100),
                    )
            elif wallet.chain_name.lower() != "solana" and self.token_mint is None:
                private_key = wallet.sec_key
                public_address = (
                    wallet.pub_key
                )  # get wallet address by using the private key provided

                eth_wallet = ETHWallet(network.sn)
                bal = (
                    await eth_wallet.get_balance(public_address)
                    * presets.balance_tradable
                )
                bal_wei = await eth_wallet.convert_to_wei(bal)  # wei
                amount_out_min = await ETHWallet.calculate_eth_amount_out(
                    bal_wei, WETH, sniped_token.token_address
                )

                transaction_detail = await eth_wallet.swap_tokens_with_uniswap(
                    private_key, WETH, contract_address, bal_wei, amount_out_min, 5000
                )

                if self.token_mint is not None:
                    token_metadata = await TokenMetadata().get_token_symbol_by_contract(
                        self.token_mint, wallet.chain_name
                    )
                    # if buying the new token with any other evm token
                    bal = (
                        await eth_wallet.get_token_balance(
                            public_address, self.token_mint
                        )
                        * presets.balance_tradable
                    )
                    bal_wei = bal * (10**token_metadata.decimal.ethereum)
                    amount_out_min = await ETHWallet.calculate_eth_amount_out(
                        bal_wei, self.token_mint, contract_address
                    )

                    transaction_detail = await eth_wallet.swap_tokens_with_uniswap(
                        private_key,
                        self.token_mint,
                        contract_address,
                        bal_wei,
                        amount_out_min,
                        5000,
                    )

            data: SnipeTrade = SnipeTrade(
                id=f"{self.user_id}-{contract_address}",
                chain_id=network.id,
                chain_name=network.name,
                decimals=(
                    token_metadata.decimal.ethereum
                    if network.name.lower() != "solana"
                    else token_metadata.decimal.solana
                ),
                token_address=contract_address,
                token_name=token_metadata.symbol,
                token_id=token_id,
                completed_trade=False,
                trading_stratus=False,
                purchased_price_usd=price_in_usd,
                user_id=self.user_id,
            )
            sniped_token: SnipeTrade = SnipeTradeData.create_snipped_token(data=data)
            return transaction_detail, sniped_token

    async def watch_price_change_for_stop_loss_or_take_profit(
        self, sniped_token: SnipeTrade
    ):
        wallet: Optional[UserWallet] = await WalletData.get_wallet_by_id(self.user_id)
        presets: Optional[Presets] = await PresetsData.get_presets_by_id(
            f"{self.user_id}-{wallet.chain_id}"
        )

        while True:
            current_price = await TokenMetadata.currency_amount(sniped_token.token_id)
            take_profit_amount = sniped_token.purchased_price_usd + (
                sniped_token.purchased_price_usd * (presets.snipe_take_profit)
            )
            stop_loss_amount = sniped_token.purchased_price_usd - (
                sniped_token.purchased_price_usd * (presets.snipe_stop_loss)
            )

            if wallet.chain_name.lower() == "solana":
                pk = Pubkey(sniped_token.token_address)
                bal = await SolanaWallet().get_token_balance(pk)
                amount_in = bal  # in lamport
            elif wallet.chain_name.lower() != "solana":
                network: Network = [
                    network
                    for network in Networks
                    if network.name.lower() == wallet.chain_name.lower()
                ][0]
                eth_wallet = ETHWallet(network.sn)
                token_metadata = await TokenMetadata().get_token_symbol_by_contract(
                    sniped_token.token_address, wallet.chain_name
                )
                # if buying the new token with any other evm token
                bal = await eth_wallet.get_token_balance(
                    wallet.pub_key, sniped_token.token_address
                )
                amount_in = bal * (
                    10**token_metadata.decimal.ethereum
                )  # in tokens native unit

            if float(current_price) <= float(stop_loss_amount) or float(
                current_price
            ) >= float(take_profit_amount):
                # sell all the token back to usdt to lessen the losses
                amount_out_min = await ETHWallet.calculate_eth_amount_out(
                    amount_in, sniped_token.token_address, WETH
                )
                transaction_detail = (
                    await eth_wallet.swap_tokens_with_uniswap(
                        wallet.sec_key,
                        sniped_token.token_address,
                        WETH,
                        amount_in,
                        amount_out_min,
                        5000,
                    )
                    if wallet.chain_name.lower() != "solana"
                    else await SolanaWallet().execute_swap(
                        wallet.sec_key,
                        Pubkey(sniped_token.token_address),
                        Pubkey(SOL),
                        amount_in,
                        (presets.slippage * 100),
                    )
                )
                data = {
                    "completed_trade": True,
                    "trading_status": "Traded",
                }
                SnipeTradeData.update_snipped_token(sniped_token.id, data)
                message = f"""
<b>SOLD {sniped_token.token_id}</b>
---------------------------------
AMOUNT: {amount_out_min / (10**sniped_token.decimals)} {sniped_token.token_name}

{transaction_detail}
                """
                # return transaction_detail
                # elif float(current_price) >= float(take_profit_amount):
                #     # sell all the token to usdt to make profit
                #     transaction_detail = await eth_wallet.swap_tokens_with_uniswap(wallet.sec_key, sniped_token.token_address, WETH, amount_in, 5000) if wallet.chain_name.lower() != "solana" else await SolanaWallet().execute_swap(wallet.sec_key, Pubkey(sniped_token.token_address), Pubkey(SOL), amount_in, (presets.slippage * 100))
                await bot.context.send_message(
                    chat_id=self.user_id,
                    text=message,
                    reply_markup=setKeyboard(auth_start_buttons),
                    parse_mode="HTML",
                )
                break
            await asyncio.sleep(300)

    async def run(self):
        best_tokens = await self.fetch_listings()

        while True:
            buy_transaction_detail, sniped_token = await self.buy_token(best_tokens)
            await bot.context.send_message(
                chat_id=self.user_id,
                text=buy_transaction_detail,
                reply_markup=setKeyboard(auth_start_buttons),
                parse_mode="HTML",
            )
            if sniped_token.completed_trade:
                LOGGER.debug(
                    "The specified token has already been traded for profit or does not exist in the wallet."
                )
                await bot.context.send_message(
                    chat_id=self.user_id,
                    text="The specified token has already been traded for profit or does not exist in the wallet.",
                    reply_markup=setKeyboard(auth_start_buttons),
                    parse_mode="HTML",
                )
                break

            LOGGER.debug(f"Watching for {sniped_token.token_name} price change")
            await self.watch_price_change_for_stop_loss_or_take_profit(sniped_token)
            await asyncio.sleep(60 * 3)
