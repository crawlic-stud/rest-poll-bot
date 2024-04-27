from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TG_TOKEN: str

    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_PORT: str
    MONGO_HOST: str
    DB_NAME: str

    ADMIN_ID: int


settings = Settings()
