from typing import Final
from decouple import config

TOKEN: Final = config("TOKEN")
REDIS: Final = config("BROKER_URL")
DEFINED_API: Final = config("DEFINED_API_KEY")
USERNAME: Final = config("USERNAME")
DEVELOPER_CHAT_ID: Final = config("DEVELOPER_CHAT_ID")
INFURA_HTTP_URL: Final = config("INFURA_HTTP_URL")
INFURA_WS_URL: Final = config("INFURA_WS_URL")
