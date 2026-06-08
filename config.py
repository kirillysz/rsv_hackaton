from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    YOUGILE_TOKEN: str = ""
    COLUMN_ID: str = ""
    FORUM_CHAT_ID: int = 0
    FORUM_THREAD_ID: int = 0

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()