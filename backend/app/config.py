from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    environment: str = "development"
    debug: bool = True
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
