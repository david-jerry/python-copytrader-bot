import base64
from datetime import datetime
from decimal import Decimal
import json
import time
from mnemonic import Mnemonic
import requests
from web3 import Web3
from bip_utils import Bip39SeedGenerator, Bip44Coins, Bip44, base58, Bip44Changes
from web3.contract import Contract
from eth_account import Account
import secrets
from typing import Dict, Any, Optional
from data.Networks import Network, Networks
from data.Queries import CoinData
from lib.GetDotEnv import (
    AVALANCHE_HTTP_URL,
    BSC_HTTP_URL,
    ETHERSCAN_API,
    INFURA_HTTP_URL,
    POLYGON_HTTP_URL,
    QUICKNODE_HTTP,
)
from lib.Logger import LOGGER
from lib.MultiChainWalletGenerator import MultiChainWalletGenerator
from lib.TokenMetadata import TokenMetadata
from lib.Types import TokenInfo
from models.CoinsModel import Coins, CurrentPrice, MarketCap, Platform

from solana.rpc.async_api import AsyncClient
from solders.message import Message, MessageAddressTableLookup, MessageHeader, MessageV0, to_bytes_versioned  # type: ignore
from solders.signature import Signature  # type: ignore
from solders.pubkey import Pubkey  # type: ignore
from solders.keypair import Keypair  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore

from solana.rpc.types import TxOpts, TokenAccountOpts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

from jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA

ERC20_ABI = json.loads(
    """
    [
        {
            "constant": true,
            "inputs": [],
            "name": "name",
            "outputs": [
                {
                    "name": "",
                    "type": "string"
                }
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [
                {
                    "name": "_spender",
                    "type": "address"
                },
                {
                    "name": "_value",
                    "type": "uint256"
                }
            ],
            "name": "approve",
            "outputs": [
                {
                    "name": "",
                    "type": "bool"
                }
            ],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [
                {
                    "name": "",
                    "type": "uint256"
                }
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [
                {
                    "name": "_from",
                    "type": "address"
                },
                {
                    "name": "_to",
                    "type": "address"
                },
                {
                    "name": "_value",
                    "type": "uint256"
                }
            ],
            "name": "transferFrom",
            "outputs": [
                {
                    "name": "",
                    "type": "bool"
                }
            ],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "decimals",
            "outputs": [
                {
                    "name": "",
                    "type": "uint8"
                }
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [
                {
                    "name": "_owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [],
            "name": "symbol",
            "outputs": [
                {
                    "name": "",
                    "type": "string"
                }
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [
                {
                    "name": "_to",
                    "type": "address"
                },
                {
                    "name": "_value",
                    "type": "uint256"
                }
            ],
            "name": "transfer",
            "outputs": [
                {
                    "name": "",
                    "type": "bool"
                }
            ],
            "payable": false,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [
                {
                    "name": "_owner",
                    "type": "address"
                },
                {
                    "name": "_spender",
                    "type": "address"
                }
            ],
            "name": "allowance",
            "outputs": [
                {
                    "name": "",
                    "type": "uint256"
                }
            ],
            "payable": false,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "payable": true,
            "stateMutability": "payable",
            "type": "fallback"
        },
        {
            "anonymous": false,
            "inputs": [
                {
                    "indexed": true,
                    "name": "owner",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "name": "spender",
                    "type": "address"
                },
                {
                    "indexed": false,
                    "name": "value",
                    "type": "uint256"
                }
            ],
            "name": "Approval",
            "type": "event"
        },
        {
            "anonymous": false,
            "inputs": [
                {
                    "indexed": true,
                    "name": "from",
                    "type": "address"
                },
                {
                    "indexed": true,
                    "name": "to",
                    "type": "address"
                },
                {
                    "indexed": false,
                    "name": "value",
                    "type": "uint256"
                }
            ],
            "name": "Transfer",
            "type": "event"
        }
    ]
    """
)

UNISWAP_TOKEN_ADDRESS = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
uniswap_contract = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
uniswap_abi = json.loads(
    """
[{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]
"""
)
oneinch_contract = "0x1111111254EEB25477B68fb85Ed929f73A960582"
oneinch_abi = json.loads(
    """
[{"inputs":[{"internalType":"contract IWETH","name":"weth","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"AccessDenied","type":"error"},{"inputs":[],"name":"AdvanceNonceFailed","type":"error"},{"inputs":[],"name":"AlreadyFilled","type":"error"},{"inputs":[],"name":"ArbitraryStaticCallFailed","type":"error"},{"inputs":[],"name":"BadPool","type":"error"},{"inputs":[],"name":"BadSignature","type":"error"},{"inputs":[],"name":"ETHTransferFailed","type":"error"},{"inputs":[],"name":"ETHTransferFailed","type":"error"},{"inputs":[],"name":"EmptyPools","type":"error"},{"inputs":[],"name":"EthDepositRejected","type":"error"},{"inputs":[],"name":"GetAmountCallFailed","type":"error"},{"inputs":[],"name":"IncorrectDataLength","type":"error"},{"inputs":[],"name":"InsufficientBalance","type":"error"},{"inputs":[],"name":"InvalidMsgValue","type":"error"},{"inputs":[],"name":"InvalidMsgValue","type":"error"},{"inputs":[],"name":"InvalidatedOrder","type":"error"},{"inputs":[],"name":"MakingAmountExceeded","type":"error"},{"inputs":[],"name":"MakingAmountTooLow","type":"error"},{"inputs":[],"name":"OnlyOneAmountShouldBeZero","type":"error"},{"inputs":[],"name":"OrderExpired","type":"error"},{"inputs":[],"name":"PermitLengthTooLow","type":"error"},{"inputs":[],"name":"PredicateIsNotTrue","type":"error"},{"inputs":[],"name":"PrivateOrder","type":"error"},{"inputs":[],"name":"RFQBadSignature","type":"error"},{"inputs":[],"name":"RFQPrivateOrder","type":"error"},{"inputs":[],"name":"RFQSwapWithZeroAmount","type":"error"},{"inputs":[],"name":"RFQZeroTargetIsForbidden","type":"error"},{"inputs":[],"name":"ReentrancyDetected","type":"error"},{"inputs":[],"name":"RemainingAmountIsZero","type":"error"},{"inputs":[],"name":"ReservesCallFailed","type":"error"},{"inputs":[],"name":"ReturnAmountIsNotEnough","type":"error"},{"inputs":[],"name":"SafePermitBadLength","type":"error"},{"inputs":[],"name":"SafeTransferFailed","type":"error"},{"inputs":[],"name":"SafeTransferFromFailed","type":"error"},{"inputs":[{"internalType":"bool","name":"success","type":"bool"},{"internalType":"bytes","name":"res","type":"bytes"}],"name":"SimulationResults","type":"error"},{"inputs":[],"name":"SwapAmountTooLarge","type":"error"},{"inputs":[],"name":"SwapWithZeroAmount","type":"error"},{"inputs":[],"name":"TakingAmountExceeded","type":"error"},{"inputs":[],"name":"TakingAmountIncreased","type":"error"},{"inputs":[],"name":"TakingAmountTooHigh","type":"error"},{"inputs":[],"name":"TransferFromMakerToTakerFailed","type":"error"},{"inputs":[],"name":"TransferFromTakerToMakerFailed","type":"error"},{"inputs":[],"name":"UnknownOrder","type":"error"},{"inputs":[],"name":"WrongAmount","type":"error"},{"inputs":[],"name":"WrongGetter","type":"error"},{"inputs":[],"name":"ZeroAddress","type":"error"},{"inputs":[],"name":"ZeroMinReturn","type":"error"},{"inputs":[],"name":"ZeroReturnAmount","type":"error"},{"inputs":[],"name":"ZeroTargetIsForbidden","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"maker","type":"address"},{"indexed":false,"internalType":"uint256","name":"newNonce","type":"uint256"}],"name":"NonceIncreased","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"maker","type":"address"},{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"remainingRaw","type":"uint256"}],"name":"OrderCanceled","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"maker","type":"address"},{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"remaining","type":"uint256"}],"name":"OrderFilled","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"makingAmount","type":"uint256"}],"name":"OrderFilledRFQ","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[{"internalType":"uint8","name":"amount","type":"uint8"}],"name":"advanceNonce","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"and","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"arbitraryStaticCall","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"interactions","type":"bytes"}],"internalType":"struct OrderLib.Order","name":"order","type":"tuple"}],"name":"cancelOrder","outputs":[{"internalType":"uint256","name":"orderRemaining","type":"uint256"},{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"orderInfo","type":"uint256"}],"name":"cancelOrderRFQ","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"orderInfo","type":"uint256"},{"internalType":"uint256","name":"additionalMask","type":"uint256"}],"name":"cancelOrderRFQ","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"interactions","type":"bytes"}],"internalType":"struct OrderLib.Order","name":"order","type":"tuple"}],"name":"checkPredicate","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IClipperExchangeInterface","name":"clipperExchange","type":"address"},{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"contract IERC20","name":"dstToken","type":"address"},{"internalType":"uint256","name":"inputAmount","type":"uint256"},{"internalType":"uint256","name":"outputAmount","type":"uint256"},{"internalType":"uint256","name":"goodUntil","type":"uint256"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"vs","type":"bytes32"}],"name":"clipperSwap","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"contract IClipperExchangeInterface","name":"clipperExchange","type":"address"},{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"contract IERC20","name":"dstToken","type":"address"},{"internalType":"uint256","name":"inputAmount","type":"uint256"},{"internalType":"uint256","name":"outputAmount","type":"uint256"},{"internalType":"uint256","name":"goodUntil","type":"uint256"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"vs","type":"bytes32"}],"name":"clipperSwapTo","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"contract IClipperExchangeInterface","name":"clipperExchange","type":"address"},{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"contract IERC20","name":"dstToken","type":"address"},{"internalType":"uint256","name":"inputAmount","type":"uint256"},{"internalType":"uint256","name":"outputAmount","type":"uint256"},{"internalType":"uint256","name":"goodUntil","type":"uint256"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"vs","type":"bytes32"},{"internalType":"bytes","name":"permit","type":"bytes"}],"name":"clipperSwapToWithPermit","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"destroy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"eq","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"interactions","type":"bytes"}],"internalType":"struct OrderLib.Order","name":"order","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"interaction","type":"bytes"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"skipPermitAndThresholdAmount","type":"uint256"}],"name":"fillOrder","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"info","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"}],"internalType":"struct OrderRFQLib.OrderRFQ","name":"order","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"uint256","name":"flagsAndAmount","type":"uint256"}],"name":"fillOrderRFQ","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"info","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"}],"internalType":"struct OrderRFQLib.OrderRFQ","name":"order","type":"tuple"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"vs","type":"bytes32"},{"internalType":"uint256","name":"flagsAndAmount","type":"uint256"}],"name":"fillOrderRFQCompact","outputs":[{"internalType":"uint256","name":"filledMakingAmount","type":"uint256"},{"internalType":"uint256","name":"filledTakingAmount","type":"uint256"},{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"info","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"}],"internalType":"struct OrderRFQLib.OrderRFQ","name":"order","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"uint256","name":"flagsAndAmount","type":"uint256"},{"internalType":"address","name":"target","type":"address"}],"name":"fillOrderRFQTo","outputs":[{"internalType":"uint256","name":"filledMakingAmount","type":"uint256"},{"internalType":"uint256","name":"filledTakingAmount","type":"uint256"},{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"info","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"}],"internalType":"struct OrderRFQLib.OrderRFQ","name":"order","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"uint256","name":"flagsAndAmount","type":"uint256"},{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"permit","type":"bytes"}],"name":"fillOrderRFQToWithPermit","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"interactions","type":"bytes"}],"internalType":"struct OrderLib.Order","name":"order_","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"interaction","type":"bytes"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"skipPermitAndThresholdAmount","type":"uint256"},{"internalType":"address","name":"target","type":"address"}],"name":"fillOrderTo","outputs":[{"internalType":"uint256","name":"actualMakingAmount","type":"uint256"},{"internalType":"uint256","name":"actualTakingAmount","type":"uint256"},{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"interactions","type":"bytes"}],"internalType":"struct OrderLib.Order","name":"order","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"interaction","type":"bytes"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"skipPermitAndThresholdAmount","type":"uint256"},{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"permit","type":"bytes"}],"name":"fillOrderToWithPermit","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"gt","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"address","name":"makerAsset","type":"address"},{"internalType":"address","name":"takerAsset","type":"address"},{"internalType":"address","name":"maker","type":"address"},{"internalType":"address","name":"receiver","type":"address"},{"internalType":"address","name":"allowedSender","type":"address"},{"internalType":"uint256","name":"makingAmount","type":"uint256"},{"internalType":"uint256","name":"takingAmount","type":"uint256"},{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"interactions","type":"bytes"}],"internalType":"struct OrderLib.Order","name":"order","type":"tuple"}],"name":"hashOrder","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"increaseNonce","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"maker","type":"address"},{"internalType":"uint256","name":"slot","type":"uint256"}],"name":"invalidatorForOrderRFQ","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"lt","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"nonce","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"makerAddress","type":"address"},{"internalType":"uint256","name":"makerNonce","type":"uint256"}],"name":"nonceEquals","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"offsets","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"or","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"remaining","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"remainingRaw","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32[]","name":"orderHashes","type":"bytes32[]"}],"name":"remainingsRaw","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueFunds","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"simulate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IAggregationExecutor","name":"executor","type":"address"},{"components":[{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"contract IERC20","name":"dstToken","type":"address"},{"internalType":"address payable","name":"srcReceiver","type":"address"},{"internalType":"address payable","name":"dstReceiver","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturnAmount","type":"uint256"},{"internalType":"uint256","name":"flags","type":"uint256"}],"internalType":"struct GenericRouter.SwapDescription","name":"desc","type":"tuple"},{"internalType":"bytes","name":"permit","type":"bytes"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"},{"internalType":"uint256","name":"spentAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"time","type":"uint256"}],"name":"timestampBelow","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"timeNonceAccount","type":"uint256"}],"name":"timestampBelowAndNonceEquals","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturn","type":"uint256"},{"internalType":"uint256[]","name":"pools","type":"uint256[]"}],"name":"uniswapV3Swap","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"int256","name":"amount0Delta","type":"int256"},{"internalType":"int256","name":"amount1Delta","type":"int256"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"uniswapV3SwapCallback","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturn","type":"uint256"},{"internalType":"uint256[]","name":"pools","type":"uint256[]"}],"name":"uniswapV3SwapTo","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturn","type":"uint256"},{"internalType":"uint256[]","name":"pools","type":"uint256[]"},{"internalType":"bytes","name":"permit","type":"bytes"}],"name":"uniswapV3SwapToWithPermit","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturn","type":"uint256"},{"internalType":"uint256[]","name":"pools","type":"uint256[]"}],"name":"unoswap","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturn","type":"uint256"},{"internalType":"uint256[]","name":"pools","type":"uint256[]"}],"name":"unoswapTo","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address payable","name":"recipient","type":"address"},{"internalType":"contract IERC20","name":"srcToken","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minReturn","type":"uint256"},{"internalType":"uint256[]","name":"pools","type":"uint256[]"},{"internalType":"bytes","name":"permit","type":"bytes"}],"name":"unoswapToWithPermit","outputs":[{"internalType":"uint256","name":"returnAmount","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]
"""
)


class SolanaWallet:
    def __init__(self) -> None:
        self.async_client = AsyncClient(QUICKNODE_HTTP)
        self.program_id = "TokenkegQfeZyiNwAJbNbGKPFCWuBvf9Ss623VQ5DA"

    async def generate_multi_chain_wallet(
        self,
        mnemonic: str = None,
        private_key_hex: str = None,
        coin_type=Bip44Coins.SOLANA,
        password="",
    ) -> tuple:
        """
        Generates a wallet for a specified chain using the MultiChainWalletGenerator class.

        This function provides a convenient wrapper for creating wallets using the `MultiChainWalletGenerator` class.
        It accepts optional arguments for a mnemonic phrase, private key in hex format, desired coin type, and password for encryption.

        Args:
            mnemonic (str, optional): A 12-word BIP39 mnemonic phrase (default: None).
            private_key_hex (str, optional): A private key in hex format (default: None). Provide either mnemonic or private key.
            coin_type (Bip44Coins, optional): The desired coin type for the wallet (default: Bip44Coins.ETHEREUM).
            password (str, optional): A password to encrypt the mnemonic (default: "").

        Returns:
            tuple: A tuple containing the public address (str), private key (str), and a boolean indicating if it's a Solana chain (True) or not (False).

        Raises:
            ValueError: If both mnemonic and private_key_hex are provided or neither are provided.
        """

        # if not mnemonic and not private_key_hex:
        #     raise ValueError(
        #         "Please provide either a mnemonic phrase or a private key in hex format."
        #     )

        wallet_data = await MultiChainWalletGenerator().generate_wallet(
            coin_type, sol_mnemonic=mnemonic, sol_private_key_hex=private_key_hex, password=password
        )
        return wallet_data

    async def connect_jupiter(self, private_key: str) -> Jupiter:
        """
        Connects to Jupiter using the provided private key.

        Args:
            private_key (Keypair): The private key for the Solana wallet.

        Returns:
            Jupiter: The Jupiter instance connected with the provided private key.

        Raises:
            ConnectionError: If the connection to Jupiter fails.
        """
        jupiter = Jupiter(self.async_client, Keypair.from_base58_string(private_key))
        if not jupiter.rpc.is_connected:
            raise ConnectionError("Failed to connect to Jupiter")
        return jupiter

    async def execute_swap(
        self,
        private_key: str,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
    ) -> str:
        """
        Executes a token swap on Solana using Jupiter.

        Args:
            private_key (Keypair): The private key for the Solana wallet.
            input_mint (str): The mint address of the input token.
            output_mint (str): The mint address of the output token.
            amount (int): The amount of input tokens to swap.
            slippage_bps (int): The allowed slippage in basis points.

        Returns:
            str: The transaction link on solana of the executed swap.

        Raises:
            Exception: If there is an error during the swap process.
        """
        pk = Keypair.from_base58_string(private_key)
        jupiter = await self.connect_jupiter(private_key)

        token_bal = await self.get_token_balance(input_mint)
        if token_bal < amount:
            LOGGER.debug("Insufficient amount to complete a swap")
            return f"""
<b>Insufficient Balance</b>
---------------------------
You do not have the total amount to complete the swap. Please top up your wallet to complete the transaction
        """

        transaction_data = await jupiter.swap(
            input_mint=input_mint,
            output_mint=output_mint,
            amount=amount,
            slippage_bps=slippage_bps,
        )

        raw_transaction = VersionedTransaction.from_bytes(
            base64.b64decode(transaction_data)
        )
        message = raw_transaction.message
        signature = pk.sign_message(to_bytes_versioned(message))
        signed_txn = VersionedTransaction.populate(message, [signature])

        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        result = await self.async_client.send_raw_transaction(
            txn=bytes(signed_txn), opts=opts
        )
        tokenInDetails = await TokenMetadata().get_token_symbol_by_contract(input_mint)
        tokenOutDetails = await TokenMetadata().get_token_symbol_by_contract(
            output_mint
        )

        json_response = json.loads(result.to_json())
        transaction_id = json_response["result"]
        LOGGER.debug(json_response)
        LOGGER.info(
            f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}"
        )
        return f"""
<code>
<b>Swap Successful</b>
--------------------------
🏦 Swapped | {tokenInDetails.symbol} for {tokenOutDetails.symbol}
---------------------------
</code>
----------------------------
<a href='https://explorer.solana.com/tx/{transaction_id}'>Transaction ID: {transaction_id}</a>
            """

    async def open_limit_order(
        self,
        private_key: Keypair,
        input_mint: str,
        output_mint: str,
        in_amount: int,
        out_amount: int,
    ) -> str:
        """
        Opens a limit order on Jupiter for swapping tokens.

        This function connects to the Jupiter API using the provided private key, creates a limit order to swap `in_amount` of `input_mint` token for `out_amount` of `output_mint` token, submits the transaction to the Solana network, and returns the transaction ID.

        **Note:** This function assumes you have already established a connection to the Jupiter API and Solana network through other methods.

        Args:
            private_key (Keypair): The private key used to sign the transaction.
            input_mint (str): The mint address of the token being offered (input token).
            output_mint (str): The mint address of the token being desired (output token).
            in_amount (int): The amount of the input token to offer.
            out_amount (int): The desired amount of the output token.

        Returns:
            str: The transaction ID of the submitted order.
        """
        jupiter = await self.connect_jupiter(private_key)

        transaction_data = await jupiter.open_order(
            input_mint=input_mint,
            output_mint=output_mint,
            in_amount=in_amount,
            out_amount=out_amount,
        )

        raw_transaction = VersionedTransaction.from_bytes(
            base64.b64decode(transaction_data["transaction_data"])
        )
        signature = private_key.sign_message(raw_transaction.message.serialize())
        signed_txn = VersionedTransaction.populate(
            raw_transaction.message, [signature, transaction_data["signature2"]]
        )

        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        result = await self.async_client.send_raw_transaction(
            txn=bytes(signed_txn), opts=opts
        )

        transaction_id = json.loads(result.to_json())["result"]
        LOGGER.debug(
            f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}"
        )
        return f"Limit Order Created: https://explorer.solana.com/tx/{transaction_id}"

    async def get_balance(self, pubkey: Pubkey) -> int:
        """
            Fetches the balance associated with a provided Solana public key.

        This asynchronous method retrieves the balance information for a given Solana public key using the connected Solana client. It utilizes the client's `get_balance` method to retrieve the balance data.

        Args:
            pubkey (Pubkey): The Solana public key for which to retrieve the balance.

        Returns:
            int: the balance in lamport which is the smallest unit of tokens in solana
        """
        balance = await self.async_client.get_balance(pubkey)
        return balance.value

    async def get_token_balance(self, token_pubkey: Pubkey) -> int:
        """
        Retrieves the balance of a specific SPL token associated with a provided public key.

        This asynchronous method fetches the balance information for a given Solana token
        public key (`token_pubkey`) using the connected Solana client. It utilizes the
        client's `get_token_account_balance` method to retrieve the balance data
        and returns the actual token amount as an integer.

        Args:
            token_pubkey (Pubkey): The public key of the SPL token account for which to retrieve the balance.

        Returns:
            int: The balance of the specified token as an integer, representing the number of tokens in the account.

        Raises:
            SolanaException: If there's an error fetching the balance information
            from the Solana network.
        """
        balance = await self.async_client.get_token_account_balance(token_pubkey)
        return int(balance.value.amount)

    async def get_token_supply(self, token_pubkey: Pubkey) -> int:
        """
        Retrieves the total supply of a specific SPL token.

        This asynchronous method fetches the total supply information for a given Solana token public key (`token_pubkey`) using the connected Solana client. It utilizes the client's `get_token_supply` method to retrieve the supply data and returns the total token supply as an integer.

        Args:
            token_pubkey (Pubkey): The public key of the SPL token for which to retrieve the total supply.

        Returns:
            int: The total supply of the specified token as an integer, representing the total number of tokens in existence.

        Raises:
            SolanaException: If there's an error fetching the supply information from the Solana network.
        """
        supply = await self.async_client.get_token_supply(token_pubkey)
        return int(supply.value.amount)

    async def get_all_tokens_for_wallet(self, owner_pubkey: Pubkey):
        """
        Retrieves all SPL token accounts associated with a provided wallet address.

        This asynchronous method fetches information about all token accounts owned by a specific Solana wallet address (`owner_pubkey`) using the connected Solana client. It utilizes the client's  `get_token_accounts_by_delegate` method with `program_id` set to the configured program ID (likely the SPL Token program ID) to filter for token accounts. The return value includes details about the retrieved token accounts.

        Args:
            owner_pubkey (Pubkey): The public key of the Solana wallet address for which to retrieve associated token accounts.

        Returns:
            Any: The raw data returned by the Solana client's `get_token_accounts_by_delegate` method, typically a dictionary-like  object containing information about the retrieved token accounts.

        Raises:
            SolanaException: If there's an error fetching the token account information from the Solana network.
        """

        tokens = await self.async_client.get_token_accounts_by_delegate(
            owner_pubkey, TokenAccountOpts(program_id=self.program_id)
        )
        return tokens.value

    async def convert_to_lamports(self, token_amount: float, decimals: int) -> int:
        """
        Converts a token amount to its equivalent value in lamports.

        This asynchronous function takes a token amount (`token_amount`) as a float
        and the number of decimal places (`decimals`) for the token and returns the
        equivalent value in lamports (SOL's smallest unit).

        Args:
            token_amount (float): The amount of tokens to convert.
            decimals (int): The number of decimal places for the token.

        Returns:
            int: The equivalent value of the token amount in lamports.

        Raises:
            ValueError: If the provided decimals value is negative.
        """

        if decimals < 0:
            raise ValueError("Decimals cannot be negative")
        lamports = int(token_amount * (10**decimals))
        return lamports

    async def convert_from_lamports(self, lamport_amount: int, decimals: int) -> float:
        """
        Converts a lamports amount to its equivalent token value.

        This asynchronous function takes a lamports amount (`lamport_amount`) as an integer
        and the number of decimal places (`decimals`) for the token and returns the
        equivalent value as a float representing the number of tokens.

        Args:
            lamport_amount (int): The amount in lamports to convert to token value.
            decimals (int): The number of decimal places for the token.

        Returns:
            float: The equivalent value of the lamport amount as a number of tokens.

        Raises:
            ValueError: If the provided decimals value is negative.
        """

        if decimals < 0:
            raise ValueError("Decimals cannot be negative")
        token_amount = float(lamport_amount / (10**decimals))
        return token_amount

    async def check_balance_for_swap(
        self,
        owner_pubkey: Pubkey,
        amount: int,
        decimals: int,
        input_mint: str = "SOL",
    ) -> bool:
        """
        Checks if the token balance or SOL balance is enough to complete a swap.

        Args:
            owner_pubkey (Pubkey): The public key of the owner wallet.
            input_mint (str): The mint address of the input token.
            amount (int): The amount of input tokens needed for the swap in lamports.
            decimals (int): The number of decimal places for the input token.

        Returns:
            bool: True if the balance is sufficient, False otherwise.
        """
        if input_mint in ["SOL", "So11111111111111111111111111111111111111112"]:
            # Check SOL balance
            sol_balance = await self.get_balance(owner_pubkey)
            return sol_balance >= amount
        else:
            # Check SPL token balance
            token_pubkey = Pubkey(input_mint)
            token_balance = await self.get_token_balance(token_pubkey)
            required_balance = await self.convert_to_lamports(amount, decimals)
            return token_balance >= required_balance


class ETHWallet:
    def __init__(self, network: str = "ETH") -> None:
        if network == "SOL":
            provider = INFURA_HTTP_URL
        if network == "ETH":
            provider = INFURA_HTTP_URL
        elif network == "BSC":
            provider = BSC_HTTP_URL
        elif network == "POL":
            provider = POLYGON_HTTP_URL
        elif network == "AVL":
            provider = AVALANCHE_HTTP_URL

        self.w3: Web3 = Web3(Web3.HTTPProvider(f"{provider}"))

        if not self.w3.is_connected():
            LOGGER.info("Connection Error")
            raise ConnectionError("Failed to connect to the Ethereum network")
        self.uniswap_router: type[Contract] = self.w3.eth.contract(
            address=uniswap_contract, abi=uniswap_abi
        )

        self.network: Network = [chain for chain in Networks if chain.sn == network][0]
        self.chain = self.network.id

    async def convert_to_wei(self, amount_eth: float) -> int:
        """
        Converts a floating-point number of Ether to Wei.

        This function utilizes the Web3.py library's `to_wei` method to convert the provided `amount` in Ether to its corresponding value in Wei.

        Args:
            amount (amount_eth): The amount of Ether to convert.

        Returns:
            int: The converted amount in Wei (integer value).
        """

        return int(self.w3.to_wei(amount_eth, "ether"))

    async def convert_from_wei(self, amount_wei: int) -> float:
        """
        Converts a value in Wei to Ether.

        This function utilizes the Web3.py library's `from_wei` method to convert the provided `amount` in Wei to its corresponding value in Ether.

        Args:
            amount_wei (int): The amount in Wei to convert.

        Returns:
            float: The converted amount in Ether.
        """

        return float(self.w3.from_wei(amount_wei, "ether"))

    async def generate_multi_chain_wallet(
        self,
        mnemonic: str = None,
        private_key_hex: str = None,
        coin_type=Bip44Coins.ETHEREUM,
        password="",
    ) -> tuple:
        """
        Generates a wallet for a specified chain using the MultiChainWalletGenerator class.

        This function provides a convenient wrapper for creating wallets using the `MultiChainWalletGenerator` class.
        It accepts optional arguments for a mnemonic phrase, private key in hex format, desired coin type, and password for encryption.

        Args:
            mnemonic (str, optional): A 12-word BIP39 mnemonic phrase (default: None).
            private_key_hex (str, optional): A private key in hex format (default: None). Provide either mnemonic or private key.
            coin_type (Bip44Coins, optional): The desired coin type for the wallet (default: Bip44Coins.ETHEREUM).
            password (str, optional): A password to encrypt the mnemonic (default: "").

        Returns:
            tuple: A tuple containing the public address (str), private key (str), and a boolean indicating if it's a Solana chain (True) or not (False).

        Raises:
            ValueError: If both mnemonic and private_key_hex are provided or neither are provided.
        """

        # if not mnemonic and not private_key_hex:
        #     raise ValueError(
        #         "Please provide either a mnemonic phrase or a private key in hex format."
        #     )

        wallet_data = await MultiChainWalletGenerator().generate_wallet(
            coin_type, mnemonic=mnemonic, private_key_hex=private_key_hex, password=password
        )
        return wallet_data

    async def convert_to_checksum(self, address: str) -> str:
        """
        Converts an Ethereum address to its checksum format.

        This function utilizes the Web3.py library's `to_checksum_address` method to convert the provided `address` to its checksum-encoded format.

        Args:
            address (str): The Ethereum address to convert.

        Returns:
            str: The checksum-encoded Ethereum address.
        """

        return self.w3.to_checksum_address(address)

    async def validate_address(self, address: str) -> bool:
        """
        Validate an Ethereum address.

        Args:
            address (str): The Ethereum address to validate.

        Returns:
            bool: True if the address is valid, False otherwise.

        Example:
            is_valid = ETHWallet.validate_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
            print(is_valid)  # Output: True or False
        """
        return self.w3.is_checksum_address(address)

    async def is_valid_private_key(self, private_key_str: str) -> bool:
        """
        Checks if a provided string is a valid Ethereum private key format.

        Args:
            private_key_str (str): The string to validate as a private key.

        Returns:
            bool: True if the format seems valid, False otherwise.

        Raises:
            Exception: Any exception raised during the validation process (e.g., invalid key format).

        Example:
            ```python
            async def my_function():
                user_key = "YOUR_PRIVATE_KEY"  # Replace with actual user input (for testing only)
                if await is_valid_private_key(user_key):
                    print("Private key format seems valid (for demonstration only).")
                else:
                    print("Invalid private key format (for demonstration only).")

            asyncio.run(my_function())
            ```

            **Important Note:**

            Never use real private keys in your code! This example is for demonstration purposes only. Exposing private keys compromises the security of cryptocurrency holdings. Consider using hardware wallets or reputable web wallets for secure private key management.
        """
        try:
            # Attempt to create an account from the key (potential exception)
            self.w3.eth.account.from_key(private_key_str)
            return True
        except Exception:
            return False

    async def get_balance(self, address: str) -> float:
        """
        Get the balance of an Ethereum address.

        Args:
            address (str): The Ethereum address to check the balance of.

        Returns:
            float: The balance in Ether.

        Example:
            balance = ETHWallet.get_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
            print(balance)  # Output: 12.345 (example balance)
        """
        balance = self.w3.eth.get_balance(address)
        return float(self.w3.from_wei(balance, "ether"))

    async def get_token_balance(self, address: str, token_address: str) -> float:
        """
        Get the balance of a specific token held by an Ethereum address.

        Args:
            address (str): The Ethereum address to check the token balance of.
            token_address (str): The contract address of the token.

        Returns:
            Decimal: The balance of the token held by the address (in the token's units).

        Example:
            token_balance = await ETHWallet.get_token_balance(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "0x..."  # Replace with the actual token contract address
            )
            print(token_balance)  # Output: 1000.0 (example token balance)
        """

        # Get the ERC20 token contract ABI (Application Binary Interface)
        # You'll need to obtain the ABI for the specific token you're interested in.
        # This can often be found on the token's website or Etherscan page.
        token: TokenInfo = await TokenMetadata().get_token_symbol_by_contract(
            token_address, self.network.name
        )
        token_meta: Optional[Coins] = await TokenMetadata().get_token_details(
            token.id, token.symbol
        )

        # Create an ERC20 contract instance using the ABI and token address
        token_contract: Contract = self.w3.eth.contract(
            address=token_address, abi=token_meta.abi
        )

        # Call the balanceOf method of the token contract to get the balance
        balance = await token_contract.functions.balanceOf(address).call()

        # Convert the balance from wei to the token's units (depends on the token)
        return float(balance) / (
            10 ** (token.decimal.ethereum or token_contract.functions.decimals().call())
        )

    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """
        Estimate the gas required for a transaction.

        Args:
            transaction (Dict[str, Any]): The transaction data.

        Returns:
            int: The estimated gas.

        Example:
            transaction = {
                "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "value": ETHWallet.w3.to_wei(0.1, "ether")
            }
            gas = ETHWallet.estimate_gas(transaction)
            print(gas)  # Output: 21000 (example gas estimate)
        """
        return self.w3.eth.estimate_gas(transaction)

    async def get_gas_price(self) -> int:
        """
        Get the current gas price.

        Returns:
            int: The current gas price in Wei.

        Example:
            gas_price = ETHWallet.get_gas_price()
            print(gas_price)  # Output: 20000000000 (example gas price)
        """
        return self.w3.eth.gas_price

    async def send_token(
        self,
        abi: Any,
        contract_address: str,
        sender_private_key: str,
        recipient_address: str,
        amount_ether: float,
    ) -> str:
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
            tx_url = ETHWallet.send_token(abi, "0xContractAddress", "0xSenderPrivateKey", "0xRecipientAddress", 1.0)
            print(tx_url)  # Output: Etherscan transaction URL
        """

        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)
        contract: type[Contract] = self.w3.eth.contract(contract_address, abi)
        token_amount = self.w3.to_wei(amount_ether, "ether")

        gas_estimate = contract.functions.transfer(
            recipient_address, token_amount
        ).estimate_gas({"from": sender_account.address})

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = (
            latest_block.baseFeePerGas
        )  # Base fee in the latest block (in wei)
        max_priority_fee_per_gas = (
            self.w3.eth.max_priority_fee
        )  # Priority fee to include the transaction in the block
        max_fee_per_gas = (
            5 * base_fee_per_gas
        ) + max_priority_fee_per_gas  # Maximum amount you’re willing to pay

        tx = {
            "nonce": nonce,
            "gas": gas_estimate,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.chain,
        }
        if self.network.sn == "BSC":
            tx = {
                "nonce": nonce,
                "gas": 2100000,
                "gasPrice": await self.get_gas_price(),
                "chainId": self.chain,
            }

        transaction = contract.functions.transfer(
            recipient_address, token_amount
        ).build_transaction(tx)
        signed_tx = self.w3.eth.account.sign_transaction(
            transaction, sender_account.key
        )

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt["status"] == 1:
                LOGGER.info("Transaction successful!")
                return f"https://etherscan.io/tx/{tx_hash.hex()}"
            else:
                LOGGER.info("Transaction failed")
                return "Transaction failed"
        except Exception as e:
            LOGGER.error(e)
            if "insufficient funds for gas" in str(e):
                return "Insufficient Balance"
            return str(e)

    async def send_eth(
        self, sender_private_key: str, recipient_address: str, amount_ether: float
    ) -> str:
        """
        Send Ether to a recipient address.

        Args:
            sender_private_key (str): The private key of the sender.
            recipient_address (str): The recipient's address.
            amount_ether (Decimal): The amount of Ether to send.

        Returns:
            str: The transaction URL on Etherscan.

        Example:
            tx_url = ETHWallet.send_crypto("0xSenderPrivateKey", "0xRecipientAddress", Decimal("0.1"))
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = (
            latest_block.baseFeePerGas
        )  # Base fee in the latest block (in wei)
        max_priority_fee_per_gas = (
            self.w3.eth.max_priority_fee
        )  # Priority fee to include the transaction in the block
        max_fee_per_gas = (
            50 * base_fee_per_gas
        ) + max_priority_fee_per_gas  # Maximum amount you’re willing to pay

        tx = {
            "nonce": nonce,
            "to": recipient_address,
            "value": self.w3.to_wei(amount_ether, "ether"),
            "gas": 21000,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.chain,
        }
        if self.network.sn == "BSC":
            tx = {
                "nonce": nonce,
                "gas": 2100000,
                "gasPrice": await self.get_gas_price(),
                "chainId": self.chain,
            }

        signed_tx = self.w3.eth.account.sign_transaction(tx, sender_account.key)

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt["status"] == 1:
                LOGGER.info("Transaction successful!")
                return f"https://etherscan.io/tx/{tx_hash.hex()}"
            else:
                LOGGER.info("Transaction failed")
                return "Transaction failed"
        except Exception as e:
            LOGGER.error(e)
            if "insufficient funds for gas" in str(e):
                return "Insufficient Balance"
            return str(e)

    async def check_balance_for_swap(
        self,
        user_address: str,
        token_address: str,
        amount_to_transfer: int,
        gas_price_gwei=20,
        gas_limit=21000,
    ):
        """
        Asynchronously checks if a user has sufficient balance for gas and token transfer on the Ethereum network.

        This function performs the following checks:

        1. Converts the provided user and token addresses to checksum format for Ethereum compatibility.
        2. Fetches the user's ETH balance and the token balance for the specified address.
        3. Calculates the gas cost in Wei based on the provided gas price (in Gwei) and gas limit.
        4. Verifies if the user has enough ETH to cover the gas cost.
        5. Verifies if the user has enough tokens of the specified address to cover the transfer amount.

        Args:
            user_address (str): The address of the user initiating the transfer.
            token_address (str): The contract address of the token being transferred.
            amount_to_transfer (int): The amount of tokens to be transferred (in units of the token).
            gas_price_gwei (int, optional): The gas price in Gwei (default: 20).
            gas_limit (int, optional): The gas limit for the transaction (default: 21000).

        Returns:
            bool: True if the user has sufficient balance for both gas and token transfer, False otherwise.
        """
        user_address = await self.convert_to_checksum(user_address)
        token_address = await self.convert_to_checksum(token_address)

        # Fetch ETH balance
        eth_balance = self.w3.eth.get_balance(user_address)
        LOGGER.debug(f"ETH Bal: {eth_balance}")

        # Fetch token balance
        token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        token_balance = token_contract.functions.balanceOf(user_address).call()
        amount_to_transfer_wei = self.w3.to_wei(amount_to_transfer, "ether")

        # Calculate gas cost in wei
        gas_price_wei = gas_price_gwei  # self.w3.to_wei(float(gas_price_gwei), "gwei")
        gas_cost = gas_price_wei * gas_limit

        # Check if user has enough ETH for gas
        if eth_balance < gas_cost:
            print(
                f"Insufficient ETH for gas: Required {self.w3.from_wei(gas_cost, 'ether')} ETH, Available {self.w3.from_wei(eth_balance, 'ether')} ETH"
            )
            return False

        # Check if user has enough tokens for transfer
        if float(token_balance) < amount_to_transfer_wei:
            print(
                f"Insufficient token balance: Required {amount_to_transfer_wei}, Available {token_balance}"
            )
            return False

        print("Sufficient balance for both gas and token transfer.")
        return True

    async def swap_tokens_with_uniswap(
        self,
        sender_private_key: str,
        token_in: str,
        token_out: str,
        amount_in_wei: int,
        amount_out_min_wei: int,
        deadline: int = 3000,
    ) -> str:
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
            tx_url = ETHWallet.swap_tokens_uniswap("0xSenderPrivateKey", "0xTokenIn", "0xTokenOut", 1.0, 0.9, 300, "0xRouterAddress", router_abi)
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)
        path = [token_in, token_out]

        deadline_timestamp = self.w3.eth.get_block("latest")["timestamp"] + deadline

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = (
            latest_block.baseFeePerGas
        )  # Base fee in the latest block (in wei)
        max_priority_fee_per_gas = (
            self.w3.eth.max_priority_fee
        )  # Priority fee to include the transaction in the block
        max_fee_per_gas = (
            5 * base_fee_per_gas
        ) + max_priority_fee_per_gas  # Maximum amount you’re willing to pay

        tx = {
            "nonce": nonce,
            "gas": 2100000,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.chain,
        }
        if self.network.sn == "BSC":
            tx = {
                "nonce": nonce,
                "gas": 2100000,
                "gasPrice": await self.get_gas_price(),
                "chainId": self.chain,
            }
        LOGGER.debug(tx)
        #         can_transfer = await self.check_balances(
        #             sender_account.address, token_in, amount_in, gas_price
        #         )
        #         LOGGER.debug(f"Can Transfer: {can_transfer}")
        #         if not can_transfer:
        #             return """
        # Insufficient Balance for transaction.
        #         """
        transaction = self.uniswap_router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amount_in_wei,
            amount_out_min_wei,
            path,
            sender_account.address,
            deadline_timestamp,
        ).build_transaction(
            tx
        )

        signed_tx = self.w3.eth.account.sign_transaction(
            transaction, sender_account.key
        )

        tokenInDetails = await TokenMetadata().get_token_symbol_by_contract(token_in)
        tokenOutDetails = await TokenMetadata().get_token_symbol_by_contract(token_out)

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt["status"] == 1:
                LOGGER.info("Token swap successful!")
                return f"""
<code>
<b>Transaction Successful</b>
--------------------------
🏦 Swapped | {tokenInDetails.symbol} for {tokenOutDetails.symbol}
💸 Amount  | {amount_in_wei / (10**tokenInDetails.decimal)} for {amount_out_min_wei / (10**tokenOutDetails.decimal)}
---------------------------
</code>
----------------------------
<a href='https://etherscan.io/tx/{tx_hash.hex()}'>Transaction Hash: {tx_hash.hex()}</a>
            """
            else:
                LOGGER.info("Token swap failed")
                return "Token swap failed"
        except Exception as e:
            LOGGER.error(e)
            if "insufficient funds for gas" in str(e):
                return "Insufficient Balance"
            return str(e)

    async def calculate_eth_amount_out(self, amount_in: int, token_in: str, token_out: str):

        # Path for swapping: [tokenIn, tokenOut]
        path = [token_in, token_out]

        LOGGER.debug(f"Path: {path}")

        # Fetch amounts out
        amounts_out = self.uniswap_router.functions.getAmountsOut(
            amount_in, path
        ).call()

        LOGGER.debug(f"Amount Out: {amounts_out}")
        return amounts_out[1]
