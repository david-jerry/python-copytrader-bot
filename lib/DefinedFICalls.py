import requests
import json
from typing import Optional, Dict, Any
from lib.GetDotEnv import DEFINED_API

class DefinedFiClient:
    """
    A class to interact with the Defined.fi GraphQL API.
    """

    def __init__(self):
        """
        Initializes the client with the API key.

        Args:
            api_key: Your Defined.fi API key.

        Example:
            client = DefinedFiClient()
        """
        self.url = "https://graph.defined.fi/graphql"
        self.headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {DEFINED_API}",
        }

    def get_token_info(self, address: str, network_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches information for a specific token from the Defined.fi API.

        Args:
            address (str): The contract address of the token.
            network_id (int): The ID of the network where the token resides.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the token information (symbol, totalSupply)
            or None if an error occurs.

        Example:
            token_info = DefinedFiClient.get_token_info("0x1234567890abcdef1234567890abcdef12345678", 1)
            print(token_info)
            # Output:
            # {
            #     'id': '1',
            #     'decimals': 18,
            #     'name': 'Token Name',
            #     'symbol': 'TKN',
            #     'totalSupply': '1000000',
            #     'info': {
            #         'circulatingSupply': '800000',
            #         'imageThumbUrk': 'https://example.com/image.png'
            #     }
            # }
        """
        query = f"""query GetTokenInfoQuery {{ getTokenInfo(address:"{address}", networkId:{network_id}) {{ id decimals name symbol totalSupply info {{ circulatingSupply imageThumbUrk }} }} }}"""

        response = requests.post(self.url, headers=self.headers, json={"query": query})

        if response.status_code == 200:
            data = json.loads(response.text)
            return data.get("data", {}).get("getTokenInfo")
        else:
            print(f"Error fetching token info: {response.status_code}")
            return None

DefinedFiCalls = DefinedFiClient()
