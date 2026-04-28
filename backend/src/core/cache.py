from functools import wraps
from typing import Any, Callable, Dict, Optional
import time

class Cache:
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl: Dict[str, int] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            ttl = self._ttl.get(key, 3600)
            if time.time() - timestamp < ttl:
                return value
            else:
                del self._cache[key]
                del self._ttl[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self._cache[key] = (value, time.time())
        self._ttl[key] = ttl
    
    def clear(self) -> None:
        self._cache.clear()
        self._ttl.clear()


cache = Cache()


def cached(ttl: int = 3600):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator