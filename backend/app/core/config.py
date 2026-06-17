from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    DOMAIN: str = "localhost"
    TZ: str = "UTC"

    DATABASE_URL: str = "postgresql+asyncpg://swan:change_me@db:5432/swan"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET: str = "change_me_access"
    JWT_REFRESH_SECRET: str = "change_me_refresh"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GOOGLE_OAUTH_REDIRECT: str = ""
    GOOGLE_DRIVE_REFRESH_TOKEN: str = ""
    GOOGLE_DRIVE_ROOT_FOLDER_ID: str = ""

    VAPID_PUBLIC: str = ""
    VAPID_PRIVATE: str = ""
    VAPID_SUBJECT: str = "mailto:admin@localhost"

    EXTERNAL_API_MASTER_KEY: str = "change_me_external"
    N8N_WEBHOOK_URL: str = ""

    @property
    def cors_origins(self) -> list[str]:
        if self.ENV == "development":
            return ["http://localhost:5173", "http://localhost:8000"]
        return [f"https://{self.DOMAIN}"]


settings = Settings()
