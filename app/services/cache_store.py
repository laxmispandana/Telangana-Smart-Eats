import json
import time

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None


class CacheStore:
    def __init__(self):
        self.client = None
        self.memory = {}

    def init_app(self, app):
        redis_url = app.config.get("REDIS_URL", "").strip()
        if redis_url and redis is not None:
            try:
                self.client = redis.from_url(redis_url, decode_responses=True)
                self.client.ping()
            except Exception:
                self.client = None

    def get_json(self, key):
        if self.client:
            value = self.client.get(key)
            return json.loads(value) if value else None

        record = self.memory.get(key)
        if not record:
            return None
        expires_at, value = record
        if expires_at and expires_at < time.time():
            self.memory.pop(key, None)
            return None
        return value

    def set_json(self, key, value, ttl=300):
        if self.client:
            self.client.setex(key, ttl, json.dumps(value))
            return
        expires_at = time.time() + ttl if ttl else None
        self.memory[key] = (expires_at, value)

    def delete(self, key):
        if self.client:
            self.client.delete(key)
            return
        self.memory.pop(key, None)


cache_store = CacheStore()
