class Network:
    """
    This class represents a blockchain network.

    It provides attributes to store information about a network,
    including its short name (sn), full name (name), and identifier (id).
    The identifier (id) could be a chain ID specific to the network.

    This class is likely used for internal representation and manipulation
    of network data within the application.
    """

    def __init__(self, sn: str, name: str, id: int) -> None:
        """
        Initializes a Network object.

        Args:
            sn (str): The short name or identifier for the network.
            name (str): The full name of the network.
            id (int): The identifier for the network, possibly a chain ID.
        """

        self.sn: str = sn
        self.name: str = name
        self.id: int = id


Values = [
    {"sn": "ETH", "name": "Ethereum", "id": 1},
    {"sn": "BSC", "name": "Binance Smart Chain", "id": 56},
    {"sn": "POL", "name": "Polygon", "id": 137},
    {"sn": "AVL", "name": "Avalanche", "id": 43114},
    {"sn": "SOL", "name": "Solana", "id": 1399811149},
]

Networks = [
    Network(network["sn"], network["name"], network["id"]) for network in Values
]
