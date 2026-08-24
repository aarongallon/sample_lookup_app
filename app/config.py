from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/samples.db"
    redis_url: str = ""
    enable_whosampled: bool = True
    cache_ttl_seconds: int = 60 * 60 * 24

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def _fix_postgres_scheme(self) -> "Settings":
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]

        if "asyncpg" in url and "@" in url:
            from urllib.parse import urlparse, urlunparse, quote
            parsed = urlparse(url)
            if parsed.password:
                safe_pw = quote(parsed.password, safe="")
                url = urlunparse(parsed._replace(
                    netloc=f"{parsed.username}:{safe_pw}@{parsed.hostname}:{parsed.port}"
                ))
        self.database_url = url
        return self


settings = Settings()
