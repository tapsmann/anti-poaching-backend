from pydantic import field_validator
from pydantic_settings import BaseSettings

def _installed(module: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False

def _normalize_database_url(url: str) -> str:
    """Rewrite the driver in a postgres URL to one that is actually installed.

    Render's DATABASE_URL is often postgresql+psycopg:// (psycopg v3) while the
    project historically pinned psycopg2-binary (v2), which makes SQLAlchemy fail
    with "No module named 'psycopg'". Accept either scheme and pin the driver to
    a package present in this environment.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if not url.startswith("postgresql"):
        return url

    rest = url.split("://", 1)[1] if "://" in url else ""
    for scheme, module in (
        ("postgresql+psycopg2", "psycopg2"),
        ("postgresql+psycopg", "psycopg"),
    ):
        if _installed(module):
            return f"{scheme}://{rest}"
    return f"postgresql://{rest}"

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:1738@localhost:5432/anti-poaching-system"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    REGION: str = "zimbabwe"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,https://anti-poaching-system-gb2e6i6ob.vercel.app,https://anti-poaching-system-btj27sibw.vercel.app"

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        return _normalize_database_url(v)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
