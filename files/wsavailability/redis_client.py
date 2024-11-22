import redis
import pickle

class RedisClient:
    def __init__(self, host: str, port: int, password: str):
        self._pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=0,
            password=password  # Add the password parameter here
        )
        self._redis = redis.Redis(connection_pool=self._pool)

    def get(self, key: str):
        obj = self._redis.get(key)
        if obj:
            return pickle.loads(obj)
        else:
            return None

    def set(self, key: str, obj, expiration: int = 0):
        if expiration == 0:
            self._redis.set(key, pickle.dumps(obj))
        else:
            self._redis.setex(key, expiration, pickle.dumps(obj))
