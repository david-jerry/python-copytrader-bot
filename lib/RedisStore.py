import json
import redis
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from lib.GetDotEnv import REDIS
from pydantic import BaseModel

# Connect to Redis using the Redis URL
r = redis.from_url(REDIS)


class RedisStore:
    def __init__(self, client=r):
        self.redis_client = client

    def store_item(self, key: str, item_id: str, data: Dict[str, Any]):
        """
        Store an item in Redis hash.

        Args:
            key (str): The Redis hash key.
            item_id (str): The ID of the item to store.
            data (Dict[str, Any]): The data to store.

        Example:
            Redis.store_item("users", "user_1", {"name": "Alice", "age": 30, "joined": datetime(2021, 5, 17)})
        """
        data = self.convert_dates_to_strings(data)
        json_data = json.dumps(data)
        self.redis_client.hset(key, item_id, json_data)

    def delete_item(self, key: str, item_id: str):
        """
        Delete an item from Redis hash.

        Args:
            key (str): The Redis hash key.
            item_id (str): The ID of the item to delete.

        Example:
            Redis.delete_item("users", "user_1")
        """
        self.redis_client.hdel(key, item_id)

    def get_item(self, key: str, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single item from Redis hash.

        Args:
            key (str): The Redis hash key.
            item_id (str): The ID of the item to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The retrieved item or None if not found.

        Example:
            user = Redis.get_item("users", "user_1")
            if user:
                print(user["name"])  # Output: Alice
        """
        json_data = self.redis_client.hget(key, item_id)
        if json_data:
            return self.decode_data(json_data)
        return None

    def get_all_items(self, key: str) -> List[Dict[str, Any]]:
        """
        Retrieve all items stored under a single key in Redis hash.

        Args:
            key (str): The Redis hash key.

        Returns:
            List[Dict[str, Any]]: A list of all items.

        Example:
            users = Redis.get_all_items("users")
            for user in users:
                print(user["name"])
        """
        items = []
        hash_data = self.redis_client.hgetall(key)
        for item_id, json_data in hash_data.items():
            item = self.decode_data(json_data)
            items.append(item)
        return items

    def update_item(self, key: str, item_id: str, data: Dict[str, Any]):
        """
        Update an item in Redis hash.

        Args:
            key (str): The Redis hash key.
            item_id (str): The ID of the item to update.
            data (Dict[str, Any]): The updated data.

        Returns:
            Dict[str, Any]: The updated item.

        Raises:
            ValueError: If the item does not exist.

        Example:
            updated_user = Redis.update_item("users", "user_1", {"age": 31})
            print(updated_user["age"])  # Output: 31
        """
        current_data = self.get_item(key, item_id)
        if current_data is None:
            raise ValueError(f"Item with id {item_id} not found under key {key}")

        current_data.update(data)
        current_data = self.convert_dates_to_strings(current_data)
        json_data = json.dumps(current_data)
        self.redis_client.hset(key, item_id, json_data)
        return current_data

    def convert_dates_to_strings(self, data: Any) -> Any:
        """
        Convert date objects to strings.

        Args:
            data (Any): The data to convert.

        Returns:
            Any: The data with date objects converted to strings.

        Example:
            data = {"name": "Alice", "joined": datetime(2021, 5, 17)}
            converted_data = Redis.convert_dates_to_strings(data)
            print(converted_data["joined"])  # Output: '2021-05-17T00:00:00'
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (datetime, date)):
                    data[key] = (
                        value.isoformat()
                        if isinstance(value, datetime)
                        else value.strftime("%Y-%m-%d")
                    )
                elif isinstance(value, dict):
                    data[key] = self.convert_dates_to_strings(value)
                elif isinstance(value, list):
                    data[key] = [self.convert_dates_to_strings(item) for item in value]
        elif isinstance(data, list):
            data = [self.convert_dates_to_strings(item) for item in data]
        return data

    def decode_data(self, json_data: bytes) -> Dict[str, Any]:
        """
        Decode JSON data from bytes to Python dictionary.

        Args:
            json_data (bytes): The JSON data to decode.

        Returns:
            Dict[str, Any]: The decoded data.

        Example:
            json_data = b'{"name": "Alice", "age": 30}'
            decoded_data = Redis.decode_data(json_data)
            print(decoded_data["name"])  # Output: Alice
        """
        return json.loads(json_data.decode("utf-8"))


# Instantiate RedisStore
Redis = RedisStore()
