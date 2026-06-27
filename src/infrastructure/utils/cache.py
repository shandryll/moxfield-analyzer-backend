import os
from cachetools import TTLCache

DECK_TTL = int(os.getenv("CACHE_DECK_TTL", "300"))
ORACLE_TTL = int(os.getenv("CACHE_ORACLE_TTL", "3600"))
COMBO_TTL = int(os.getenv("CACHE_COMBO_TTL", "86400"))

DECK_MAXSIZE = int(os.getenv("CACHE_DECK_MAXSIZE", "100"))
ORACLE_MAXSIZE = int(os.getenv("CACHE_ORACLE_MAXSIZE", "500"))
COMBO_MAXSIZE = int(os.getenv("CACHE_COMBO_MAXSIZE", "200"))

deck_cache = TTLCache(maxsize=DECK_MAXSIZE, ttl=DECK_TTL)
oracle_cache = TTLCache(maxsize=ORACLE_MAXSIZE, ttl=ORACLE_TTL)
combo_cache = TTLCache(maxsize=COMBO_MAXSIZE, ttl=COMBO_TTL)
