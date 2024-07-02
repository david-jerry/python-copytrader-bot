from typing import Optional
from bip_utils import (
    Bip39SeedGenerator,
    Bip39MnemonicGenerator,
    Bip39WordsNum,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip44PrivateKey,
    Bip44PublicKey,
)
import asyncio
import base58
from eth_account import Account
from solders.keypair import Keypair # type: ignore

from lib.Logger import LOGGER # type: ignore

# Chain constants with BIP44 coin type and derivation path
CHAIN_CONFIG = {
    Bip44Coins.ETHEREUM: {
        "name": "Ethereum",
        "derivation_path": "m/44'/60'/0'/0/0",  # Standard Ethereum path
    },
    Bip44Coins.POLYGON: {
        "name": "Polygon",
        "derivation_path": "m/44'/60'/0'/0/0",  # Same as Ethereum
    },
    Bip44Coins.BINANCE_SMART_CHAIN: {
        "name": "Binance Smart Chain",
        "derivation_path": "m/44'/714'/0'/0/0",
    },
    Bip44Coins.AVAX_C_CHAIN: {
        "name": "Avalanche",
        "derivation_path": "m/44'/9000'/0'/0/0",
    },
    Bip44Coins.SOLANA: {
        "name": "Solana",
        "derivation_path": "m/44'/501'/0'/0'",  # Solana path
    },
}


class MultiChainWalletGenerator:
    """
    This class generates a multi-chain wallet supporting Solana, Ethereum, Polygon, Binance Smart Chain, and Avalanche.

    It utilizes BIP39 standards for mnemonic phrase generation (seed generation) and BIP44 for HD wallet derivation with chain-specific paths.

    **Supported Chains:**

    * Solana
    * Ethereum
    * Polygon (uses Ethereum derivation path for now)
    * Binance Smart Chain
    * Avalanche

    **Generating a Wallet:**

    1. Create an instance of `MultiChainWalletGenerator`. You can optionally provide a 12-word BIP39 mnemonic phrase,
       otherwise a new one will be generated. Supplying a password for encryption is recommended for security.
    2. Use the `generate_wallet` method to generate a public address and private key for your desired chain type.
       This method is asynchronous.
    3. The `generate_wallet` method returns a tuple containing the public address (str), private key (hex-encoded str for non-Solana, base58-encoded for Solana),
       and a boolean indicating if it's a Solana chain (True) or not (False).

    **Example Usage:**

    ```python
    from hdwallet import BIP44HDWalletBase

    # Generate a wallet for Ethereum with a custom mnemonic
    mnemonic = "your 12-word mnemonic phrase"
    wallet = MultiChainWalletGenerator()
    address, private_key, is_solana = await wallet.generate_wallet(Bip44Coins.ETHEREUM, mnemonic)

    # Use the address and private key for your application (e.g., sending transactions)
    hd_wallet = BIP44HDWalletBase(private_key, network="ethereum")  # Replace with appropriate library for your use case
    # ... perform transactions using hd_wallet object

    print(f"Address: {address}")
    print(f"Private Key: {private_key}")
    ```

    **Important Notes:**

    * This class provides a starting point for generating wallets. It's your responsibility to handle the private key securely.
    * Consider using a Hardware Wallet for enhanced security.
    * The Polygon derivation path might change in the future.
    """

    def __init__(self):
        """
        Initializes the MultiChainWalletGenerator object.

        """


    async def generate_wallet(
        self, chain_type: Bip44Coins, mnemonic: str = None, sol_mnemonic: str = None, private_key_hex: str = None, sol_private_key_hex: str = None, password: str = ""
    ) -> tuple[str, str, Optional[str]]:
        """
        Generates a public address and private key for the specified chain type.

        This method asynchronously generates a seed from the mnemonic (optionally encrypted with password),
        derives the keypair based on the provided chain_type using BIP44, and returns the address and private key.

        For Solana (SOL), it uses the account index 0 and change type `CHAIN_EXT` (might require adjustment for Solflare compatibility).

        Args:
            chain_type (Bip44Coins): The desired coin type for the wallet (refer to `Bip44Coins` enum for supported chains).
            mnemonic (str, optional): A 12-word BIP39 mnemonic phrase. If not provided, a new one will be generated. Defaults to None.
            Optional:
                private_key_hex (str, optional): If provided, it will be used to derive the public key instead of using the mnemonic.
            password (str, optional): An optional password to encrypt the mnemonic (recommended for added security). Defaults to ''.

        Returns:
            tuple: A tuple containing the following:
                - public_address (str): The public address for the generated wallet.
                - private_key (str): The private key for the generated wallet (hex-encoded for non-Solana, base58-encoded for Solana).
                - is_solana (bool): A boolean indicating if the generated wallet is for the Solana chain.
        """
        if not mnemonic:
            phrase = Bip39MnemonicGenerator().FromWordsNumber(
                Bip39WordsNum.WORDS_NUM_12
            )
            mnemonic = str(phrase)

        if not sol_mnemonic:
            sol_phrase = Bip39MnemonicGenerator().FromWordsNumber(
                Bip39WordsNum.WORDS_NUM_12
            )
            LOGGER.debug(phrase)
            sol_mnemonic = str(sol_phrase)

        if chain_type not in CHAIN_CONFIG:
            raise ValueError(f"Unsupported chain type: {chain_type}")

        if private_key_hex is not None or sol_private_key_hex is not None:
            return self._generate_wallet_from_private_key(chain_type, private_key_hex, sol_private_key_hex)
        else:
            if chain_type == Bip44Coins.SOLANA:
                kp = Keypair()
                pubkey = kp.pubkey()
                rawPK = bytes(kp)
                private_key = base58.b58encode(rawPK).decode()
                return str(pubkey), private_key, mnemonic
            else:
                seed_bytes = Bip39SeedGenerator(mnemonic).Generate(password)

                chain_info = CHAIN_CONFIG[chain_type]
                bip44_mst_ctx = Bip44.FromSeed(seed_bytes, chain_type)
                derivation_path = chain_info["derivation_path"]


                # bip44_ctx = bip44_mst_ctx.DerivePath(derivation_path)
                address = bip44_mst_ctx.PublicKey().ToAddress()
                private_key = bip44_mst_ctx.PrivateKey().Raw().ToHex()
                return address, private_key, mnemonic

    def _generate_wallet_from_private_key(
        self, chain_type: Bip44Coins, private_key_hex: str, sol_private_key_hex: str
    ) -> tuple[str, str, Optional[str]]:
        """
        Generates a public address from a provided private key in hex format.

        This function is used internally by `generate_wallet` when a `private_key_hex` argument is provided.
        It directly derives the public key from the given hex-encoded private key and chain type using the `bip_utils` library.

        For Solana (SOL), it additionally combines the private key bytes with the compressed public key bytes
        before base58 encoding.

        Args:
            chain_type (Bip44Coins): The desired coin type for the wallet (refer to `Bip44Coins` enum for supported chains).
            private_key_hex (str): The private key in hex format.

        Returns:
            tuple: A tuple containing the following:
                - public_address (str): The public address for the generated wallet.
                - private_key (str): The provided private key (unchanged).
                - is_solana (bool): A boolean indicating if the generated wallet is for the Solana chain.
        """
        if chain_type == Bip44Coins.SOLANA:
            account = Keypair.from_base58_string(sol_private_key_hex)
            return account.pubkey, sol_private_key_hex, None
        else:
            account = Account.from_key(private_key_hex)
            return account.address, private_key_hex, None

