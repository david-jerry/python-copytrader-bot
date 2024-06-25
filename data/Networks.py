class Network:
    def __init__(self, sn, name, id):
        self.sn = sn
        self.name = name
        self.id = id

Values = [
    {"sn": "ETH", "name": "Ethereum", "id": 1},
    {"sn": "POL", "name": "Polygon", "id": 137},
    {"sn": "SOL", "name": "Solana", "id": 1399811149},
    {"sn": "BSC", "name": "Binance Smart Chain", "id": 56},
    {"sn": "AVL", "name": "Avalanche", "id": 43114},
]

Networks = [Network(network['sn'], network["name"], network["id"]) for network in Values]
