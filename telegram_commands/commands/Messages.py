from textwrap import fill
from typing import Optional

from data.Networks import Network, Networks
from lib.WalletClass import CryptoWallet
from models.Presets import Presets
from models.UserModel import User, UserWallet


def profile_msg(user: User) -> str:
    """
    Generates a formatted profile message for a User object.

    Args:
        user (User): The User object containing profile information.

    Returns:
        str: The formatted profile message.
    """

    username = user.username or user.user_id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    agreement_status = "Yes" if user.accepted_agreement else "No"

    # Formatted message with f-strings and textwrap.fill
    message = f"""
<code>
PROFILE FOR {username.upper()}
---------------------------------
Username    |  {username}
UserID      |  {user.user_id}
FirstName   |  {first_name}
LastName    |  {last_name}
Agreement   |  {agreement_status}
Agreement   |  {user.accepted_on or 'N/A'}
</code>
    """

    return message

async def preset_msg(wallet: Optional[UserWallet], preset: Optional[Presets], amount: float):
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]
    return f"""

<b>Connected to {wallet.chain_name}</b>
-----------------------------------
<code>
🔺 SLIPPAGE               | {preset.slippage}
🔺 MAX GAS PRICE          | {preset.max_gas_price}
🔺 GAS LIMIT              | {preset.gas_limit}
🔺 MIN CIRCULATING SUPPLY | {preset.min_circulating_supply}
🔺 MIN TOTAL SUPPLY       | {preset.min_token_supply}
</code>
-----------------------------------
💰 BALANCE
<b>{await CryptoWallet(network.sn).get_balance(wallet.pub_key)} {'ETH' if not wallet.chain_name.lower() == "solana" else 'SOL'}</b>
-----------------------------------
💵 CURRENT GAS
<pre>{await CryptoWallet(network.sn).get_gas_price()} WEI</pre>
-----------------------------------
👛 MULTI WALLET ADDRESS
<pre>{wallet.pub_key}</pre>
-----------------------------------
🔑 PRIVATE KEY
<pre>{wallet.sec_key}</pre>
------------------------------------
🗒 NOTE: <b>Ensure to store this keys somewhere as we do not have a means to recover these wallet addresses for you.</b>
            """


async def wallet_msg(wallet: Optional[UserWallet]) -> str:
    """
    Generates a formatted wallet message for a Wallet object.

    Args:
        wallet (UserWallet | None): The Wallet object containing wallet informations.

    Returns:
        str: The formatted wallet message.
    """
    # Formatted message with f-strings and textwrap.fill
    network: Network  = [network for network in Networks if network.id == wallet.chain_id][0] if wallet is not None else Networks[0]

    no_wallet_message = f"""
You currently have no wallet attached to your account.

Please generate a unique one or attach an existing one to your account to aid your trading.
    """

    if wallet is not None:
        balance = await CryptoWallet(network.sn).get_balance(wallet.pub_key)
        message = f"""
CONNECTED TO {wallet.chain_name.upper()}
---------------------------------
👛 Public    :  <pre><code>{wallet.pub_key}</code></pre>
---------------------------------
🔑 Private   :  <pre><code>{wallet.sec_key}</code></pre>
---------------------------------
🗝 Encrypted :  <pre><code>{wallet.enc_key['address']}</code></pre>
---------------------------------


💰 Balance :  {round(balance, 6)} {'ETH' if not wallet.chain_name.lower() == "solana" else 'SOL'}
---------------------------------
⛓ ChainID :  {wallet.chain_id}
----------------------------------

💵 CURRENT GAS:------------ <pre>{await CryptoWallet(network.sn).get_gas_price()} WEI</pre>
🗒 NOTE: <b>Ensure to store this keys somewhere as we do not have a means to recover these wallet addresses for you.</b>

        """
        return message
    else:
        return no_wallet_message
