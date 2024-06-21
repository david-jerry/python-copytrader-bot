from decimal import Decimal
from web3 import Web3
from eth_account import Account
import secrets
from typing import Dict, Any
from lib.GetDotEnv import INFURA_HTTP_URL
from lib.Logger import LOGGER

class CryptoWallet:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(f"{INFURA_HTTP_URL}"))
        if not self.w3.is_connected():
            LOGGER.info("Connection Error")
            raise ConnectionError("Failed to connect to the Ethereum network")
        self.private_key = f"0x{secrets.token_hex(32)}"
        LOGGER.info(f"Generated private key: {self.private_key}")

    def validate_address(self, address: str) -> bool:
        """
        Validate an Ethereum address.

        Args:
            address (str): The Ethereum address to validate.

        Returns:
            bool: True if the address is valid, False otherwise.

        Example:
            is_valid = CryptoWallet.validate_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
            print(is_valid)  # Output: True or False
        """
        return self.w3.is_checksum_address(address)

    def create_wallet(self, password: str) -> Dict[str, Any]:
        """
        Create a new Ethereum wallet.

        Args:
            password (str): The password to encrypt the wallet.

        Returns:
            Dict[str, Any]: The wallet details including private key, address, and encrypted key.

        Example:
            wallet = CryptoWallet.create_wallet("my_secure_password")
            print(wallet["address"])  # Output: Ethereum address
        """
        LOGGER.info("Generating wallet...")
        account = Account.from_key(self.private_key)
        encrypted_key = Account.encrypt(account.key.hex(), password)
        LOGGER.info(f"Encrypted key: {encrypted_key}")
        return {
            "private_key": account.key.hex(),
            "address": account.address,
            "encrypted_key": encrypted_key
        }

    def import_wallet(self, encrypted_key: str, password: str) -> str:
        """
        Import an Ethereum wallet.

        Args:
            encrypted_key (str): The encrypted key of the wallet.
            password (str): The password to decrypt the wallet.

        Returns:
            str: The Ethereum address of the imported wallet.

        Example:
            address = CryptoWallet.import_wallet(encrypted_key, "my_secure_password")
            print(address)  # Output: Ethereum address
        """
        decrypted_key = Account.decrypt(encrypted_key, password)
        account = self.w3.eth.account.from_key(decrypted_key)
        return account.address

    def get_balance(self, address: str) -> Decimal:
        """
        Get the balance of an Ethereum address.

        Args:
            address (str): The Ethereum address to check the balance of.

        Returns:
            Decimal: The balance in Ether.

        Example:
            balance = CryptoWallet.get_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
            print(balance)  # Output: 12.345 (example balance)
        """
        balance = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance, "ether")

    def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """
        Estimate the gas required for a transaction.

        Args:
            transaction (Dict[str, Any]): The transaction data.

        Returns:
            int: The estimated gas.

        Example:
            transaction = {
                "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "value": CryptoWallet.w3.to_wei(0.1, "ether")
            }
            gas = CryptoWallet.estimate_gas(transaction)
            print(gas)  # Output: 21000 (example gas estimate)
        """
        return self.w3.eth.estimate_gas(transaction)

    def get_gas_price(self) -> int:
        """
        Get the current gas price.

        Returns:
            int: The current gas price in Wei.

        Example:
            gas_price = CryptoWallet.get_gas_price()
            print(gas_price)  # Output: 20000000000 (example gas price)
        """
        return self.w3.eth.gas_price

    def send_token(self, abi: Any, contract_address: str, sender_private_key: str, recipient_address: str, amount_ether: float) -> str:
        """
        Send tokens to a recipient address.

        Args:
            abi (Any): The contract ABI.
            contract_address (str): The address of the token contract.
            sender_private_key (str): The private key of the sender.
            recipient_address (str): The recipient's address.
            amount_ether (float): The amount of tokens to send in Ether equivalent.

        Returns:
            str: The transaction URL on Etherscan.

        Example:
            abi = [...]  # Contract ABI
            tx_url = CryptoWallet.send_token(abi, "0xContractAddress", "0xSenderPrivateKey", "0xRecipientAddress", 1.0)
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)
        contract = self.w3.eth.contract(contract_address, abi)
        token_amount = self.w3.to_wei(amount_ether, "ether")

        gas_estimate = contract.functions.transfer(recipient_address, token_amount).estimate_gas({"from": sender_account.address})

        tx = {
            "nonce": nonce,
            "gas": gas_estimate,
            "gasPrice": self.get_gas_price(),
            "chainId": 1
        }

        transaction = contract.functions.transfer(recipient_address, token_amount).build_transaction(tx)
        signed_tx = self.w3.eth.account.sign_transaction(transaction, sender_account.key)

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status:
                LOGGER.info("Transaction successful!")
                return f"https://etherscan.io/tx/{tx_hash.hex()}"
            else:
                LOGGER.info("Transaction failed")
                return "Transaction failed"
        except Exception as e:
            LOGGER.error(e)
            return str(e)

    def send_crypto(self, sender_private_key: str, recipient_address: str, amount_ether: Decimal) -> str:
        """
        Send Ether to a recipient address.

        Args:
            sender_private_key (str): The private key of the sender.
            recipient_address (str): The recipient's address.
            amount_ether (Decimal): The amount of Ether to send.

        Returns:
            str: The transaction URL on Etherscan.

        Example:
            tx_url = CryptoWallet.send_crypto("0xSenderPrivateKey", "0xRecipientAddress", Decimal("0.1"))
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)

        tx = {
            "nonce": nonce,
            "to": recipient_address,
            "value": self.w3.to_wei(amount_ether, "ether"),
            "gas": 21000,
            "gasPrice": self.get_gas_price(),
            "chainId": 1
        }

        signed_tx = self.w3.eth.account.sign_transaction(tx, sender_account.key)

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status:
                LOGGER.info("Transaction successful!")
                return f"https://etherscan.io/tx/{tx_hash.hex()}"
            else:
                LOGGER.info("Transaction failed")
                return "Transaction failed"
        except Exception as e:
            LOGGER.error(e)
            return str(e)

    def swap_tokens_uniswap(self, sender_private_key: str, token_in: str, token_out: str, amount_in: float, amount_out_min: float, deadline: int, router_address: str, router_abi: Any) -> str:
        """
        Swap tokens using Uniswap.

        Args:
            sender_private_key (str): The private key of the sender.
            token_in (str): The address of the input token.
            token_out (str): The address of the output token.
            amount_in (float): The amount of input tokens.
            amount_out_min (float): The minimum amount of output tokens.
            deadline (int): The transaction deadline in seconds.
            router_address (str): The address of the Uniswap router.
            router_abi (Any): The ABI of the Uniswap router.

        Returns:
            str: The transaction URL on Etherscan.

        Example:
            router_abi = [...]  # Uniswap Router ABI
            tx_url = CryptoWallet.swap_tokens_uniswap("0xSenderPrivateKey", "0xTokenIn", "0xTokenOut", 1.0, 0.9, 300, "0xRouterAddress", router_abi)
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)
        amount_in_wei = self.w3.to_wei(amount_in, 'ether')
        amount_out_min_wei = self.w3.to_wei(amount_out_min, 'ether')
        path = [token_in, token_out]

        router_contract = self.w3.eth.contract(address=router_address, abi=router_abi)
        deadline_timestamp = self.w3.eth.get_block('latest')['timestamp'] + deadline

        tx = {
            "nonce": nonce,
            "gas": 2100000,
            "gasPrice": self.get_gas_price(),
            "chainId": 1
        }

        transaction = router_contract.functions.swapExactTokensForTokens(
            amount_in_wei,
            amount_out_min_wei,
            path,
            sender_account.address,
            deadline_timestamp
        ).build_transaction(tx)

        signed_tx = self.w3.eth.account.sign_transaction(transaction, sender_account.key)

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status:
                LOGGER.info("Token swap successful!")
                return f"https://etherscan.io/tx/{tx_hash.hex()}"
            else:
                LOGGER.info("Token swap failed")
                return "Token swap failed"
        except Exception as e:
            LOGGER.error(e)
            return str(e)

CryptoWallet = CryptoWallet()
