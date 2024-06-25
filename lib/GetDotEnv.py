from typing import Final
from decouple import config

TOKEN: Final = config("TOKEN")
REDIS: Final = config("BROKER_URL")
REDIS_HOST: Final = config("REDIS_HOST")
REDIS_POST: Final = config("REDIS_POST")
REDIS_DB: Final = config("REDIS_DB")
DEFINED_API: Final = config("DEFINED_API_KEY")
USERNAME: Final = config("USERNAME")
DEVELOPER_CHAT_ID: Final = config("DEVELOPER_CHAT_ID")
INFURA_HTTP_URL: Final = config("INFURA_HTTP_URL")
AVALANCHE_HTTP_URL: Final = config('AVALANCHE_HTTP_URL')
POLYGON_HTTP_URL: Final = config('POLYGON_HTTP_URL')
BSC_HTTP_URL:Final = config('BSC_HTTP_URL')
INFURA_WS_URL: Final = config("INFURA_WS_URL")
ETHERSCAN_API: Final = config("ETHERSCAN_API")
COINMARKETCAP_API: Final = config('COINMARKETCAP_API')
