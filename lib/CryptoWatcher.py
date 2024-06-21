import asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
from lib.GetDotEnv import INFURA_HTTP_URL, INFURA_WS_URL
from lib.Logger import LOGGER


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

    def __init__(self):
        self.w3 = Web3(Web3.WebsocketProvider(INFURA_WS_URL))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if not self.w3.is_connected():
            LOGGER.error("Connection Error")
            raise Exception("Unable to connect to the RPC network")

    async def copytrade(
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

        async def handle_event(event: dict) -> None:
            tx_hash = event["transactionHash"]
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status == 1:  # Check if the transaction was successful
                await self.mirror_trade(tx_hash, watcher_account)

        event_filter = self.w3.eth.filter(
            {"fromBlock": "latest", "address": target_address}
        )

        while True:
            for event in event_filter.get_new_entries():
                await handle_event(event)
            await asyncio.sleep(poll_interval)  # Poll every poll_interval seconds

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

            # Build and send the transaction
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


CryptoWatcherHttp = HttpCryptoCopyTrader()
CryptoWatcherWs = WsCryptoCopyTrader()

# if __name__ == "__main__":
#     asyncio.run(CryptoWatcherHttp.watch_trades(WATCHER_PRIVATE_KEY, TARGET_ADDRESS))
#     asyncio.run(CryptoWatcherWs.copytrade(WATCHER_PRIVATE_KEY, TARGET_ADDRESS))
