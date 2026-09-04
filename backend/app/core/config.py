from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./teamflow.db"
    secret_key: str = "development-secret-key"
    access_token_expire_minutes: int = 60 * 24 * 7
    redis_url: str = "redis://localhost:6379/0"
    run_migrations: bool = True
    seed_demo: bool = True
    demo_enabled: bool = True
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @model_validator(mode="after")
    def validate_production(self):
        if self.environment.lower() == "production":
            if len(self.secret_key) < 32 or self.secret_key in {"development-secret-key", "change-me-in-production"}:
                raise ValueError("SECRET_KEY must be a strong, unique value in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("DATABASE_URL must use PostgreSQL in production")
            if self.seed_demo:
                raise ValueError("SEED_DEMO must be false in production")
            if self.demo_enabled:
                raise ValueError("DEMO_ENABLED must be false in production")
            if not self.cors_origins.strip() or "*" in {origin.strip() for origin in self.cors_origins.split(",")}:
                raise ValueError("CORS_ORIGINS must explicitly list production origins")
        return self


settings = Settings()
