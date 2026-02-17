import json
import os
import time
import hashlib
import logging

class CacheManager:
    def __init__(self, cache_file=".cache.json", ttl=86400):
        """
        Initialize the cache manager.
        :param cache_file: Path to the JSON cache file.
        :param ttl: Time to live in seconds (default: 24 hours).
        """
        self.cache_file = cache_file
        self.ttl = ttl
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save cache: {e}")

    def _get_key(self, key):
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def get(self, key):
        hashed_key = self._get_key(key)
        entry = self.cache.get(hashed_key)

        if entry:
            timestamp = entry.get("timestamp", 0)
            if time.time() - timestamp < self.ttl:
                logging.info(f"Cache hit for key: {key[:50]}...")
                return entry.get("value")
            else:
                logging.info(f"Cache expired for key: {key[:50]}...")
                del self.cache[hashed_key]
                self._save_cache()

        return None

    def set(self, key, value):
        hashed_key = self._get_key(key)
        self.cache[hashed_key] = {
            "value": value,
            "timestamp": time.time()
        }
        self._save_cache()
