import aiohttp
import json

from lib.GetDotEnv import COINMARKETCAP_API

class CryptoArbitrageBot:
    def __init__(self, ):
        self.cmc_headers = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API}
        self.cmc_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    async def fetch_listings(self):
        params = {'start': 1, 'limit': 200, 'convert': 'USD'}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.cmc_url, headers=self.cmc_headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

