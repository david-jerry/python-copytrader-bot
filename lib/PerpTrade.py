# import aiohttp
# import json

# from lib.GetDotEnv import COINMARKETCAP_API

# class CryptoArbitrageBot:
#     def __init__(self, ):
#         self.cmc_headers = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API}
#         self.cmc_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

#     async def fetch_listings(self):
#         params = {'start': 200, 'limit': 200, 'sort': 'date_added', 'cryptocurrency_type': 'tokens', 'convert': 'USD', 'aux':'circulating_supply,total_supply,market_cap_by_total_supply,volume_24h_reported,volume_7d,volume_7d_reported,volume_30d,volume_30d_reported,is_market_cap_included_in_calc,date_added,tags,platform,'}
#         async with aiohttp.ClientSession() as session:
#             async with session.get(self.cmc_url, headers=self.cmc_headers, params=params) as response:
#                 response.raise_for_status()
#                 return await response.json()

# # from dydx3 import Client
# # from dydx3.constants import ORDER_SIDE_BUY, ORDER_SIDE_SELL, ORDER_TYPE_LIMIT
# # from dydx3.stark_private_key import private_key_from_seed
# # from web3 import Web3
# # import time

# # # Your DYDX credentials and private key
# # DYDX_API_KEY = 'your_dydx_api_key'
# # DYDX_API_SECRET = 'your_dydx_api_secret'
# # DYDX_API_PASSPHRASE = 'your_dydx_api_passphrase'
# # STARK_PRIVATE_KEY = 'your_stark_private_key'
# # ETH_PRIVATE_KEY = 'your_eth_private_key'
# # WEB3_PROVIDER_URL = 'https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'

# # # Initialize the Web3 instance
# # w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

# # # Initialize the dydx client
# # client = Client(
# #     host='https://api.dydx.exchange',
# #     api_key_credentials={
# #         'key': DYDX_API_KEY,
# #         'secret': DYDX_API_SECRET,
# #         'passphrase': DYDX_API_PASSPHRASE,
# #     },
# #     stark_private_key=STARK_PRIVATE_KEY,
# #     eth_private_key=ETH_PRIVATE_KEY,
# #     network_id=1,  # Mainnet
# #     web3=w3,
# # )

# # # Define the parameters for the buy order
# # market = 'NEW_TOKEN-USD'
# # side = ORDER_SIDE_BUY
# # size = '10'  # Size of the order
# # price = '1.0'  # Price at which you want to buy
# # limit_fee = '0.001'  # Fee

# # # Create the buy order
# # order = client.private.create_order(
# #     position_id='YOUR_POSITION_ID',
# #     market=market,
# #     side=side,
# #     order_type=ORDER_TYPE_LIMIT,
# #     post_only=True,
# #     size=size,
# #     price=price,
# #     limit_fee=limit_fee,
# #     expiration_epoch_seconds=int(time.time()) + 24 * 60 * 60,  # Expire in 24 hours
# # )
# # print(f'Buy order created: {order}')

# # # Define parameters for the limit sell order
# # market = 'NEW_TOKEN-USD'
# # side = ORDER_SIDE_SELL
# # size = '10'  # Size of the order
# # limit_fee = '0.001'  # Fee

# # # Set multiple limit sell orders at different prices
# # sell_prices = ['1.2', '1.5', '2.0']  # Example prices

# # for price in sell_prices:
# #     order = client.private.create_order(
# #         position_id='YOUR_POSITION_ID',
# #         market=market,
# #         side=side,
# #         order_type=ORDER_TYPE_LIMIT,
# #         post_only=True,
# #         size=size,
# #         price=price,
# #         limit_fee=limit_fee,
# #         expiration_epoch_seconds=int(time.time()) + 24 * 60 * 60,  # Expire in 24 hours
# #     )
# #     print(f'Limit sell order created at price {price}: {order}')

# # bot.py
# import os
# import json
# import dotenv
# from web3 import Account, Web3
# import argparse
# from celery import Celery

# dotenv.load_dotenv()

# MIN_ERC20_ABI = json.loads("""
#     [...]  # Your existing MIN_ERC20_ABI JSON data here
# """)

# UNISWAPV2_ROUTER_ABI = json.loads("""
#     [...]  # Your existing UNISWAPV2_ROUTER_ABI JSON data here
# """)

# UNISWAP_V2_SWAP_ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
# # Initialize Celery
# celery_app = Celery('tasks')
# celery_app.config_from_object('celeryconfig')


# class AutoSellBot:
#     def __init__(self, name: str, token_address: str, stop_loss_percent: int = 10,
#                  take_profit_percent: int = 50, check_interval: int = 60,
#                  slippage_percent: int = 3, private_key: str = "", rpc: str = "") -> None:
#         self.name = name
#         self.token_address = token_address
#         self.stop_loss_percent = stop_loss_percent
#         self.take_profit_percent = take_profit_percent
#         self.check_interval = check_interval
#         self.slippage_percent = slippage_percent
#         self.private_key = private_key if private_key else os.getenv("PRIVATE_KEY")
#         if not self.private_key:
#             raise ValueError("error: no private key provided")

#         self.sell_path = [self.token_address, WETH_TOKEN_ADDRESS]

#         self.rpc = rpc if rpc else os.getenv("RPC_ENPOINT")
#         if not self.rpc:
#             raise ValueError("error: no rpc endpoint configured")

#         self.account = Account.from_key(self.private_key)

#         self.web3 = Web3(Web3.HTTPProvider(self.rpc))
#         self.router_contract = self.web3.eth.contract(
#             address=UNISWAP_V2_SWAP_ROUTER_ADDRESS, abi=UNISWAPV2_ROUTER_ABI
#         )
#         self.token_contract = self.web3.eth.contract(
#             address=self.token_address, abi=MIN_ERC20_ABI
#         )

#         self.token_balance = self.get_balance()
#         if self.token_balance == 0:
#             raise ValueError("error: token_balance is 0")

#         self.initial_value = self.get_position_value()
#         self.stop_loss_value = self.initial_value * (1 - self.stop_loss_percent / 100)
#         self.take_profit_value = self.initial_value * (1 + self.take_profit_percent / 100)

#         approved = self.approve_token()
#         assert approved, f"{self.name}: error: could not approve token"
#         print(f"{self.name}: bot started")

#     def get_balance(self):
#         return self.token_contract.functions.balanceOf(self.account.address).call()

#     def get_position_value(self):
#         amounts_out = self.router_contract.functions.getAmountsOut(
#             self.token_balance, self.sell_path
#         ).call()
#         return amounts_out[1]

#     def approve_token(self):
#         approve_tx = self.token_contract.functions.approve(
#             UNISWAP_V2_SWAP_ROUTER_ADDRESS, 2**256 - 1
#         ).build_transaction(
#             {
#                 "gas": 500_000,
#                 "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
#                 "maxFeePerGas": 100 * 10**10,
#                 "nonce": self.web3.eth.get_transaction_count(self.account.address),
#             }
#         )

#         signed_approve_tx = self.web3.eth.account.sign_transaction(
#             approve_tx, self.account.key
#         )

#         tx_hash = self.web3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
#         tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

#         if tx_receipt and tx_receipt["status"] == 1:
#             print(f"{self.name}: approve successful: approved {UNISWAP_V2_SWAP_ROUTER_ADDRESS} to spend unlimited token")
#             return True
#         else:
#             raise Exception(f"{self.name} error: could not approve token")

#     def sell_token(self, min_amount_out=0):
#         sell_tx_params = {
#             "nonce": self.web3.eth.get_transaction_count(self.account.address),
#             "from": self.account.address,
#             "gas": 500_000,
#             "maxPriorityFeePerGas": self.web3.eth.max_priority_fee,
#             "maxFeePerGas": 100 * 10**10,
#         }
#         sell_tx = self.router_contract.functions.swapExactTokensForETH(
#             self.token_balance,
#             min_amount_out,
#             self.sell_path,
#             self.account.address,
#             int(time.time()) + 180,
#         ).build_transaction(sell_tx_params)

#         signed_sell_tx = self.web3.eth.account.sign_transaction(
#             sell_tx, self.account.key
#         )

#         tx_hash = self.web3.eth.send_raw_transaction(signed_sell_tx.rawTransaction)
#         tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
#         if tx_receipt and tx_receipt["status"] == 1:
#             self.token_balance = self.get_balance()
#             if self.token_balance == 0:
#                 print(f"{self.name}: all token sold: tx hash: {Web3.to_hex(tx_hash)}")
#                 return True
#         else:
#             print(f"{self.name}: error selling token")
#             return False

#     def execute(self):
#         position_value = self.get_position_value()
#         print(f"{self.name}: position value {position_value / 10 ** 18:.6f}")
#         if (position_value <= self.stop_loss_value) or (position_value >= self.take_profit_value):
#             min_amount_out = int(position_value * (1 - self.slippage_percent / 100))
#             print(f"{self.name}: position value hit limit - selling all token")
#             self.sell_token(min_amount_out)


# @celery_app.task
# def run_bot(name, token_address, stop_loss_percent, take_profit_percent, check_interval, slippage_percent, private_key, rpc):
#     bot = AutoSellBot(name, token_address, stop_loss_percent, take_profit_percent, check_interval, slippage_percent, private_key, rpc)
#     while bot.token_balance:
#         try:
#             bot.execute()
#             time.sleep(check_interval)
#         except Exception as e:
#             print(f"exception: {e}")
#     print(f"{bot.name}: stopping bot - all token sold")


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Simple stop loss and take profit trading bot.")
#     parser.add_argument("token_address", type=str, help="token address you want to monitor")
#     parser.add_argument("--name", type=str, default="simple bot", help="bot name")
#     parser.add_argument("--sl", type=int, default=5, help="stop-loss percentage")
#     parser.add_argument("--tp", type=int, default=20, help="take profit percentage")
#     parser.add_argument("--interval", type=int, default=60, help="check interval in seconds")
#     parser.add_argument("--slippage", type=int, default=3, help="slippage percentage")
#     parser.add_argument("--key", type=str, help="private key")
#     parser.add_argument("--rpc", type=str, help="RPC endpoint")

#     args = parser.parse_args()

#     run_bot.apply_async(args=(args.name, args.token_address, args.sl, args.tp, args.interval, args.slippage, args.key, args.rpc))

