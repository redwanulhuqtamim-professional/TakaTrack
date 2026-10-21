from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "TakaTrack API"
    DATABASE_URL: str
    SECRET_KEY: str
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    TIMEZONE: str = "Asia/Dhaka"
    CURRENCY: str = "BDT"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
