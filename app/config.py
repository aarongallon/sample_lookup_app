from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/samples.db"
    redis_url: str = ""
    enable_whosampled: bool = True
    cache_ttl_seconds: int = 60 * 60 * 24

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
