from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: SecretStr
    ADMIN_IDS: list[int] = []
    
    # API Keys
    EXCHANGE_RATE_API_KEY: SecretStr = SecretStr("")  # Опциональный ключ
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings() 