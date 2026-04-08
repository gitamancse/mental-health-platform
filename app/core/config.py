from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Literal
from pydantic import Field, AnyUrl, computed_field
from pydantic_core import MultiHostUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -------------------------
    # APP SETTINGS
    # -------------------------
    APP_NAME: str = "Mental Health Platform"
    ENVIRONMENT: Literal["local", "development", "production"] = "local"
    DOMAIN: str = "localhost"

    @computed_field
    @property
    def SERVER_HOST(self) -> str:
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    # -------------------------
    # SECURITY
    # -------------------------
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # -------------------------
    # DATABASE
    # -------------------------
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            MultiHostUrl.build(
                scheme="postgresql+psycopg2",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    # -------------------------
    # REDIS (Optional)
    # -------------------------
    REDIS_URL: Optional[str] = None

    # -------------------------
    # CORS
    # -------------------------
    BACKEND_CORS_ORIGINS: List[AnyUrl] = Field(default_factory=list)

    # -------------------------
    # EMAIL
    # -------------------------
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # -------------------------
    # FRONTEND
    # -------------------------
    FRONTEND_URL: Optional[AnyUrl] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # === EMAIL SETTINGS (Add these) ===
    EMAIL_FROM: str = "noreply@yourplatform.com"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""


settings = Settings()