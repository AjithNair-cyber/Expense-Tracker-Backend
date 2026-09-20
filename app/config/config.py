from pydantic_settings import BaseSettings

# Define a Settings class to manage application configuration
class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    TELEGRAM_BOT_TOKEN: str
    OPENAI_MODEL: str
    USER_ID: int
    AUTH_TOKEN: str

    class Config:
        env_file = ".env"


settings = Settings()