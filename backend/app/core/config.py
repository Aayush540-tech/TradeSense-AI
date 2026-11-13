from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    APP_NAME: str = "TradeSense AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Redis / Cloud Memorystore
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_TIMEOUT_MS: int = 50

    # Google Cloud & Vertex AI
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: str = "asia-south1"
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Broker Integration
    BROKER_PROVIDER: Literal["mock", "dhan", "upstox", "zerodha"] = "mock"
    DHAN_CLIENT_ID: Optional[str] = None
    DHAN_ACCESS_TOKEN: Optional[str] = None
    UPSTOX_API_KEY: Optional[str] = None
    UPSTOX_API_SECRET: Optional[str] = None
    UPSTOX_REDIRECT_URI: Optional[str] = None
    ZERODHA_API_KEY: Optional[str] = None
    ZERODHA_API_SECRET: Optional[str] = None
    ZERODHA_ACCESS_TOKEN: Optional[str] = None

    # SEBI Compliance Prompt Guardrail
    SEBI_DISCLAIMER_TEXT: str = (
        "Disclaimer: TradeSense AI is an educational and analytical research platform. "
        "We do not provide direct buy/sell recommendations or financial advice. "
        "Trading in equities and F&O involves substantial risk of loss."
    )


settings = Settings()
