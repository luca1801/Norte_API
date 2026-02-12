from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Info
    API_TITLE: str
    API_VERSION: str
    API_DESCRIPTION: str

    # Server
    HOST: str
    PORT: int

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    # CORS
    CORS_ORIGINS: str
    # Logging
    LOG_LEVEL: str

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
