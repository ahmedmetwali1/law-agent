from pydantic_settings import BaseSettings
from agents.config.settings import settings

class RedisSettings(BaseSettings):
    """Redis Configuration for the Queue"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    
    @property
    def redis_url(self) -> str:
        # If a full URL is provided in settings, use it, else construct
        # Ideally, we reuse settings.redis_url if available
        return f"redis://{self.host}:{self.port}/{self.database}"

redis_settings = RedisSettings()

# Queue Constants
QUEUE_NAME = "legal_agent_queue"
