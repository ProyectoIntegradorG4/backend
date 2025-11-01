from typing import Optional, Any
import redis
import json
import os

class RedisCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
            cls._instance.init_redis()
        return cls._instance

    def init_redis(self):
        """Inicializa la conexión a Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://redis-cache:6379")
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = int(os.getenv("REDIS_TTL", "3600"))  # 1 hora por defecto

    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error al obtener de Redis: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Guarda un valor en el caché"""
        try:
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            print(f"Error al guardar en Redis: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Elimina un valor del caché"""
        try:
            return self.redis_client.delete(key) > 0
        except Exception as e:
            print(f"Error al eliminar de Redis: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe en el caché"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Error al verificar existencia en Redis: {str(e)}")
            return False