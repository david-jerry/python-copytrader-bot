import asyncio
from typing import Optional
from telegram import Bot
from web3 import Web3
from solders.pubkey import Pubkey  # type: ignore
from web3.middleware import geth_poa_middleware
from data.Networks import Network, Networks
from data.Queries import PresetsData, WalletData
from lib.GetDotEnv import (
    AVALANCHE_HTTP_URL,
    BSC_HTTP_URL,
    INFURA_HTTP_URL,
    INFURA_WS_URL,
    POLYGON_HTTP_URL,
    TOKEN,
)
from lib.Logger import LOGGER
from lib.TokenMetadata import TokenMetadata
from lib.WalletClass import ETHWallet, SolanaWallet
from models.Presets import Presets
from models.UserModel import UserWallet
from telegram_commands.commands.Buttons import setKeyboard, auth_start_buttons

bot = Bot(TOKEN)


class HttpCryptoCopyTrader:
    """
    Class to watch and copy trades from a target address using HTTP connection.
    """

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(INFURA_HTTP_URL))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if not self.w3.is_connected():
            LOGGER.error("Connection Error")
            raise Exception("Unable to connect to the RPC network")

    async def watch_trades(
        self, watcher_private_key: str, target_address: str, poll_interval: int = 10
    ) -> None:
        """
        Watch for trades from the target_address and mirror them in the watcher wallet.

        Args:
            watcher_private_key (str): The private key of the watcher wallet.
            target_address (str): The address to watch for trades.
            poll_interval (int): Polling interval in seconds. Default is 10 seconds.
        """
        watcher_account = self.w3.eth.account.from_key(watcher_private_key)
        while True:
            try:
                # Filter for new transactions from the target address
                async for tx in self.w3.eth.filter(
                    {"from": target_address}
                ).get_new_entries():
                    tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx["hash"])
                    if (
                        tx_receipt.status == 1
                    ):  # Check if the transaction was successful
                        await self.mirror_trade(tx, watcher_account)
            except Exception as e:
                LOGGER.error(f"Error watching trades: {e}")
            await asyncio.sleep(poll_interval)  # Poll every poll_interval seconds

    async def mirror_trade(self, tx: dict, watcher_account: any) -> None:
        """
        Perform the same trade in the watcher wallet.

        Args:
            tx (dict): The transaction dictionary.
            watcher_account (Web3.eth.account): The watcher account object.
        """
        try:
            # Extract details from the target transaction
            tx_details = self.w3.eth.get_transaction(tx["hash"])
            token_address = tx_details["to"]
            amount = tx_details["value"]

            # Build and send the transaction
            nonce = self.w3.eth.get_transaction_count(watcher_account.address)
            gas_price = self.w3.eth.gas_price

            tx_data = {
                "nonce": nonce,
                "to": token_address,
                "value": amount,
                "gas": 21000,
                "gasPrice": gas_price,
                "chainId": 1,
            }

            signed_tx = self.w3.eth.account.sign_transaction(
                tx_data, watcher_account.key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            LOGGER.info(f"Mirrored transaction sent: {tx_hash.hex()}")
            await self.wait_for_receipt(tx_hash)
        except Exception as e:
            LOGGER.error(f"Error mirroring trade: {e}")

    async def wait_for_receipt(self, tx_hash: str) -> None:
        """
        Wait for the transaction receipt.

        Args:
            tx_hash (str): The transaction hash.
        """
        while True:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt.status == 1:
                    LOGGER.info(f"Transaction {tx_hash.hex()} confirmed successfully.")
                else:
                    LOGGER.error(f"Transaction {tx_hash.hex()} failed.")
                break
            await asyncio.sleep(1)


class WsCryptoCopyTrader:
    """
    Class to watch and copy trades from a target address using WebSocket connection.
    """

    UNISWAP_ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    PANCAKESWAP_ROUTER_ADDRESS = "0xEfF92A263d31888d860bD50809A8D171709b7b1c"
    KNOWN_ETH_ROUTERS = [
        UNISWAP_ROUTER_ADDRESS,
        PANCAKESWAP_ROUTER_ADDRESS,
        "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24",
        "0xedf6066a2b290C185783862C7F4776A2C8077AD1",
        "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "0x8cFe327CEc66d1C090Dd72bd0FF11d690C33a2Eb",
        "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891",
        "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "0x89Fa1974120d2a7F83a0cb80df3654721c6a38Cd",
    ]
    """
    uniswap: for ethereum main net and polygon
    pancakeswap: for binance smart chain
    oneinch: avalanche network
    jupiter sdk: for solana
    """

    def __init__(self, chat_id: int, network: str = "ETH"):
        provider = INFURA_HTTP_URL
        if network == "ETH":
            provider = INFURA_HTTP_URL
        elif network == "BSC":
            provider = BSC_HTTP_URL
        elif network == "POL":
            provider = POLYGON_HTTP_URL
        elif network == "AVL":
            provider = AVALANCHE_HTTP_URL
        self.w3 = Web3(Web3.HTTPProvider(f"{provider}"))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.bot = bot
        self.network_sn = network
        self.chat_id = chat_id
        if not self.w3.is_connected():
            LOGGER.error("Connection Error")
            raise Exception("Unable to connect to the RPC network")

    async def copytrade(
        self,
        watcher_private_key: str,
        target_address: str,
        chain_id: int = 1,
        poll_interval: float = 10.0,
    ) -> None:
        """
        Watch for trades from the target_address and mirror them in the watcher wallet.

        Args:
            watcher_private_key (str): The private key of the watcher wallet.
            target_address (str): The address to watch for trades.
            poll_interval (float): Polling interval in seconds. Default is 10 seconds.
        """
        LOGGER.debug(f"Private Key: {watcher_private_key}")
        LOGGER.debug(f"Address: {target_address}")
        LOGGER.debug(f"Poll Interval: {poll_interval}")

        watcher_account = self.w3.eth.account.from_key(watcher_private_key)
        LOGGER.debug(f"Watcher Account: {watcher_account.address}")

        async def handle_event(event: dict) -> None:
            tx_hash = event["transactionHash"]
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            LOGGER.debug(f"Transaction Hash: {tx_hash}")
            LOGGER.debug(f"Transaction Receipt Status: {tx_receipt.status}")
            if tx_receipt.status == 1:  # Check if the transaction was successful
                tx_details = self.w3.eth.get_transaction(tx_hash)
                LOGGER.debug(f"Transaction Details: {tx_details}")
                if tx_details["to"] in self.KNOWN_ETH_ROUTERS:
                    LOGGER.debug("Transaction is to a known router")
                    await self.mirror_trade(tx_hash, watcher_account)

        event_filter = self.w3.eth.filter(
            {"fromBlock": "latest", "address": target_address}
        )
        LOGGER.debug("Event filter created")

        while True:
            LOGGER.debug("Polling for new events")
            for event in event_filter.get_new_entries():
                LOGGER.debug(f"New event found: {event}")
                await handle_event(event)
            await asyncio.sleep(poll_interval)

    async def mirror_trade(self, tx_hash: str, watcher_account: any) -> None:
        """
        Perform the same trade in the watcher wallet.

        Args:
            tx_hash (str): The transaction hash.
            watcher_account (Web3.eth.account): The watcher account object.
        """
        try:
            # Extract details from the target transaction
            tx_details = self.w3.eth.get_transaction(tx_hash)
            token_address = tx_details["to"]
            amount = tx_details["value"]

            wallet: UserWallet = await WalletData.get_wallet_by_id(self.chat_id)
            network: Network = [
                network for network in Networks if network.sn == self.network_sn
            ][0]
            preset: Optional[Presets] = await PresetsData.get_presets_by_id(
                self.chat_id
            )
            tradable_percentage = (
                preset.balance_tradable if preset is not None else 0.25
            )

            if network.name == "solana":
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text="We do not copy trade with solana wallet for now",
                    reply_markup=setKeyboard(auth_start_buttons),
                    parse_mode="HTML",
                )
                await self.wait_for_receipt("error")


            balance = await ETHWallet(network.sn).get_token_balance(
                watcher_account.address, token_address
            )

            token_metadata = await TokenMetadata().get_token_symbol_by_contract(
                token_address
            )
            # Build and send the transaction
            amount = (
                balance * tradable_percentage
            ) * 10**token_metadata.decimal.ethereum
            nonce = self.w3.eth.get_transaction_count(watcher_account.address)
            gas_price = self.w3.eth.gas_price

            tx_data = {
                "nonce": nonce,
                "to": token_address,
                "value": amount,
                "gas": 21000,
                "gasPrice": gas_price,
                "chainId": self.w3.eth.chain_id,
            }

            signed_tx = self.w3.eth.account.sign_transaction(
                tx_data, watcher_account.key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            LOGGER.info(f"Mirrored transaction sent: {tx_hash.hex()}")
            await self.wait_for_receipt(tx_hash)

            # send transaction information to user
            copy_message = f"""
<b>COPY TRADE RESULT</b>
------------------------
<code>
AMOUNT      | {amount}
TO          | {token_address}
</code>
🔗 <a href="https://etherscan.io/tx/{tx_hash.hex()}">Transaction Hash</a>
            """

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=copy_message,
                reply_markup=setKeyboard(auth_start_buttons),
                parse_mode="HTML",
            )
        except Exception as e:
            LOGGER.error(f"Error copying trade: {e}")
            copy_message = f"""
<b>COPY TRADE RESULT</b>
------------------------
🔗 <a href="https://etherscan.io/tx/{tx_hash.hex()}">Transaction Hash</a>
------------------------
There was an error copying similar trade from your whale:
ℹ Reason: <b>{e}</b>
            """
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=copy_message,
                reply_markup=setKeyboard(auth_start_buttons),
                parse_mode="HTML",
            )

    async def wait_for_receipt(self, tx_hash: str) -> None:
        """
        Wait for the transaction receipt.

        Args:
            tx_hash (str): The transaction hash.
        """
        while True:
            if tx_hash == "error":
                break
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt.status == 1:
                    LOGGER.info(f"Transaction {tx_hash.hex()} confirmed successfully.")
                else:
                    LOGGER.error(f"Transaction {tx_hash.hex()} failed.")
                break
            await asyncio.sleep(1)


CryptoWatcherHttp = HttpCryptoCopyTrader()
# CryptoWatcherWs = WsCryptoCopyTrader()

# if __name__ == "__main__":
#     asyncio.run(CryptoWatcherHttp.watch_trades(WATCHER_PRIVATE_KEY, TARGET_ADDRESS))
#     asyncio.run(CryptoWatcherWs.copytrade(WATCHER_PRIVATE_KEY, TARGET_ADDRESS))
