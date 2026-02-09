from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Info
    API_TITLE: str = "api_norte"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Asset Management API"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./api_norte.db"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours for development

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Timezone
    TIMEZONE: str = "America/Sao_Paulo"
    TIMEZONE_OFFSET_HOURS: int = -3  # UTC-3 for Brasília

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
