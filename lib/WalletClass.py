from datetime import datetime
from decimal import Decimal
import json
from mnemonic import Mnemonic
import requests
from web3 import Web3
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
)
from lib.Logger import LOGGER
from models.CoinsModel import Coins, CurrentPrice, MarketCap, Platform

ERC20_ABI = json.loads(
    '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
)

WETH = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
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


class CryptoWallet:
    def __init__(self, network: str = "ETH"):
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
        if not self.w3.is_connected():
            LOGGER.info("Connection Error")
            raise ConnectionError("Failed to connect to the Ethereum network")
        self.uniswap_router = self.w3.eth.contract(
            address=uniswap_contract, abi=uniswap_abi
        )
        chain: Network  = [chain for chain in Networks if chain.sn == network][0]
        self.chain = chain.id

    async def convert_to_wei(self, amount: float):
        return self.w3.to_wei(amount, 'ether')

    async def convert_from_wei(self, amount: float):
        return self.w3.from_wei(amount, 'ether')

    async def generate_private_key(self):
        private_key = f"0x{secrets.token_hex(32)}"
        LOGGER.info(f"Generated private key: {private_key}")
        return private_key

    async def convert_to_checksum(self, address: str) -> str:
        return self.w3.to_checksum_address(address)

    async def validate_address(self, address: str) -> bool:
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

    async def create_wallet(self, password: str) -> Dict[str, Any]:
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
        private_key = await self.generate_private_key()
        account = Account.from_key(private_key)
        encrypted_key = Account.encrypt(account.key.hex(), str(password))
        LOGGER.info(f"Encrypted key: {encrypted_key}")
        return {
            "user_id": str(password),
            "pub_key": account.address,
            "sec_key": account.key.hex(),
            "enc_key": encrypted_key,
        }

    async def import_wallet(self, encrypted_key: str, password: str) -> str:
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

    async def get_balance(self, address: str) -> Decimal:
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
                "value": CryptoWallet.w3.to_wei(0.1, "ether")
            }
            gas = CryptoWallet.estimate_gas(transaction)
            print(gas)  # Output: 21000 (example gas estimate)
        """
        return self.w3.eth.estimate_gas(transaction)

    async def get_gas_price(self) -> int:
        """
        Get the current gas price.

        Returns:
            int: The current gas price in Wei.

        Example:
            gas_price = CryptoWallet.get_gas_price()
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
            tx_url = CryptoWallet.send_token(abi, "0xContractAddress", "0xSenderPrivateKey", "0xRecipientAddress", 1.0)
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)
        contract = self.w3.eth.contract(contract_address, abi)
        token_amount = self.w3.to_wei(amount_ether, "ether")

        gas_estimate = contract.functions.transfer(
            recipient_address, token_amount
        ).estimate_gas({"from": sender_account.address})

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = (
            latest_block.baseFeePerGas
        )  # Base fee in the latest block (in wei)
        max_priority_fee_per_gas = self.w3.to_wei(
            1, "gwei"
        )  # Priority fee to include the transaction in the block
        max_fee_per_gas = (
            5 * base_fee_per_gas
        ) + max_priority_fee_per_gas  # Maximum amount you’re willing to pay


        tx = {
            "nonce": nonce,
            "gas": gas_estimate,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.chain
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
            if tx_receipt.status:
                LOGGER.info("Transaction successful!")
                return f"https://etherscan.io/tx/{tx_hash.hex()}"
            else:
                LOGGER.info("Transaction failed")
                return "Transaction failed"
        except Exception as e:
            LOGGER.error(e)
            if 'insufficient funds for gas' in str(e):
                return "Insufficient Balance"
            return str(e)

    async def send_crypto(
        self, sender_private_key: str, recipient_address: str, amount_ether: Decimal
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
            tx_url = CryptoWallet.send_crypto("0xSenderPrivateKey", "0xRecipientAddress", Decimal("0.1"))
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = (
            latest_block.baseFeePerGas
        )  # Base fee in the latest block (in wei)
        max_priority_fee_per_gas = self.w3.to_wei(
            1, "gwei"
        )  # Priority fee to include the transaction in the block
        max_fee_per_gas = (
            5 * base_fee_per_gas
        ) + max_priority_fee_per_gas  # Maximum amount you’re willing to pay

        tx = {
            "nonce": nonce,
            "to": recipient_address,
            "value": self.w3.to_wei(amount_ether, "ether"),
            "gas": 21000,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.chain
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
            if 'insufficient funds for gas' in str(e):
                return "Insufficient Balance"
            return str(e)

    async def check_balances(
        self,
        user_address: str,
        token_address: str,
        amount_to_transfer: int,
        gas_price_gwei=20,
        gas_limit=21000,
    ):
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
        gas_price_wei = gas_price_gwei #self.w3.to_wei(float(gas_price_gwei), "gwei")
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

    async def swap_tokens_uniswap(
        self,
        sender_private_key: str,
        token_in: str,
        token_out: str,
        amount_in: float,
        amount_out_min: float,
        deadline: int = 5000,
        router_address: str = uniswap_contract,
        router_abi: Any = uniswap_abi,
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
            tx_url = CryptoWallet.swap_tokens_uniswap("0xSenderPrivateKey", "0xTokenIn", "0xTokenOut", 1.0, 0.9, 300, "0xRouterAddress", router_abi)
            print(tx_url)  # Output: Etherscan transaction URL
        """
        sender_account = self.w3.eth.account.from_key(sender_private_key)
        nonce = self.w3.eth.get_transaction_count(sender_account.address)
        amount_in_wei = self.w3.to_wei(amount_in, "ether")
        amount_out_min_wei = self.w3.to_wei(amount_out_min, "ether")
        path = [token_in, token_out]

        router_contract = self.w3.eth.contract(address=router_address, abi=router_abi)
        deadline_timestamp = self.w3.eth.get_block("latest")["timestamp"] + deadline
        gas_price = await self.get_gas_price()

        # Get and determine gas parameters
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = (
            latest_block.baseFeePerGas
        )  # Base fee in the latest block (in wei)
        max_priority_fee_per_gas = self.w3.to_wei(
            1, "gwei"
        )  # Priority fee to include the transaction in the block
        max_fee_per_gas = (
            5 * base_fee_per_gas
        ) + max_priority_fee_per_gas  # Maximum amount you’re willing to pay

        tx = {
            "nonce": nonce,
            "gas": 2100000,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": self.chain
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
        transaction = router_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
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

        tokenInDetails = await self.get_token_symbol_by_contract(token_in)
        tokenOutDetails = await self.get_token_symbol_by_contract(token_out)

        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt.status:
                LOGGER.info("Token swap successful!")
                return f"""
<code>
<b>Transaction Successful</b>
--------------------------
🏦 Swapped | {tokenInDetails['symbol']} for {tokenOutDetails['symbol']}
💸 Amount  | {amount_in} for {amount_out_min}
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
            if 'insufficient funds for gas' in str(e):
                return "Insufficient Balance"
            return str(e)

    async def calculate_amount_out(self, amount_in, token_in, token_out):

        # Path for swapping: [tokenIn, tokenOut]
        path = [token_in, token_out]

        LOGGER.debug(f"Path: {path}")

        # Fetch amounts out
        amounts_out = self.uniswap_router.functions.getAmountsOut(
            self.w3.to_wei(amount_in, "ether"), path
        ).call()

        LOGGER.debug(f"Amount Out: {amounts_out}")
        return amounts_out[-1]

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
            token_id = await CryptoWallet.get_token_id("xrp")
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

    async def get_token_details(self, token_id: str) -> Optional[Coins]:
        """
        Get detailed information about a token from CoinGecko.

        Args:
            token_id (str): The CoinGecko token ID.

        Returns:
            Optional[Coins]: A Coins object if found, None otherwise.
        """
        api_url = f"https://api.coingecko.com/api/v3/coins/{token_id}"

        try:
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
    ) -> Optional[Coins]:
        """
        Get detailed information about a token from CoinGecko.

        Args:
            platform (str): The name of the platform (e.g., 'ethereum').
            contract_address (str): The contract address of the token.

        Returns:
            Optional[Coins]: A Coins object if found, None otherwise.
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
            token_details = {"id": id, "symbol": symbol}
            return token_details
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"An error occurred: {e}")
            return None


